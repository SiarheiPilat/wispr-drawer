import pyperclip
import pyautogui
import time


def copy_to_clipboard(text: str):
    pyperclip.copy(text)


def type_at_caret(text: str):
    """Type text at the current caret position using pyautogui."""
    time.sleep(0.1)  # Brief pause to let focus return to the previous window
    pyautogui.typewrite(text, interval=0.01) if text.isascii() else _type_unicode(text)


def _type_unicode(text: str):
    """Handle non-ASCII text by using clipboard paste."""
    import pyperclip
    old = pyperclip.paste()
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.05)
    pyperclip.copy(old)
