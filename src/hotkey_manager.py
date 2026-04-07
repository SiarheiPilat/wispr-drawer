import threading
from pynput import keyboard


# Virtual key codes for letters on Windows
_VK_CODES = {chr(i): 0x41 + i - ord('a') for i in range(ord('a'), ord('z') + 1)}


def parse_shortcut(shortcut_str: str) -> tuple:
    """Parse 'ctrl+shift+a' into modifier flags + a vk code for the letter."""
    parts = shortcut_str.lower().split("+")
    modifiers = set()
    vk = None
    for part in parts:
        part = part.strip()
        if part in ("ctrl", "control"):
            modifiers.add("ctrl")
        elif part == "shift":
            modifiers.add("shift")
        elif part in ("alt", "menu"):
            modifiers.add("alt")
        elif len(part) == 1 and part in _VK_CODES:
            vk = _VK_CODES[part]
        else:
            try:
                keyboard.Key[part]
                modifiers.add(part)
            except KeyError:
                pass
    return (frozenset(modifiers), vk)


class HotkeyManager:
    def __init__(self):
        self._listener = None
        self._held_modifiers = set()  # "ctrl", "shift", "alt"
        self._held_vks = set()        # virtual key codes
        self._bindings = {}           # shortcut_str -> {parsed, on_press, on_release}
        self._active_shortcut = None
        self._lock = threading.Lock()

    def register(self, shortcut_str: str, on_press, on_release):
        self._bindings[shortcut_str] = {
            "parsed": parse_shortcut(shortcut_str),
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

    def _extract_info(self, key):
        """Extract modifier name or vk code from a key event."""
        modifier = None
        vk = None
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            modifier = "ctrl"
        elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r, keyboard.Key.shift):
            modifier = "shift"
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            modifier = "alt"
        elif hasattr(key, 'vk') and key.vk is not None:
            vk = key.vk
        return modifier, vk

    def _check_match(self, modifiers_needed, vk_needed):
        """Check if the currently held keys satisfy a binding."""
        if not modifiers_needed.issubset(self._held_modifiers):
            return False
        if vk_needed is not None and vk_needed not in self._held_vks:
            return False
        return True

    def _on_press(self, key):
        modifier, vk = self._extract_info(key)
        with self._lock:
            if modifier:
                self._held_modifiers.add(modifier)
            if vk is not None:
                self._held_vks.add(vk)

            if self._active_shortcut:
                return

            for shortcut_str, binding in self._bindings.items():
                mods, bvk = binding["parsed"]
                if self._check_match(mods, bvk):
                    self._active_shortcut = shortcut_str
                    try:
                        binding["on_press"]()
                    except Exception as e:
                        print(f"Error in hotkey press handler: {e}")
                    return

    def _on_release(self, key):
        modifier, vk = self._extract_info(key)
        with self._lock:
            if modifier:
                self._held_modifiers.discard(modifier)
            if vk is not None:
                self._held_vks.discard(vk)

            if self._active_shortcut:
                binding = self._bindings.get(self._active_shortcut)
                if binding:
                    mods, bvk = binding["parsed"]
                    if not self._check_match(mods, bvk):
                        self._active_shortcut = None
                        try:
                            binding["on_release"]()
                        except Exception as e:
                            print(f"Error in hotkey release handler: {e}")
