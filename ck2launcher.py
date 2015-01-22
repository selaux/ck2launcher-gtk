#!/usr/bin/python

# This is an alternative launcher for Crusader Kings 2
# Dependencies: pygobject, appdirs

import os
import subprocess
import json
import glob
import re
import appdirs
from gi.repository import Gtk
from gi.repository import Gdk

APP_NAME = 'ck2-launcher'
DLC_DEFAULT_SELECTION = True
MOD_DEFAULT_SELECTION = False

def get_config_path():
    """
        Gets config path four our little launcher
    """
    return os.path.join(appdirs.user_data_dir('ck2-launcher'), 'config.json')

def default_ck2_game_path():
    """
        Tries to guess the correct path for CK2 intstall on each OS
    """
    paths = {
        'posix': os.path.join(os.path.expanduser('~'), '.steam/steam/SteamApps/common/Crusader Kings II/'),
        'mac': os.path.join(os.path.expanduser('~'), 'Library/Application Support/Steam/SteamApps/common/Crusader Kings II/'),
        'nt': os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Steam/SteamApps/common/Crusader Kings II/'),
    }
    return paths[os.name]

def default_ck2_config_path():
    """
        Tries to guess the correct CK2 config path for each os
    """
    linux_and_osx = os.path.join(os.path.expanduser('~'), 'Documents/Paradox Interactive/Crusader Kings II/')
    paths = {
        'posix': linux_and_osx,
        'mac': linux_and_osx,
        'nt': appdirs.user_data_dir('Crusader Kings II', 'Paradox Interactive'),
    }
    return paths[os.name]

def read_name_from_ini(path):
    """
        Reads mod/dlc name from provided .dlc or .mod file
    """
    f = open(path, 'r')
    regex = 'name\s*=\s*"([^"]+)"'
    content = f.read()
    return re.match(regex, content).group(1)

def get_extension(dir, type, config):
    """
        Reads all mods/dlcs from path
    """
    path = os.path.join(dir, type + '/')
    glob_pattern = os.path.join(path, '*.' + type)
    l = []
    for file_path in glob.glob(glob_pattern):
        l.append({
            'name': read_name_from_ini(file_path),
            'file_name': os.path.basename(file_path)
        })
    return l

def get_dlcs(config):
    return sorted(get_extension(config['game_dir'], 'dlc', config), key=lambda m: m['name'])

def get_mods(config):
    return sorted(get_extension(config['config_dir'], 'mod', config), key=lambda m: m['name'])


def read_config():
    """
        Reads config for our little launcher
    """
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return None
    f = open(config_path, 'r')
    config = json.loads(f.read())
    f.close()
    return config

def write_config(config):
    """
        Writes config for our little launcher
    """
    config_path = get_config_path()
    if not os.path.exists(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    f = open(config_path, 'w')
    f.write(json.dumps(config))
    f.close()

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Crusader Kings 2 Launcher")
        self.set_name('main')

        self.config = read_config()
        if not self.config:
            self.get_initial_config()

        self.checkboxes_to_mods = {}
        self.checkboxes_to_dlcs = {}

        self.set_background()
        self.initialize_layout()
        self.connect_signals()

    def initialize_layout(self):
        main_box = Gtk.Box(spacing=20, orientation=Gtk.Orientation.VERTICAL)

        image_path = os.path.join(self.config['game_dir'], 'launcher/launcher_bg2.jpg')
        image = Gtk.Image()
        image.set_from_file(image_path)
        main_box.pack_start(image, True, True, 0)

        checkboxes_box = Gtk.Box(spacing=20)

        mod_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        mod_scroll = Gtk.ScrolledWindow()
        mod_scroll.set_size_request(340, 200);
        mod_scroll.add(mod_box)

        mod_label = Gtk.Label()
        mod_label.set_markup('<b>Mods</b>')
        mod_label.set_justify(Gtk.Justification.LEFT)
        mod_box.pack_start(mod_label, False, False, 0)

        mods = get_mods(self.config)
        for mod in mods:
            cb = Gtk.CheckButton(mod['name'])
            cb.set_active(self.config['mods'].get(mod['file_name'], MOD_DEFAULT_SELECTION))
            self.checkboxes_to_mods[cb] = mod
            mod_box.pack_start(cb, False, False, 0)
        checkboxes_box.pack_start(mod_scroll, True, True, 0)

        dlc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dlc_scroll = Gtk.ScrolledWindow()
        dlc_scroll.set_size_request(340, 200);
        dlc_scroll.add(dlc_box)

        dlc_label = Gtk.Label()
        dlc_label.set_markup('<b>DLCs</b>')
        dlc_box.pack_start(dlc_label, False, False, 0)

        dlcs = get_dlcs(self.config)
        for it, dlc in enumerate(dlcs):
            cb = Gtk.CheckButton(dlc['name'])
            cb.set_active(self.config['dlcs'].get(dlc['file_name'], DLC_DEFAULT_SELECTION))
            self.checkboxes_to_dlcs[cb] = dlc
            dlc_box.pack_start(cb, False, False, 0)
        checkboxes_box.pack_start(dlc_scroll, True, True, 0)

        main_box.pack_start(checkboxes_box, True, True, 0)

        self.start_button = Gtk.Button('Start Crusader Kings 2')
        self.start_button.set_size_request(700, 80);
        self.start_button.set_name('start_button')
        main_box.pack_start(self.start_button, True, True, 0)

        self.add(main_box)

    def connect_signals(self):
        self.connect("delete-event", self.close)
        self.start_button.connect("clicked", self.start_ck2)

        for cb in self.checkboxes_to_mods:
            cb.connect("toggled", self.mod_checkbox_clicked)
        for cb in self.checkboxes_to_dlcs:
            cb.connect("toggled", self.dlc_checkbox_clicked)

    def mod_checkbox_clicked(self, checkbox, *args):
        mod_filename = self.checkboxes_to_mods[checkbox]['file_name']
        self.config['mods'][mod_filename] = checkbox.get_active()
        write_config(self.config)

    def dlc_checkbox_clicked(self, checkbox, *args):
        dlc_filename = self.checkboxes_to_dlcs[checkbox]['file_name']
        self.config['dlcs'][dlc_filename] = checkbox.get_active()
        write_config(self.config)

    def set_background(self):
        style_provider = Gtk.CssProvider()
        background_path = os.path.join(self.config['game_dir'], 'launcher/background.jpg')
        css= str.encode("""
        #main, #start_button {{
            background-image: url('{0:s}');
        }}
        """.format(background_path))
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def close(self, *args):
        write_config(self.config)
        Gtk.main_quit()

    def get_initial_config(self):
        """
            Shows dialog to perform initial setup
        """
        self.config = {}

        game_dir_dialog = Gtk.FileChooserDialog(
            "Please choose the game directory of Crusader Kings 2",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        game_dir_dialog.set_filename(default_ck2_game_path())
        game_dir_response = game_dir_dialog.run()
        self.config['game_dir'] = game_dir_dialog.get_filename()
        game_dir_dialog.destroy()
        if game_dir_response != Gtk.ResponseType.OK:
            if not self.config:
                Gtk.main_quit()
            return

        config_dir_dialog = Gtk.FileChooserDialog(
            "Please choose the configuration directory of Crusader Kings 2",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        config_dir_dialog.set_filename(default_ck2_config_path())
        config_dir_response = config_dir_dialog.run()
        self.config['config_dir'] = config_dir_dialog.get_filename()
        config_dir_dialog.destroy()
        if config_dir_response != Gtk.ResponseType.OK:
            if not self.config:
                Gtk.main_quit()
            return

        self.config['mods'] = {}
        self.config['dlcs'] = {}

        write_config(self.config)

    def start_ck2(self, *args):
        """
            Start Crusader Kings
        """
        command = [ os.path.join(self.config['game_dir'], 'ck2') ]

        for mod, selected in self.config['mods'].items():
            if selected:
                command.append('-mod=mod/{0}'.format(mod))

        for dlc, selected in self.config['dlcs'].items():
            if not selected:
                command.append('-exclude_dlc=dlc/{0}'.format(dlc))

        print('Starting CK2: {0}'.format(' '.join(command)))
        subprocess.Popen(command).pid
        self.close()

win = MainWindow()
win.show_all()
Gtk.main()
