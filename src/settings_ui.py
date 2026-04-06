import tkinter as tk
from tkinter import ttk, messagebox


class SettingsWindow:
    def __init__(self, config, on_save_callback=None):
        self.config = config
        self.on_save = on_save_callback
        self._window = None

    def show(self):
        if self._window and self._window.winfo_exists():
            self._window.lift()
            return

        self._window = tk.Toplevel()
        self._window.title("Wispr Drawer — Settings")
        self._window.geometry("450x400")
        self._window.resizable(False, False)

        frame = ttk.Frame(self._window, padding=20)
        frame.pack(fill="both", expand=True)

        # API Key
        ttk.Label(frame, text="OpenAI API Key:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self._api_key_var = tk.StringVar(value=self.config.get("openai_api_key"))
        api_entry = ttk.Entry(frame, textvariable=self._api_key_var, width=40, show="*")
        api_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        # Shortcut A
        ttk.Label(frame, text="Voice Memo Shortcut:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self._shortcut_a_var = tk.StringVar(value=self.config.get("shortcut_a"))
        ttk.Entry(frame, textvariable=self._shortcut_a_var, width=40).grid(row=1, column=1, sticky="ew", pady=(0, 5))

        # Shortcut B
        ttk.Label(frame, text="Screenshot Shortcut:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self._shortcut_b_var = tk.StringVar(value=self.config.get("shortcut_b"))
        ttk.Entry(frame, textvariable=self._shortcut_b_var, width=40).grid(row=2, column=1, sticky="ew", pady=(0, 5))

        # Toggles
        ttk.Separator(frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        self._clipboard_var = tk.BooleanVar(value=self.config.get("copy_to_clipboard"))
        ttk.Checkbutton(frame, text="Copy transcription to clipboard", variable=self._clipboard_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=2
        )

        self._caret_var = tk.BooleanVar(value=self.config.get("insert_at_caret"))
        ttk.Checkbutton(frame, text="Insert transcription at caret position", variable=self._caret_var).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=2
        )

        self._save_audio_var = tk.BooleanVar(value=self.config.get("save_audio"))
        ttk.Checkbutton(frame, text="Save audio recordings locally", variable=self._save_audio_var).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=2
        )

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._window.destroy).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def _save(self):
        api_key = self._api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Missing API Key", "Please enter your OpenAI API key.")
            return

        self.config.set("openai_api_key", api_key)
        self.config.set("shortcut_a", self._shortcut_a_var.get().strip().lower())
        self.config.set("shortcut_b", self._shortcut_b_var.get().strip().lower())
        self.config.set("copy_to_clipboard", self._clipboard_var.get())
        self.config.set("insert_at_caret", self._caret_var.get())
        self.config.set("save_audio", self._save_audio_var.get())

        if self.on_save:
            self.on_save()

        self._window.destroy()
