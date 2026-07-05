import os
import sys
import winreg


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_KEY = "CrossHud"
LEGACY_AUTOSTART_KEYS = (
    "CrossHud_PetyaBlatnoy",
    "CrossHud_By_PetyaBlatnoy",
    "Crosshud_By_Petyablatnoy",
    "Crosshud_By_Petyablatnoy-HudsightKiller",
)


def app_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'


def set_autostart(enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, AUTOSTART_KEY, 0, winreg.REG_SZ, app_command())
        else:
            _delete_value(key, AUTOSTART_KEY)
        for legacy_key in LEGACY_AUTOSTART_KEYS:
            _delete_value(key, legacy_key)


def repair_autostart() -> None:
    set_autostart(True)


def _delete_value(key, value_name: str) -> None:
    try:
        winreg.DeleteValue(key, value_name)
    except FileNotFoundError:
        pass
