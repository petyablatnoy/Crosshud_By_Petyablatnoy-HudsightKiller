from threading import Timer, Lock, Event, Thread, current_thread
from typing import Optional, List, Tuple
import ctypes
from ctypes import wintypes
import time
import logging
import queue
import random
from crosshair_renderer import opacity_byte, render_crosshair_bgra

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
shcore = ctypes.windll.shcore

WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOPMOST = 0x8
WS_EX_TOOLWINDOW = 0x80
WS_EX_NOACTIVATE = 0x08000000
WS_POPUP = 0x80000000
GWL_EXSTYLE = -20
LWA_ALPHA = 0x2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_NOZORDER = 0x0004
HWND_TOPMOST = -1
WM_QUIT = 0x0012
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_HOTKEY = 0x0312
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_RBUTTONDBLCLK = 0x0206
PM_REMOVE = 0x0001
WH_MOUSE_LL = 14
BI_RGB = 0
DIB_RGB_COLORS = 0
AC_SRC_ALPHA = 1

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_long), ('biHeight', ctypes.c_long), ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD), ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', ctypes.c_long), ('biYPelsPerMeter', ctypes.c_long), ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 3)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte), ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]

if not hasattr(wintypes, 'HICON'): wintypes.HICON = ctypes.c_void_p
if not hasattr(wintypes, 'HCURSOR'): wintypes.HCURSOR = ctypes.c_void_p
if not hasattr(wintypes, 'HBRUSH'): wintypes.HBRUSH = ctypes.c_void_p
if not hasattr(wintypes, 'LPCWSTR'): wintypes.LPCWSTR = ctypes.c_wchar_p
if not hasattr(wintypes, 'HINSTANCE'): wintypes.HINSTANCE = ctypes.c_void_p

class WNDCLASSEX(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("style", wintypes.UINT), ("lpfnWndProc", ctypes.c_void_p), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON), ("hCursor", wintypes.HCURSOR), ("hbrBackground", wintypes.HBRUSH), ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HICON)]

if ctypes.sizeof(ctypes.c_void_p) == 8:
    LRESULT = ctypes.c_int64
    WPARAM = ctypes.c_uint64
    LPARAM = ctypes.c_int64
else:
    LRESULT = ctypes.c_long
    WPARAM = ctypes.c_uint
    LPARAM = ctypes.c_long

HWND = ctypes.c_void_p
HDC = ctypes.c_void_p
HBITMAP = ctypes.c_void_p
HGDIOBJ = ctypes.c_void_p

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, wintypes.UINT, WPARAM, LPARAM)
LOWLEVELMOUSEPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, WPARAM, LPARAM)

user32.DefWindowProcW.argtypes = [HWND, wintypes.UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.CreateWindowExW.argtypes = [ctypes.c_uint, wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, HWND, wintypes.HANDLE, wintypes.HINSTANCE, ctypes.c_void_p]
user32.CreateWindowExW.restype = HWND
user32.SetWindowLongW.argtypes = [HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEX)]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.GetDC.argtypes = [HWND]
user32.GetDC.restype = HDC
user32.ReleaseDC.argtypes = [HWND, HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.UpdateLayeredWindow.argtypes = [HWND, HDC, ctypes.POINTER(POINT), ctypes.POINTER(SIZE), HDC, ctypes.POINTER(POINT), wintypes.COLORREF, ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]
user32.UpdateLayeredWindow.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, WPARAM, LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HANDLE
user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, WPARAM, LPARAM]
user32.CallNextHookEx.restype = LRESULT
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateDIBSection.argtypes = [HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
gdi32.CreateDIBSection.restype = HBITMAP
gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
gdi32.SelectObject.restype = HGDIOBJ
gdi32.DeleteObject.argtypes = [HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [HDC]
gdi32.DeleteDC.restype = wintypes.BOOL

class OverlayManager:
    VK_MAP = {
        'Insert': 0x2D, 'Home': 0x24, 'End': 0x23, 'PageUp': 0x21, 'PageDown': 0x22,
        'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75,
        'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B
    }

    def __init__(self, settings_manager, on_toggle_callback=None):
        self.settings_manager = settings_manager
        self.on_toggle_callback = on_toggle_callback
        self.hwnd = None
        self.hdc = None
        self.hbitmap = None
        self.old_bitmap = None
        self.mem_dc = None
        self.rmb_pressed = False
        self.rainbow_hue = 0
        self.overlay_size = 100
        self.is_visible = False
        self.cleanup_in_progress = False
        self.registered_class_name = None
        self.thread_stop_event = Event()
        self.render_event = Event()
        self.command_queue = queue.Queue()
        self.window_ready = Event()
        self.hook_handle = None
        self.monitor_thread = None
        self.render_thread = None
        self.hotkey_thread = None
        self.topmost_thread = None
        self.hotkey_thread_id = 0
        self.mouse_thread_id = 0
        self.mouse_hook_handle = None
        self.mouse_hook_proc = LOWLEVELMOUSEPROC(self._low_level_mouse_proc)
        self.win_event_proc_proto = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, ctypes.c_long, ctypes.c_long, wintypes.DWORD, wintypes.DWORD)
        self.win_event_proc = self.win_event_proc_proto(self._win_event_proc)
        self.hotkey_restart_event = Event()
        self.start_monitoring()

    def _setup_win_event_hook(self):
        try:
            user32.SetWinEventHook.restype = wintypes.HANDLE
            user32.SetWinEventHook.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.HMODULE, self.win_event_proc_proto, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
            self.hook_handle = user32.SetWinEventHook(0x0003, 0x0003, None, self.win_event_proc, 0, 0, 0x0000 | 0x0002)
        except Exception:
            logging.exception("Failed to install WinEvent hook")

    def _win_event_proc(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if event == 0x0003 and self.hwnd and self.is_visible:
            self.command_queue.put(('reforce_top', None))

    def create_layered_window(self) -> None:
        for attempt in range(100):
            try:
                class_name = f"CH_Overlay_{int(time.time())}_{random.randint(1000, 9999)}"
                def wnd_proc(hwnd, msg, wparam, lparam):
                    if msg == WM_DESTROY or msg == WM_CLOSE: return 0
                    if msg == 0x0084: return -1
                    return user32.DefWindowProcW(HWND(hwnd), wintypes.UINT(msg), WPARAM(wparam), LPARAM(lparam))
                self.wnd_proc_ptr = WNDPROC(wnd_proc)
                h_instance = kernel32.GetModuleHandleW(None)
                wc = WNDCLASSEX()
                wc.cbSize = ctypes.sizeof(WNDCLASSEX)
                wc.lpfnWndProc = ctypes.cast(self.wnd_proc_ptr, ctypes.c_void_p)
                wc.hInstance = h_instance
                wc.lpszClassName = class_name
                if not user32.RegisterClassExW(ctypes.byref(wc)):
                    if kernel32.GetLastError() != 1410:
                        time.sleep(0.01)
                        continue
                self.registered_class_name = class_name
                ex_style = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                self.hwnd = user32.CreateWindowExW(ex_style, class_name, "Crosshair", WS_POPUP, 0, 0, self.overlay_size, self.overlay_size, None, None, h_instance, None)
                if self.hwnd:
                    self.hdc = user32.GetDC(self.hwnd)
                    self.mem_dc = gdi32.CreateCompatibleDC(self.hdc)
                    self.create_drawing_surface()
                    return
            except: 
                time.sleep(0.01)

    def create_drawing_surface(self) -> None:
        if not self.hwnd or not self.mem_dc: return
        if self.hbitmap:
            if self.old_bitmap: gdi32.SelectObject(self.mem_dc, self.old_bitmap)
            gdi32.DeleteObject(self.hbitmap)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = self.overlay_size
        bmi.bmiHeader.biHeight = -self.overlay_size
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB
        self.pBits = ctypes.c_void_p()
        self.hbitmap = gdi32.CreateDIBSection(self.mem_dc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(self.pBits), None, 0)
        self.old_bitmap = gdi32.SelectObject(self.mem_dc, self.hbitmap)

    def start_monitoring(self) -> None:
        self._setup_win_event_hook()
        self.monitor_thread = Thread(target=self._mouse_monitor_loop, daemon=True, name="CrossHudMouseMonitor")
        self.render_thread = Thread(target=self._render_loop, daemon=True, name="CrossHudRender")
        self.hotkey_thread = Thread(target=self._hotkey_loop, daemon=True, name="CrossHudHotkey")
        self.topmost_thread = Thread(target=self._keep_on_top_loop, daemon=True, name="CrossHudTopmost")
        for thread in [self.monitor_thread, self.render_thread, self.hotkey_thread, self.topmost_thread]:
            thread.start()

    def _keep_on_top_loop(self) -> None:
        while not self.thread_stop_event.is_set():
            if self.hwnd and self.is_visible and not self.rmb_pressed:
                user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010 | 0x4000 | 0x0040)
            self.thread_stop_event.wait(0.1)

    def update_hotkey(self):
        self.hotkey_restart_event.set()
        if self.hotkey_thread_id:
            user32.PostThreadMessageW(self.hotkey_thread_id, WM_QUIT, 0, 0)

    def _hotkey_loop(self) -> None:
        HOTKEY_ID = 1
        self.hotkey_thread_id = kernel32.GetCurrentThreadId()
        while not self.thread_stop_event.is_set():
            key_name = self.settings_manager.get('hotkey', 'Insert')
            vk = self.VK_MAP.get(key_name, 0x2D)
            if user32.RegisterHotKey(None, HOTKEY_ID, 0, vk):
                msg = wintypes.MSG()
                self.hotkey_restart_event.clear()
                while not self.thread_stop_event.is_set() and not self.hotkey_restart_event.is_set():
                    result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                    if result <= 0:
                        break
                    if not self.hotkey_restart_event.is_set():
                        if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                            if self.on_toggle_callback: self.on_toggle_callback()
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                user32.UnregisterHotKey(None, HOTKEY_ID)
            else:
                self.thread_stop_event.wait(1)

    def _mouse_monitor_loop(self) -> None:
        self.mouse_thread_id = kernel32.GetCurrentThreadId()
        if self._install_mouse_hook():
            msg = wintypes.MSG()
            try:
                while not self.thread_stop_event.is_set():
                    result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                    if result <= 0:
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
            except Exception:
                logging.exception("Mouse hook loop error")
            finally:
                self._uninstall_mouse_hook()
            return

        last_state = False
        while not self.thread_stop_event.is_set():
            try:
                state = user32.GetAsyncKeyState(0x02)
                is_down = bool(state & 0x8000)
                transitioned = bool(state & 0x0001)
                if transitioned and not is_down and not last_state:
                    self._handle_mouse_event(True)
                    self._handle_mouse_event(False)
                if is_down != last_state:
                    self._handle_mouse_event(is_down)
                    last_state = is_down
                self.thread_stop_event.wait(0.005)
            except Exception:
                logging.exception("Mouse monitor loop error")
                self.thread_stop_event.wait(1)

    def _install_mouse_hook(self) -> bool:
        try:
            h_instance = kernel32.GetModuleHandleW(None)
            self.mouse_hook_handle = user32.SetWindowsHookExW(WH_MOUSE_LL, self.mouse_hook_proc, h_instance, 0)
            if self.mouse_hook_handle:
                return True
            logging.warning("Low-level mouse hook unavailable, falling back to polling")
        except Exception:
            logging.exception("Failed to install low-level mouse hook")
        return False

    def _uninstall_mouse_hook(self) -> None:
        if not self.mouse_hook_handle:
            return
        try:
            user32.UnhookWindowsHookEx(self.mouse_hook_handle)
        except Exception:
            logging.exception("Failed to unhook low-level mouse hook")
        finally:
            self.mouse_hook_handle = None

    def _low_level_mouse_proc(self, n_code, w_param, l_param):
        try:
            if n_code >= 0:
                if w_param in (WM_RBUTTONDOWN, WM_RBUTTONDBLCLK):
                    self._handle_mouse_event(True)
                elif w_param == WM_RBUTTONUP:
                    self._handle_mouse_event(False)
        except Exception:
            logging.exception("Low-level mouse hook callback error")
        return user32.CallNextHookEx(self.mouse_hook_handle, n_code, w_param, l_param)

    def _handle_mouse_event(self, is_down: bool) -> None:
        m = self.settings_manager.get('rmb_hide_mode', 'disabled')
        enabled = self.settings_manager.get('enabled', False)
        if m == 'hold' and enabled:
            self.rmb_pressed = is_down
            self.command_queue.put(('hide' if is_down else 'show', None))
        elif m == 'toggle':
            if not is_down and self.rmb_pressed:
                if self.on_toggle_callback: self.on_toggle_callback()
            self.rmb_pressed = is_down

    def _render_loop(self) -> None:
        self.create_layered_window()
        if not self.hwnd: return
        
        if self.settings_manager.get('enabled', True):
            self.is_visible = True
            user32.ShowWindow(self.hwnd, 8) 
            self.draw_crosshair()
            
        msg = wintypes.MSG()
        while not self.thread_stop_event.is_set():
            try:
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                try:
                    while True:
                        cmd, _ = self.command_queue.get_nowait()
                        if cmd == 'show': self._show_overlay()
                        elif cmd == 'hide': self._hide_overlay()
                        elif cmd == 'draw': self.draw_crosshair()
                        elif cmd == 'recreate':
                            ns = 512
                            if ns != self.overlay_size:
                                self.overlay_size = ns
                                self.create_drawing_surface()
                            if self.settings_manager.get('enabled', False):
                                self._show_overlay()
                        elif cmd == 'reforce_top':
                            if self.hwnd and self.is_visible and not self.rmb_pressed:
                                user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010 | 0x4000 | 0x0040)
                        elif cmd == 'refresh':
                            if self.settings_manager.get('enabled', False): self.draw_crosshair()
                            else: self._hide_overlay()
                except queue.Empty: pass
                is_anim = self.settings_manager.get('rainbow_mode', False) or self.settings_manager.get('dynamic_color', False)
                if is_anim:
                    self.rainbow_hue = (self.rainbow_hue + 2) % 360
                    if self.is_visible and not self.rmb_pressed:
                        self.draw_crosshair()
                    self.thread_stop_event.wait(1 / 30)
                else:
                    if self.render_event.wait(timeout=0.1):
                        self.render_event.clear()
                        self.draw_crosshair()
            except Exception:
                logging.exception("Render loop error")
                self.thread_stop_event.wait(1)
        if self.mem_dc:
            if self.old_bitmap: gdi32.SelectObject(self.mem_dc, self.old_bitmap)
            if self.hbitmap: gdi32.DeleteObject(self.hbitmap)
            gdi32.DeleteDC(self.mem_dc)
        if self.hdc: user32.ReleaseDC(self.hwnd, self.hdc)
        if self.hwnd: user32.DestroyWindow(self.hwnd)

    def request_recreation(self) -> None:
        self.render_event.set()
        self.command_queue.put(('recreate', None))

    def _show_overlay(self) -> None:
        if not self.hwnd: return
        user32.ShowWindow(self.hwnd, 8) 
        self.is_visible = True
        self.draw_crosshair()

    def _hide_overlay(self) -> None:
        if self.hwnd: user32.ShowWindow(self.hwnd, 0)
        self.is_visible = False

    def show(self) -> None: self.command_queue.put(('show', None))
    def hide(self) -> None: self.command_queue.put(('hide', None))
    def refresh(self) -> None:
        self.render_event.set()
        self.command_queue.put(('refresh', None))

    def draw_crosshair(self) -> None:
        if not self.hwnd or not self.mem_dc or not self.is_visible: return
        try:
            sz = int(self.overlay_size)
            if sz <= 0: return

            dynamic_x = None
            if self.settings_manager.get('dynamic_color', False):
                pt = POINT()
                if user32.GetCursorPos(ctypes.byref(pt)):
                    dynamic_x = pt.x
            self.current_opacity = opacity_byte(self.settings_manager)
            data = render_crosshair_bgra(self.settings_manager, size=sz, hue=self.rainbow_hue, dynamic_x=dynamic_x)
            if data is None:
                return
            if self.pBits:
                ctypes.memmove(self.pBits, data, len(data))
            self.update_layered_window()
        except Exception as e:
            logging.error(f"Error in draw_crosshair: {e}", exc_info=True)

    def update_layered_window(self) -> None:
        if not self.hwnd or not self.mem_dc: return
        try:
            sw = self.settings_manager.get('screen_width', 1920)
            sh = self.settings_manager.get('screen_height', 1080)
            x = int((sw - self.overlay_size) / 2)
            y = int((sh - self.overlay_size) / 2)
            pd = POINT(x, y)
            ps = POINT(0, 0)
            sz = SIZE(self.overlay_size, self.overlay_size)
            
            alpha = getattr(self, 'current_opacity', 255)
            
            bl = BLENDFUNCTION(0, 0, alpha, 1)
            user32.UpdateLayeredWindow(self.hwnd, self.hdc, ctypes.byref(pd), ctypes.byref(sz), self.mem_dc, ctypes.byref(ps), 0, ctypes.byref(bl), 2)
        except Exception:
            logging.exception("Failed to update layered window")

    def cleanup(self) -> None:
        if self.cleanup_in_progress:
            return
        self.cleanup_in_progress = True
        try:
            if self.hook_handle:
                user32.UnhookWinEvent(self.hook_handle)
                self.hook_handle = None
        except Exception:
            logging.exception("Failed to unhook WinEvent")
        self.thread_stop_event.set()
        self.render_event.set()
        self.hotkey_restart_event.set()
        if self.hotkey_thread_id:
            user32.PostThreadMessageW(self.hotkey_thread_id, WM_QUIT, 0, 0)
        if self.mouse_thread_id:
            user32.PostThreadMessageW(self.mouse_thread_id, WM_QUIT, 0, 0)
        self.command_queue.put(('hide', None))
        for t in [self.monitor_thread, self.render_thread, self.hotkey_thread, self.topmost_thread]:
            if t and t.is_alive() and t is not current_thread():
                t.join(timeout=1.5)
