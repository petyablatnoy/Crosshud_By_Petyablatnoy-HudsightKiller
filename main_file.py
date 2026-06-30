import sys
import os
import argparse
import logging
import ctypes
from logging.handlers import RotatingFileHandler
from PySide6.QtCore import QCoreApplication

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PetyaBlatnoy.CrossHud.App.4")
except Exception:
    pass

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    plugin_paths = [
        os.path.join(application_path, 'PySide6', 'plugins'),
        os.path.join(application_path, 'plugins'),
        application_path
    ]
    for p in plugin_paths:
        if os.path.exists(p):
            QCoreApplication.addLibraryPath(p)

from crosshud_app import CrossHudApp
from single_instance import SingleInstanceManager

def setup_paths():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)
    
    if application_path not in sys.path:
        sys.path.insert(0, application_path)

def parse_arguments():
    parser = argparse.ArgumentParser(description='CrossHud_By_PetyaBlatnoy')
    parser.add_argument('--profile', help='Load specific profile')
    parser.add_argument('--minimize', action='store_true', help='Start minimized')
    parser.add_argument('--enable', action='store_true', help='Enable crosshair on start')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='4')
    return parser.parse_args()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def setup_logging(debug_mode=False):
    level = logging.DEBUG if debug_mode else logging.INFO
    log_dir = os.path.join(os.path.expanduser("~"), "CrossHud_By_PetyaBlatnoy", "logs")
    os.makedirs(log_dir, exist_ok=True)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(os.path.join(log_dir, "crosshud.log"), maxBytes=2*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    sys.excepthook = handle_exception

def load_profile(app, profile_name):
    if not profile_name: return
    try:
        paths = [
            f"{profile_name}_profile.json", 
            f"{profile_name}.json", 
            os.path.join("profiles", f"{profile_name}.json"),
            os.path.join(app.settings.profiles_dir, f"{profile_name}.json")
        ]
        for p in paths:
            if os.path.exists(p):
                app.settings.load_from_file(p)
                return
    except Exception:
        logging.exception("Failed to load profile: %s", profile_name)

def main():
    try:
        setup_paths()
        
        args = parse_arguments()
        setup_logging(args.debug)

        if SingleInstanceManager.notify_existing():
            return
        
        app = CrossHudApp()
        single_instance = SingleInstanceManager(app.app)
        if single_instance.start(app.show_main_window):
            app.single_instance = single_instance
        else:
            logging.warning("Single-instance protection is disabled for this run")

        if args.profile: load_profile(app, args.profile)
        if args.enable: app.settings.set('enabled', True)
        
        start_minimized = args.minimize or app.settings.get('start_minimized', False)
        app.run(start_minimized)
        
    except Exception:
        logging.exception("Fatal startup error")
        sys.exit(1)

if __name__ == "__main__":
    main()
