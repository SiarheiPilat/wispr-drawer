import ctypes
import os
import subprocess
import tempfile
import time

import pyperclip
import pyautogui


def send_to_claude(text: str, working_dir: str = None, delivery: str = "new_session",
                   terminal_title: str = ""):
    """Send a voice command to Claude Code.

    delivery:
        "new_session"  — opens a new terminal and pipes text into claude --print
        "attached"     — pastes text + Enter into an existing terminal window
    terminal_title:
        Substring to match against window titles when delivery="attached".
        If empty, targets the foreground window.
    """
    if delivery == "attached":
        _send_to_attached(text, terminal_title)
    else:
        _send_new_session(text, working_dir)


def _send_new_session(text: str, working_dir: str = None):
    """Open a new terminal window and pipe text into claude --print."""
    fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="wispr_cmd_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)

    tmp_win = tmp_path.replace("/", "\\")
    inner = f"type {tmp_win} | claude --print & del {tmp_win}"
    subprocess.Popen(
        ["cmd.exe", "/c", "start", "Claude Code", "cmd", "/k", inner],
        cwd=working_dir,
    )
    print(f"Sent to Claude Code (new session): {text[:80]}")


def _send_to_attached(text: str, terminal_title: str = ""):
    """Paste text + Enter into an existing terminal window."""
    target_hwnd = None

    if terminal_title:
        target_hwnd = _find_window_by_title(terminal_title)
        if not target_hwnd:
            print(f"No window found matching '{terminal_title}'. Falling back to foreground window.")

    # Save previous clipboard content
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    pyperclip.copy(text)

    if target_hwnd:
        _focus_window(target_hwnd)
        time.sleep(0.15)  # let the window come to foreground

    # Ctrl+V to paste, then Enter to send
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.05)
    pyautogui.press("enter")

    # Restore previous clipboard after a short delay
    time.sleep(0.2)
    try:
        pyperclip.copy(old_clipboard)
    except Exception:
        pass

    print(f"Sent to terminal (attached): {text[:80]}")


# ── Windows API helpers ──

# user32 handle
_user32 = ctypes.windll.user32

# Callback type for EnumWindows
_EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))


def _find_window_by_title(substring: str):
    """Find the first window whose title contains the given substring (case-insensitive)."""
    result = []
    substring_lower = substring.lower()

    def callback(hwnd, _):
        length = _user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            _user32.GetWindowTextW(hwnd, buf, length + 1)
            if substring_lower in buf.value.lower():
                if _user32.IsWindowVisible(hwnd):
                    result.append(hwnd)
                    return False  # stop enumerating
        return True

    _user32.EnumWindows(_EnumWindowsProc(callback), 0)
    return result[0] if result else None


def _focus_window(hwnd):
    """Bring a window to the foreground."""
    SW_RESTORE = 9
    if _user32.IsIconic(hwnd):
        _user32.ShowWindow(hwnd, SW_RESTORE)
    _user32.SetForegroundWindow(hwnd)
