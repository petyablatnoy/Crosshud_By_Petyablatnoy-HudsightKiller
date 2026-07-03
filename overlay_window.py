import ctypes
import logging
import random
import time

from win32_api import (
    BI_RGB,
    BITMAPINFO,
    BITMAPINFOHEADER,
    BLENDFUNCTION,
    DIB_RGB_COLORS,
    ERROR_CLASS_ALREADY_EXISTS,
    HGDIOBJ,
    HTTRANSPARENT,
    HWND,
    HWND_TOPMOST,
    POINT,
    SIZE,
    SW_HIDE,
    SW_SHOWNA,
    TOPMOST_FLAGS,
    WNDCLASSEX,
    WNDPROC,
    WM_CLOSE,
    WM_DESTROY,
    WM_NCHITTEST,
    WS_EX_LAYERED,
    WS_EX_NOACTIVATE,
    WS_EX_TOOLWINDOW,
    WS_EX_TOPMOST,
    WS_EX_TRANSPARENT,
    WS_POPUP,
    gdi32,
    kernel32,
    user32,
)


class OverlayWindow:
    def __init__(self, size: int):
        self.size = int(size)
        self.hwnd = None
        self.hdc = None
        self.mem_dc = None
        self.hbitmap = None
        self.old_bitmap = None
        self.p_bits = ctypes.c_void_p()
        self.class_name = None
        self.h_instance = None
        self._wnd_proc_ptr = None

    @property
    def is_created(self) -> bool:
        return bool(self.hwnd and self.mem_dc)

    def create(self) -> bool:
        if self.is_created:
            return True

        self.h_instance = kernel32.GetModuleHandleW(None)
        for _ in range(100):
            class_name = f"CH_Overlay_{int(time.time())}_{random.randint(1000, 9999)}"
            try:
                if not self._register_window_class(class_name):
                    time.sleep(0.01)
                    continue

                ex_style = (
                    WS_EX_LAYERED
                    | WS_EX_TRANSPARENT
                    | WS_EX_TOPMOST
                    | WS_EX_TOOLWINDOW
                    | WS_EX_NOACTIVATE
                )
                self.hwnd = user32.CreateWindowExW(
                    ex_style,
                    class_name,
                    "Crosshair",
                    WS_POPUP,
                    0,
                    0,
                    self.size,
                    self.size,
                    None,
                    None,
                    self.h_instance,
                    None,
                )
                if not self.hwnd:
                    self._unregister_window_class()
                    time.sleep(0.01)
                    continue

                self.hdc = user32.GetDC(self.hwnd)
                self.mem_dc = gdi32.CreateCompatibleDC(self.hdc)
                if self.hdc and self.mem_dc:
                    self.create_drawing_surface()
                    if self.hbitmap and self.p_bits:
                        return True

                self.destroy()
                time.sleep(0.01)
            except Exception:
                logging.exception("Failed to create overlay window")
                self.destroy()
                time.sleep(0.01)
        return False

    def _register_window_class(self, class_name: str) -> bool:
        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg in (WM_DESTROY, WM_CLOSE):
                return 0
            if msg == WM_NCHITTEST:
                return HTTRANSPARENT
            return user32.DefWindowProcW(HWND(hwnd), msg, wparam, lparam)

        self._wnd_proc_ptr = WNDPROC(wnd_proc)

        wc = WNDCLASSEX()
        wc.cbSize = ctypes.sizeof(WNDCLASSEX)
        wc.lpfnWndProc = ctypes.cast(self._wnd_proc_ptr, ctypes.c_void_p)
        wc.hInstance = self.h_instance
        wc.lpszClassName = class_name

        if user32.RegisterClassExW(ctypes.byref(wc)):
            self.class_name = class_name
            return True

        if kernel32.GetLastError() == ERROR_CLASS_ALREADY_EXISTS:
            self.class_name = class_name
            return True
        return False

    def create_drawing_surface(self) -> None:
        if not self.is_created:
            return

        if self.hbitmap:
            if self.old_bitmap:
                gdi32.SelectObject(self.mem_dc, self.old_bitmap)
            gdi32.DeleteObject(self.hbitmap)
            self.hbitmap = None
            self.old_bitmap = None

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = self.size
        bmi.bmiHeader.biHeight = -self.size
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB

        self.p_bits = ctypes.c_void_p()
        self.hbitmap = gdi32.CreateDIBSection(
            self.mem_dc,
            ctypes.byref(bmi),
            DIB_RGB_COLORS,
            ctypes.byref(self.p_bits),
            None,
            0,
        )
        if not self.hbitmap or not self.p_bits:
            logging.error("Failed to create overlay drawing surface")
            return
        self.old_bitmap = gdi32.SelectObject(self.mem_dc, HGDIOBJ(self.hbitmap))

    def resize_surface(self, size: int) -> None:
        size = int(size)
        if size <= 0 or size == self.size:
            return
        self.size = size
        self.create_drawing_surface()

    def show(self) -> None:
        if self.hwnd:
            user32.ShowWindow(self.hwnd, SW_SHOWNA)

    def hide(self) -> None:
        if self.hwnd:
            user32.ShowWindow(self.hwnd, SW_HIDE)

    def force_topmost(self) -> None:
        if self.hwnd:
            user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, TOPMOST_FLAGS)

    def update_pixels(self, data: bytes) -> None:
        if self.p_bits and data:
            ctypes.memmove(self.p_bits, data, len(data))

    def update_layered(self, screen_width: int, screen_height: int, alpha: int) -> None:
        if not self.is_created:
            return

        x = int((screen_width - self.size) / 2)
        y = int((screen_height - self.size) / 2)
        position = POINT(x, y)
        source = POINT(0, 0)
        size = SIZE(self.size, self.size)
        blend = BLENDFUNCTION(0, 0, max(0, min(255, int(alpha))), 1)
        user32.UpdateLayeredWindow(
            self.hwnd,
            self.hdc,
            ctypes.byref(position),
            ctypes.byref(size),
            self.mem_dc,
            ctypes.byref(source),
            0,
            ctypes.byref(blend),
            2,
        )

    def destroy(self) -> None:
        try:
            if self.mem_dc:
                if self.old_bitmap:
                    gdi32.SelectObject(self.mem_dc, self.old_bitmap)
                if self.hbitmap:
                    gdi32.DeleteObject(self.hbitmap)
                gdi32.DeleteDC(self.mem_dc)
        finally:
            self.mem_dc = None
            self.hbitmap = None
            self.old_bitmap = None

        try:
            if self.hdc and self.hwnd:
                user32.ReleaseDC(self.hwnd, self.hdc)
        finally:
            self.hdc = None

        try:
            if self.hwnd:
                user32.DestroyWindow(self.hwnd)
        finally:
            self.hwnd = None

        self._unregister_window_class()

    def _unregister_window_class(self) -> None:
        if not self.class_name or not self.h_instance:
            return
        try:
            user32.UnregisterClassW(self.class_name, self.h_instance)
        except Exception:
            logging.debug("Failed to unregister overlay window class", exc_info=True)
        finally:
            self.class_name = None
