import logging
from typing import Tuple, Optional

class ResolutionDetector:
    @staticmethod
    def get_resolution_winapi() -> Optional[Tuple[int, int]]:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            if width > 0 and height > 0:
                return width, height
        except Exception:
            logging.debug("WinAPI resolution detection failed", exc_info=True)
        return None

    @classmethod
    def get_resolution(cls) -> Tuple[int, int]:
        res = cls.get_resolution_winapi()
        if res: return res
        return 1920, 1080

    @classmethod
    def monitor_resolution_changes(cls, callback, interval=2.0):
        import threading
        import time
        last_resolution = cls.get_resolution()
        def monitor():
            nonlocal last_resolution
            while True:
                try:
                    current_resolution = cls.get_resolution()
                    if current_resolution != last_resolution:
                        callback(last_resolution, current_resolution)
                        last_resolution = current_resolution
                    time.sleep(interval)
                except Exception:
                    time.sleep(interval)
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        return thread
