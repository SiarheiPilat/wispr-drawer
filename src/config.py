import json
import os

DEFAULT_CONFIG = {
    "openai_api_key": "",
    "shortcut_a": "ctrl+shift+a",
    "shortcut_b": "ctrl+shift+b",
    "copy_to_clipboard": True,
    "insert_at_caret": False,
    "save_audio": False,
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
