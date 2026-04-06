import threading
from pynput import keyboard


def parse_shortcut(shortcut_str: str) -> set:
    """Parse 'ctrl+shift+a' into a set of pynput keys."""
    parts = shortcut_str.lower().split("+")
    keys = set()
    for part in parts:
        part = part.strip()
        if part == "ctrl":
            keys.add(keyboard.Key.ctrl_l)
        elif part == "shift":
            keys.add(keyboard.Key.shift_l)
        elif part == "alt":
            keys.add(keyboard.Key.alt_l)
        elif len(part) == 1:
            keys.add(keyboard.KeyCode.from_char(part))
        else:
            try:
                keys.add(keyboard.Key[part])
            except KeyError:
                pass
    return keys


class HotkeyManager:
    def __init__(self):
        self._listener = None
        self._pressed_keys = set()
        self._bindings = {}  # shortcut_str -> {"on_press": fn, "on_release": fn}
        self._active_shortcut = None
        self._lock = threading.Lock()

    def register(self, shortcut_str: str, on_press, on_release):
        self._bindings[shortcut_str] = {
            "keys": parse_shortcut(shortcut_str),
            "on_press": on_press,
            "on_release": on_release,
        }

    def unregister_all(self):
        self._bindings.clear()
        self._active_shortcut = None

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _normalize_key(self, key):
        """Normalize key variants (e.g., ctrl_r -> ctrl_l)."""
        if key == keyboard.Key.ctrl_r:
            return keyboard.Key.ctrl_l
        if key == keyboard.Key.shift_r:
            return keyboard.Key.shift_l
        if key == keyboard.Key.alt_r:
            return keyboard.Key.alt_l
        return key

    def _on_press(self, key):
        key = self._normalize_key(key)
        with self._lock:
            self._pressed_keys.add(key)
            if self._active_shortcut:
                return  # Already activated, ignore additional presses
            for shortcut_str, binding in self._bindings.items():
                if binding["keys"].issubset(self._pressed_keys):
                    self._active_shortcut = shortcut_str
                    try:
                        binding["on_press"]()
                    except Exception as e:
                        print(f"Error in hotkey press handler: {e}")
                    return

    def _on_release(self, key):
        key = self._normalize_key(key)
        with self._lock:
            self._pressed_keys.discard(key)
            # Also discard the un-normalized version
            if hasattr(key, 'char'):
                self._pressed_keys.discard(key)

            if self._active_shortcut:
                binding = self._bindings.get(self._active_shortcut)
                if binding and not binding["keys"].issubset(self._pressed_keys):
                    shortcut = self._active_shortcut
                    self._active_shortcut = None
                    try:
                        binding["on_release"]()
                    except Exception as e:
                        print(f"Error in hotkey release handler: {e}")
