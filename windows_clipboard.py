"""Explicit Unicode clipboard transfers. No monitoring or history."""
import ctypes as C
from ctypes import wintypes as W
import threading
import time

_lock = threading.Lock()
MAX_TEXT = 2000


def clipboard(action, text=None):
    if action not in ('read', 'write'):
        raise ValueError('Action presse-papiers inconnue')
    if action == 'write' and (not isinstance(text, str) or len(text) > MAX_TEXT or '\0' in text):
        raise ValueError('Presse-papiers : texte de 2 000 caractères maximum, sans caractère nul.')
    user = C.WinDLL('user32', use_last_error=True)
    kernel = C.WinDLL('kernel32', use_last_error=True)
    user.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
                                   C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, C.c_void_p]
    user.CreateWindowExW.restype = W.HWND
    user.DestroyWindow.argtypes = [W.HWND]
    user.OpenClipboard.argtypes = [W.HWND]
    user.GetClipboardData.argtypes = [W.UINT]
    user.GetClipboardData.restype = W.HANDLE
    user.SetClipboardData.argtypes = [W.UINT, W.HANDLE]
    user.SetClipboardData.restype = W.HANDLE
    kernel.GlobalAlloc.argtypes = [W.UINT, C.c_size_t]
    kernel.GlobalAlloc.restype = W.HANDLE
    kernel.GlobalLock.argtypes = [W.HANDLE]
    kernel.GlobalLock.restype = C.c_void_p
    kernel.GlobalUnlock.argtypes = [W.HANDLE]
    kernel.GlobalFree.argtypes = [W.HANDLE]
    kernel.GlobalSize.argtypes = [W.HANDLE]
    kernel.GlobalSize.restype = C.c_size_t
    with _lock:
        owner = user.CreateWindowExW(0, 'STATIC', '', 0, 0, 0, 0, 0, W.HWND(-3), None, None, None)
        if not owner:
            raise ValueError('Presse-papiers Windows indisponible')
        opened = False
        allocated = None
        try:
            for _ in range(10):
                if user.OpenClipboard(owner):
                    opened = True
                    break
                time.sleep(.02)
            if not opened:
                raise ValueError('Presse-papiers occupé. Réessaie dans un instant.')
            if action == 'read':
                handle = user.GetClipboardData(13)  # CF_UNICODETEXT
                if not handle:
                    raise ValueError('Le presse-papiers du PC ne contient pas de texte.')
                size = kernel.GlobalSize(handle)
                pointer = kernel.GlobalLock(handle)
                if not pointer:
                    raise ValueError('Lecture du presse-papiers impossible')
                try:
                    raw = C.string_at(pointer, min(size, (MAX_TEXT * 2 + 2) * 2))
                    value = raw.decode('utf-16-le').split('\0', 1)[0]
                finally:
                    kernel.GlobalUnlock(handle)
                if len(value) > MAX_TEXT:
                    raise ValueError('Texte trop long : 2 000 caractères maximum.')
                return value
            raw = (text + '\0').encode('utf-16-le')
            allocated = kernel.GlobalAlloc(0x0002, len(raw))
            if not allocated:
                raise ValueError('Mémoire presse-papiers indisponible')
            pointer = kernel.GlobalLock(allocated)
            if not pointer:
                raise ValueError('Écriture du presse-papiers impossible')
            C.memmove(pointer, raw, len(raw))
            kernel.GlobalUnlock(allocated)
            if not user.EmptyClipboard() or not user.SetClipboardData(13, allocated):
                raise ValueError('Écriture du presse-papiers impossible')
            allocated = None  # Windows owns the memory now.
        finally:
            if allocated:
                kernel.GlobalFree(allocated)
            if opened:
                user.CloseClipboard()
            user.DestroyWindow(owner)
