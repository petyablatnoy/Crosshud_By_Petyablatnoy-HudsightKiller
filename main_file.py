import sys
import os
import argparse
import logging
import ctypes
from logging.handlers import RotatingFileHandler
from PySide6.QtCore import QCoreApplication

from app_metadata import APP_NAME, APP_USER_MODEL_ID, APP_VERSION


LOG_MAX_BYTES = int(7.5 * 1024 * 1024)
LOG_BACKUP_COUNT = 4

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
except Exception:
    pass

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    resource_path = getattr(sys, "_MEIPASS", application_path)
    plugin_paths = [
        os.path.join(resource_path, 'PySide6', 'plugins'),
        os.path.join(resource_path, 'plugins'),
        os.path.join(application_path, 'PySide6', 'plugins'),
        os.path.join(application_path, 'plugins'),
        application_path
    ]
    for p in plugin_paths:
        if os.path.exists(p):
            QCoreApplication.addLibraryPath(p)

from crosshud_app import CrossHudApp
from single_instance import SingleInstanceManager

def attach_console_for_cli():
    if not getattr(sys, 'frozen', False):
        return
    if not any(arg in ('--version', '-h', '--help') for arg in sys.argv[1:]):
        return
    try:
        import msvcrt
        stdout_handle = ctypes.windll.kernel32.GetStdHandle(-11)
        stderr_handle = ctypes.windll.kernel32.GetStdHandle(-12)
        invalid = ctypes.c_void_p(-1).value
        if stdout_handle not in (0, invalid):
            stdout_fd = msvcrt.open_osfhandle(stdout_handle, os.O_WRONLY)
            sys.stdout = open(stdout_fd, "w", encoding="utf-8", buffering=1, closefd=False)
        if stderr_handle not in (0, invalid):
            stderr_fd = msvcrt.open_osfhandle(stderr_handle, os.O_WRONLY)
            sys.stderr = open(stderr_fd, "w", encoding="utf-8", buffering=1, closefd=False)
        if sys.stdout:
            return
    except Exception:
        pass
    try:
        if ctypes.windll.kernel32.AttachConsole(-1):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
    except Exception:
        pass

def setup_paths():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)
    
    if application_path not in sys.path:
        sys.path.insert(0, application_path)

def parse_arguments():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument('--profile', help='Load specific profile')
    parser.add_argument('--minimize', action='store_true', help='Start minimized')
    parser.add_argument('--enable', action='store_true', help='Enable crosshair on start')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version=APP_VERSION)
    return parser.parse_args()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def rotate_logs_on_start(log_file, backup_count=LOG_BACKUP_COUNT):
    for index in range(backup_count, 0, -1):
        source = f"{log_file}.{index}"
        target = f"{log_file}.{index + 1}"
        if not os.path.exists(source):
            continue
        if index >= backup_count:
            os.remove(source)
        else:
            os.replace(source, target)

    if not os.path.exists(log_file):
        return
    if os.path.getsize(log_file) <= 0:
        os.remove(log_file)
        return
    os.replace(log_file, f"{log_file}.1")

def setup_logging(debug_mode=False):
    level = logging.DEBUG if debug_mode else logging.INFO
    log_dir = os.path.join(os.path.expanduser("~"), "CrossHud_By_PetyaBlatnoy", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "crosshud.log")
    rotate_logs_on_start(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(
        log_file,
        mode='w',
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
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
        attach_console_for_cli()
        
        args = parse_arguments()

        if SingleInstanceManager.notify_existing():
            return

        setup_logging(args.debug)
        logging.info(
            "%s %s starting; debug=%s; frozen=%s",
            APP_NAME,
            APP_VERSION,
            args.debug,
            getattr(sys, "frozen", False),
        )

        app = CrossHudApp()
        single_instance = SingleInstanceManager(app.app)
        if single_instance.start(app.show_main_window):
            app.single_instance = single_instance
        else:
            logging.warning("Single-instance protection is disabled for this run")

        if args.profile: load_profile(app, args.profile)
        if args.enable: app.settings.set('enabled', True)
        
        start_minimized = args.minimize or app.settings.get('start_minimized', False)
        logging.info(
            "Startup mode: minimized=%s, overlay_enabled=%s, settings=%s",
            start_minimized,
            app.settings.get('enabled', True),
            app.settings.settings_file,
        )
        app.run(start_minimized)
        
    except Exception:
        logging.exception("Fatal startup error")
        sys.exit(1)

if __name__ == "__main__":
    main()
