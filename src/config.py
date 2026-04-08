import json
import os

DEFAULT_CONFIG = {
    "openai_api_key": "",
    "shortcut_a": "ctrl+win",
    "shortcut_b": "ctrl+shift+b",
    "copy_to_clipboard": True,
    "insert_at_caret": False,
    "save_audio": False,
    "mic_device": None,
    "wake_word_mode": "simple_input",
    "wake_word_enabled": False,
    "wake_word_model": "hey_jarvis",
    "wake_word_sensitivity": 0.5,
    "wake_word_silence_duration": 1.5,
    "wake_word_max_duration": 15,
    "wake_word_max_duration_plus": 120,
    "claude_delivery": "new_session",
    "claude_terminal_title": "",
}

CONFIG_FILENAME = "config.json"


class Config:
    def __init__(self, app_dir: str):
        self.path = os.path.join(app_dir, CONFIG_FILENAME)
        self.data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                saved = json.load(f)
            self.data.update(saved)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str):
        return self.data.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value):
        self.data[key] = value
        self.save()
