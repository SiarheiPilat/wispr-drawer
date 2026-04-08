import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from audio_recorder import AudioRecorder
from transcriber import transcribe
from overlay import RecordingOverlay, DrawingOverlay
from screenshot import capture_screen, composite_with_drawings, save_screenshot
from clipboard_util import copy_to_clipboard, type_at_caret
from transcript_log import append_transcription, append_annotation
from hotkey_manager import HotkeyManager
from settings_ui import SettingsWindow
from toast import show_toast
from wake_word import WakeWordListener
from claude_actor import send_to_claude

try:
    import pystray
    from PIL import Image, ImageDraw as PilImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


class WisprDrawer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window

        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = Config(self.app_dir)
        self.project_dir = None

        self.recorder = AudioRecorder(device=self.config.get("mic_device"))
        self.hotkey_manager = HotkeyManager()
        self.recording_overlay = RecordingOverlay()
        self.drawing_overlay = DrawingOverlay()
        self.settings_window = SettingsWindow(self.config, on_save_callback=self._on_settings_saved)
        self.wake_listener = None

        self._tray_icon = None

    def start(self):
        # Check API key first
        if not self.config.get("openai_api_key"):
            self._show_api_key_prompt()

        # Pick project folder
        self.project_dir = self._pick_project_folder()
        if not self.project_dir:
            messagebox.showerror("No Folder", "You must select a project folder. Exiting.")
            sys.exit(1)

        print(f"Project folder: {self.project_dir}")
        print(f"Voice memo shortcut: {self.config.get('shortcut_a')}")
        print(f"Screenshot shortcut: {self.config.get('shortcut_b')}")
        if self.config.get("wake_word_enabled"):
            print(f"Wake word: {self.config.get('wake_word_model')} (sensitivity: {self.config.get('wake_word_sensitivity')})")
        print("Wispr Drawer is running. Use your shortcuts or right-click the tray icon.")

        # Register hotkeys
        self._register_hotkeys()
        self.hotkey_manager.start()

        # Start wake word listener if enabled
        self._start_wake_listener()

        # Start tray icon
        if HAS_TRAY:
            threading.Thread(target=self._run_tray, daemon=True).start()

        # Keep tkinter alive for overlays
        self.root.mainloop()

    def _show_api_key_prompt(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Wispr Drawer — API Key")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Enter your OpenAI API Key:").pack(anchor="w")
        entry = tk.Entry(frame, width=50, show="*")
        entry.pack(fill="x", pady=(5, 10))

        def save():
            key = entry.get().strip()
            if key:
                self.config.set("openai_api_key", key)
                dialog.destroy()
            else:
                messagebox.showwarning("Required", "API key is required.")

        tk.Button(frame, text="Save", command=save).pack()

        dialog.wait_window()

    def _pick_project_folder(self) -> str | None:
        folder = filedialog.askdirectory(title="Select Project Folder for Wispr Drawer")
        return folder if folder else None

    def _register_hotkeys(self):
        self.hotkey_manager.unregister_all()
        self.hotkey_manager.register(
            self.config.get("shortcut_a"),
            on_press=self._on_voice_memo_press,
            on_release=self._on_voice_memo_release,
        )
        self.hotkey_manager.register(
            self.config.get("shortcut_b"),
            on_press=self._on_screenshot_press,
            on_release=self._on_screenshot_release,
        )

    def _start_wake_listener(self):
        if self.wake_listener:
            self.wake_listener.stop()
            self.wake_listener = None

        if not self.config.get("wake_word_enabled"):
            return

        try:
            mode = self.config.get("wake_word_mode")
            capture_mode = "wake_word_stop" if mode == "ai_actor_plus" else "silence"
            self.wake_listener = WakeWordListener(
                model_name=self.config.get("wake_word_model"),
                sensitivity=self.config.get("wake_word_sensitivity"),
                mic_device=self.config.get("mic_device"),
                on_command=self._on_wake_command,
                silence_duration=self.config.get("wake_word_silence_duration"),
                max_duration=self.config.get("wake_word_max_duration"),
                capture_mode=capture_mode,
                max_duration_plus=self.config.get("wake_word_max_duration_plus"),
            )
            self.wake_listener.start()
        except Exception as e:
            print(f"Failed to start wake word listener: {e}")
            self.wake_listener = None

    def _on_wake_command(self, audio_data):
        """Handle voice command captured after wake word."""
        mode = self.config.get("wake_word_mode")
        if mode in ("ai_actor", "ai_actor_plus"):
            self._process_ai_actor(audio_data)
        else:
            self._process_voice_memo(audio_data)

    def _process_ai_actor(self, audio_data):
        """Transcribe voice command and send it to Claude Code."""
        try:
            if AudioRecorder.is_silent(audio_data):
                print("No voice command detected.")
                return

            temp_path = self.recorder.save_temp_wav(audio_data)
            api_key = self.config.get("openai_api_key")
            text = transcribe(temp_path, api_key)
            print(f"AI Actor command: {text}")

            show_toast(f"Sending to Claude: {text[:60]}...")
            send_to_claude(
                text,
                working_dir=self.project_dir,
                delivery=self.config.get("claude_delivery"),
                terminal_title=self.config.get("claude_terminal_title"),
            )

        except Exception as e:
            print(f"AI Actor error: {e}")
            show_toast(f"AI Actor failed: {e}")

    def _on_settings_saved(self):
        """Re-register hotkeys and update mic device after settings change."""
        self.hotkey_manager.stop()
        self._register_hotkeys()
        self.hotkey_manager.start()
        self.recorder.device = self.config.get("mic_device")
        self._start_wake_listener()
        print("Settings saved. Hotkeys re-registered.")

    # ── Feature A: Voice Memo ──

    def _on_voice_memo_press(self):
        print("Recording voice memo...")
        if self.wake_listener:
            self.wake_listener.pause()
        self.recording_overlay.show()
        self.recorder.start()

    def _on_voice_memo_release(self):
        print("Processing voice memo...")
        audio_data = self.recorder.stop()
        self.recording_overlay.hide()
        if self.wake_listener:
            self.wake_listener.resume()

        if audio_data is None or len(audio_data) == 0 or AudioRecorder.is_silent(audio_data):
            print("No audio captured.")
            return

        threading.Thread(target=self._process_voice_memo, args=(audio_data,), daemon=True).start()

    def _process_voice_memo(self, audio_data):
        try:
            # Save audio if enabled
            wav_path = None
            if self.config.get("save_audio"):
                wav_path = self.recorder.save_wav(audio_data, self.project_dir)
                print(f"Audio saved: {wav_path}")

            # Save temp file for transcription
            temp_path = self.recorder.save_temp_wav(audio_data)

            # Transcribe
            api_key = self.config.get("openai_api_key")
            text = transcribe(temp_path, api_key)
            print(f"Transcription: {text}")

            # Log
            append_transcription(self.project_dir, text, audio_path=wav_path)

            # Clipboard
            if self.config.get("copy_to_clipboard"):
                copy_to_clipboard(text)

            # Insert at caret
            if self.config.get("insert_at_caret"):
                type_at_caret(text)

            preview = text[:80] + "..." if len(text) > 80 else text
            show_toast(f"Transcription saved: {preview}")

        except Exception as e:
            print(f"Voice memo error: {e}")
            show_toast(f"Voice memo failed: {e}")
            append_transcription(self.project_dir, f"[transcription failed: {e}]")

    # ── Feature B: Annotated Screenshot ──

    def _on_screenshot_press(self):
        print("Recording + drawing mode...")
        if self.wake_listener:
            self.wake_listener.pause()
        self.recording_overlay.show()
        self.drawing_overlay.show()
        self.recorder.start()

    def _on_screenshot_release(self):
        print("Processing annotated screenshot...")
        audio_data = self.recorder.stop()
        lines = self.drawing_overlay.get_drawing_lines()
        self.drawing_overlay.hide()
        self.recording_overlay.hide()
        if self.wake_listener:
            self.wake_listener.resume()

        threading.Thread(
            target=self._process_screenshot, args=(audio_data, lines), daemon=True
        ).start()

    def _process_screenshot(self, audio_data, lines):
        try:
            # Capture screen
            screen = capture_screen()

            # Composite drawings onto screenshot
            composited = composite_with_drawings(screen, lines)

            # Save screenshot
            screenshot_path = save_screenshot(composited, self.project_dir)
            print(f"Screenshot saved: {screenshot_path}")

            # Transcribe if we have non-silent audio
            text = ""
            wav_path = None
            has_audio = (audio_data is not None and len(audio_data) > 0
                         and not AudioRecorder.is_silent(audio_data))
            if has_audio:
                if self.config.get("save_audio"):
                    wav_path = self.recorder.save_wav(audio_data, self.project_dir)

                temp_path = self.recorder.save_temp_wav(audio_data)
                api_key = self.config.get("openai_api_key")
                text = transcribe(temp_path, api_key)
                print(f"Transcription: {text}")

            # Log annotation
            append_annotation(self.project_dir, text, screenshot_path, audio_path=wav_path)

            preview = text[:60] + "..." if len(text) > 60 else text
            show_toast(f"Screenshot saved with annotation: {preview}")

        except Exception as e:
            print(f"Screenshot error: {e}")
            show_toast(f"Screenshot failed: {e}")

    # ── System Tray ──

    def _create_tray_image(self):
        img = Image.new("RGB", (64, 64), "black")
        draw = PilImageDraw.Draw(img)
        draw.ellipse([16, 16, 48, 48], fill="red")
        return img

    def _run_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Settings", lambda: self.root.after(0, self.settings_window.show)),
            pystray.MenuItem(
                "Open Project Folder",
                lambda: os.startfile(self.project_dir) if self.project_dir else None,
            ),
            pystray.MenuItem("Quit", self._quit),
        )
        self._tray_icon = pystray.Icon("wispr_drawer", self._create_tray_image(), "Wispr Drawer", menu)
        self._tray_icon.run()

    def _quit(self):
        self.hotkey_manager.stop()
        if self.wake_listener:
            self.wake_listener.stop()
        if self._tray_icon:
            self._tray_icon.stop()
        self.root.after(0, self.root.destroy)


if __name__ == "__main__":
    app = WisprDrawer()
    app.start()
