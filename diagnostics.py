import json
import os
import platform
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from app_metadata import APP_DISPLAY_NAME, APP_NAME, APP_VERSION


class DiagnosticService:
    CLIENT_ID_FILE = "client_id.txt"
    SUPPORT_CONTACT = "@petyablatnoy"
    LOG_ARCHIVE_COUNT = 5

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
            {"label": "CPU", "value": self._cpu_name()},
            {"label": "RAM", "value": self._total_memory()},
            {"label": "Видеокарта", "value": self._video_names()},
            {"label": "Драйвер GPU", "value": self._video_driver_versions()},
            {"label": "Дисплей", "value": self._display_resolution()},
            {"label": "Мониторы", "value": self._monitor_summary()},
            {"label": "Разрешение оверлея", "value": self._overlay_resolution()},
            {"label": "DPI", "value": self._system_dpi()},
            {"label": "Настройки прицела", "value": self._crosshair_settings_summary()},
            {"label": "Запуск", "value": "EXE" if getattr(sys, "frozen", False) else "Python"},
            {"label": "Python", "value": platform.python_version()},
            {"label": "PID", "value": str(os.getpid())},
            {"label": "EXE", "value": sys.executable},
            {"label": "Настройки", "value": self.settings_file},
            {"label": "Логи", "value": self.log_file},
        ]

    def rows_json(self) -> str:
        return json.dumps(self.rows(), ensure_ascii=False)

    def report_text(self) -> str:
        lines = [
            f"{APP_DISPLAY_NAME} support diagnostics",
            f"Support: Telegram {self.SUPPORT_CONTACT}",
            f"Generated: {datetime.now().isoformat(timespec='seconds')}",
            "",
        ]
        lines.extend(f"{row['label']}: {row['value']}" for row in self.rows())
        return "\n".join(lines)

    def report_data(self) -> Dict[str, Any]:
        return {
            "support": {"telegram": self.SUPPORT_CONTACT},
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "client_id": self.client_id(),
            "rows": self.rows(),
            "video_controllers": self._video_info(),
            "monitors": self._monitor_info(),
            "settings": self._settings_snapshot(),
            "logs": [os.path.basename(path) for path in self.log_files()],
        }

    def create_support_archive(self) -> str:
        reports_dir = os.path.join(self.app_data_dir, "support_reports")
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_name = f"{APP_NAME}_support_{self.client_id()[:8]}_{timestamp}.zip"
        archive_path = os.path.join(reports_dir, archive_name)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("system_info.txt", self.report_text())
            archive.writestr("system_info.json", json.dumps(self.report_data(), indent=2, ensure_ascii=False))
            for index, log_path in enumerate(self.log_files(), start=1):
                archive.write(log_path, f"logs/{index:02d}_{os.path.basename(log_path)}")
        return archive_path

    def log_files(self) -> List[str]:
        candidates = [self.log_file]
        candidates.extend(f"{self.log_file}.{index}" for index in range(1, self.LOG_ARCHIVE_COUNT))
        return [path for path in candidates if os.path.exists(path)][:self.LOG_ARCHIVE_COUNT]

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

    def _cpu_name(self) -> str:
        if os.name == "nt":
            value = self._powershell_json(
                "Get-CimInstance Win32_Processor | "
                "Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | "
                "ConvertTo-Json -Compress"
            )
            if isinstance(value, dict):
                name = value.get("Name") or "CPU"
                cores = value.get("NumberOfCores")
                logical = value.get("NumberOfLogicalProcessors")
                clock = value.get("MaxClockSpeed")
                parts = [str(name).strip()]
                if cores and logical:
                    parts.append(f"{cores}C/{logical}T")
                if clock:
                    parts.append(f"{clock} MHz")
                return ", ".join(parts)
        return platform.processor() or "недоступно"

    def _total_memory(self) -> str:
        try:
            if os.name == "nt":
                import ctypes

                class MemoryStatus(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                status = MemoryStatus()
                status.dwLength = ctypes.sizeof(status)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                    total_gb = status.ullTotalPhys / (1024 ** 3)
                    available_gb = status.ullAvailPhys / (1024 ** 3)
                    return f"{total_gb:.1f} GB total, {available_gb:.1f} GB free"
        except Exception:
            pass
        return "недоступно"

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

    def _monitor_summary(self) -> str:
        monitors = self._monitor_info()
        if not monitors:
            return "недоступно"
        parts = []
        for index, monitor in enumerate(monitors, start=1):
            width = monitor.get("width")
            height = monitor.get("height")
            x = monitor.get("x")
            y = monitor.get("y")
            primary = ", primary" if monitor.get("primary") else ""
            parts.append(f"#{index}: {width}x{height} @ {x},{y}{primary}")
        return "; ".join(parts)

    def _monitor_info(self) -> List[Dict[str, Any]]:
        if os.name != "nt":
            return []
        try:
            import ctypes
            from ctypes import wintypes

            monitors: List[Dict[str, Any]] = []
            user32 = ctypes.windll.user32

            class Rect(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            class MonitorInfo(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", Rect),
                    ("rcWork", Rect),
                    ("dwFlags", wintypes.DWORD),
                ]

            monitor_enum_proc = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(Rect),
                wintypes.LPARAM,
            )

            def callback(monitor, _hdc, _rect, _data):
                info = MonitorInfo()
                info.cbSize = ctypes.sizeof(MonitorInfo)
                if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    monitors.append(
                        {
                            "x": info.rcMonitor.left,
                            "y": info.rcMonitor.top,
                            "width": info.rcMonitor.right - info.rcMonitor.left,
                            "height": info.rcMonitor.bottom - info.rcMonitor.top,
                            "work_width": info.rcWork.right - info.rcWork.left,
                            "work_height": info.rcWork.bottom - info.rcWork.top,
                            "primary": bool(info.dwFlags & 1),
                        }
                    )
                return 1

            user32.EnumDisplayMonitors(None, None, monitor_enum_proc(callback), 0)
            return monitors
        except Exception:
            return []

    def _crosshair_settings_summary(self) -> str:
        snapshot = self._settings_snapshot()
        if not snapshot:
            return "недоступно"
        keys = [
            "enabled",
            "size",
            "thickness",
            "gap",
            "opacity",
            "outline_enabled",
            "outline_width",
            "center_dot",
            "center_dot_size",
            "pixel_perfect",
            "rainbow_mode",
            "dynamic_color",
            "rmb_hide_mode",
            "hotkey",
            "overlay_size",
            "custom_pixels_count",
        ]
        return ", ".join(f"{key}={snapshot[key]}" for key in keys if key in snapshot)

    def _settings_snapshot(self) -> Dict[str, Any]:
        if not self.settings:
            return {}
        keys = [
            "enabled",
            "size",
            "thickness",
            "gap",
            "opacity",
            "outline_enabled",
            "outline_width",
            "center_dot",
            "center_dot_size",
            "pixel_perfect",
            "rainbow_mode",
            "dynamic_color",
            "screen_width",
            "screen_height",
            "overlay_size",
            "rmb_hide_mode",
            "hotkey",
            "autostart",
            "start_minimized",
            "check_updates",
        ]
        snapshot: Dict[str, Any] = {}
        for key in keys:
            try:
                snapshot[key] = self.settings.get(key)
            except Exception:
                pass
        try:
            snapshot["custom_pixels_count"] = len(self.settings.get("custom_pixels") or [])
        except Exception:
            pass
        return snapshot

    def _video_info(self) -> List[Dict[str, Any]]:
        if self._video_info_cache is not None:
            return self._video_info_cache

        self._video_info_cache = []
        if os.name != "nt":
            return self._video_info_cache

        command = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM,DriverVersion,DriverDate,VideoProcessor,"
            "CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate,VideoModeDescription | "
            "ConvertTo-Json -Compress"
        )
        data = self._powershell_json(command)
        if isinstance(data, dict):
            self._video_info_cache = [data]
        elif isinstance(data, list):
            self._video_info_cache = [item for item in data if isinstance(item, dict)]
        return self._video_info_cache

    def _powershell_json(self, command: str) -> Any:
        if os.name != "nt":
            return None
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
                return None
            return json.loads(completed.stdout)
        except Exception:
            return None
