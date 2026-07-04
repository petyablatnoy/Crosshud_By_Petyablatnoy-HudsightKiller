import json
import os
import platform
import subprocess
import sys
import uuid
from typing import Any, Dict, List, Optional

from app_metadata import APP_DISPLAY_NAME, APP_VERSION


class DiagnosticService:
    CLIENT_ID_FILE = "client_id.txt"

    def __init__(self, app_data_dir: str, settings_file: str, log_file: str, settings: Optional[Any] = None):
        self.app_data_dir = app_data_dir
        self.settings_file = settings_file
        self.log_file = log_file
        self.settings = settings
        self._video_info_cache: Optional[List[Dict[str, Any]]] = None

    def client_id(self) -> str:
        os.makedirs(self.app_data_dir, exist_ok=True)
        path = os.path.join(self.app_data_dir, self.CLIENT_ID_FILE)
        existing = self._read_client_id(path)
        if existing:
            return existing

        generated = str(uuid.uuid4())
        with open(path, "w", encoding="utf-8") as f:
            f.write(generated)
        return generated

    def rows(self) -> List[Dict[str, str]]:
        return [
            {"label": "Версия", "value": f"{APP_DISPLAY_NAME} {APP_VERSION}"},
            {"label": "UID", "value": self.client_id()},
            {"label": "Windows", "value": self._windows_version()},
            {"label": "Архитектура", "value": platform.machine() or "unknown"},
            {"label": "Видеокарта", "value": self._video_names()},
            {"label": "Драйвер GPU", "value": self._video_driver_versions()},
            {"label": "Дисплей", "value": self._display_resolution()},
            {"label": "Разрешение оверлея", "value": self._overlay_resolution()},
            {"label": "DPI", "value": self._system_dpi()},
            {"label": "Запуск", "value": "EXE" if getattr(sys, "frozen", False) else "Python"},
            {"label": "Python", "value": platform.python_version()},
            {"label": "Настройки", "value": self.settings_file},
            {"label": "Логи", "value": self.log_file},
        ]

    def rows_json(self) -> str:
        return json.dumps(self.rows(), ensure_ascii=False)

    def report_text(self) -> str:
        return "\n".join(f"{row['label']}: {row['value']}" for row in self.rows())

    def _read_client_id(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                value = f.read().strip()
            parsed = uuid.UUID(value)
            return str(parsed)
        except (FileNotFoundError, ValueError):
            return ""

    def _windows_version(self) -> str:
        release = platform.release()
        version = platform.version()
        return f"{release} ({version})" if version else release

    def _video_names(self) -> str:
        names = [item.get("Name", "") for item in self._video_info() if item.get("Name")]
        return "; ".join(names) if names else "недоступно"

    def _video_driver_versions(self) -> str:
        versions = []
        for item in self._video_info():
            name = item.get("Name", "GPU")
            version = item.get("DriverVersion", "")
            if version:
                versions.append(f"{name}: {version}")
        return "; ".join(versions) if versions else "недоступно"

    def _display_resolution(self) -> str:
        for item in self._video_info():
            width = item.get("CurrentHorizontalResolution")
            height = item.get("CurrentVerticalResolution")
            if width and height:
                return f"{width}x{height}"
        try:
            import ctypes
            user32 = ctypes.windll.user32
            width = int(user32.GetSystemMetrics(0))
            height = int(user32.GetSystemMetrics(1))
            if width > 0 and height > 0:
                return f"{width}x{height}"
        except Exception:
            pass
        return "недоступно"

    def _overlay_resolution(self) -> str:
        if not self.settings:
            return "недоступно"
        try:
            return f"{int(self.settings.get('screen_width'))}x{int(self.settings.get('screen_height'))}"
        except Exception:
            return "недоступно"

    def _system_dpi(self) -> str:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            if hasattr(user32, "GetDpiForSystem"):
                dpi = int(user32.GetDpiForSystem())
            else:
                gdi32 = ctypes.windll.gdi32
                dc = user32.GetDC(None)
                try:
                    dpi = int(gdi32.GetDeviceCaps(dc, 88))
                finally:
                    user32.ReleaseDC(None, dc)
            if dpi > 0:
                return f"{dpi} ({round(dpi / 96 * 100)}%)"
        except Exception:
            pass
        return "недоступно"

    def _video_info(self) -> List[Dict[str, Any]]:
        if self._video_info_cache is not None:
            return self._video_info_cache

        self._video_info_cache = []
        if os.name != "nt":
            return self._video_info_cache

        command = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,DriverVersion,CurrentHorizontalResolution,CurrentVerticalResolution | "
            "ConvertTo-Json -Compress"
        )
        try:
            completed = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=3,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode != 0 or not completed.stdout.strip():
                return self._video_info_cache
            data = json.loads(completed.stdout)
            if isinstance(data, dict):
                self._video_info_cache = [data]
            elif isinstance(data, list):
                self._video_info_cache = [item for item in data if isinstance(item, dict)]
        except Exception:
            self._video_info_cache = []
        return self._video_info_cache
