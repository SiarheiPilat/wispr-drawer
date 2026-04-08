# Wispr Drawer

A Windows background utility for voice-to-text transcription and annotated screenshots. Runs in the system tray with global hotkeys.

## Requirements

* Python 3.10+
* OpenAI API key (for Whisper transcription)
* Microphone

## Setup

```Shell
pip install -r requirements.txt
python src/main.py
```

On first launch you'll be prompted for your OpenAI API key and asked to select a project folder. The app then minimizes to the system tray.

## Features

### Voice Memo (Ctrl+Shift+A)

Hold the shortcut to record, release to transcribe. Transcriptions are saved to `transcriptions.jsonl` in your project folder.

Toggle options in Settings:

* **Copy to clipboard** (default ON) — transcription goes to clipboard
* **Insert at caret** (default OFF) — types transcription at your cursor position
* **Save audio** (default OFF) — saves WAV files to `recordings/`

### Annotated Screenshot (Ctrl+Shift+B)

Hold the shortcut to record voice and draw on screen with a red pen. Release to capture a screenshot with your drawings composited on top.

Saves to your project folder:

* `screenshots/YYYY-MM-DD_HH-MM-SS.png` — screenshot with drawings
* `annotations.jsonl` — transcription with reference to the screenshot

### Wake Word Modes

Enable wake word detection in Settings to use hands-free voice commands. Say the configured wake word (default: "hey jarvis") to activate.

**Simple Input** — Transcribes your voice and inserts text at the caret (same as Voice Memo, but hands-free).

**AI Actor** — Say the wake word, speak a single command (stops on silence), and it gets sent to Claude Code in a terminal window.

**AI Actor Plus** — Say the wake word, speak **continuously** for as long as you want (pauses won't stop recording), then say the wake word **again** to stop. All accumulated speech is transcribed and sent to Claude Code at once. A lower-pitched beep confirms the stop.

Settings for wake word modes:

* **Sensitivity** (0.1–0.9) — wake word detection confidence threshold
* **Silence wait** — seconds of silence to end capture (AI Actor only)
* **Max command** — safety limit in seconds (AI Actor)
* **Max command — Plus** — safety limit in seconds for AI Actor Plus (default 120s)

### Claude Delivery

Controls how transcribed commands reach Claude Code:

* **New Session** (default) — opens a new terminal window and runs `claude --print` each time. Stateless — each command is independent.
* **Attached Terminal** — pastes the transcribed text into an existing terminal window and presses Enter. Stateful — Claude remembers conversation context. Start a `claude` session in your terminal first, then use this mode.

When using Attached Terminal, set **Terminal window title** to a substring of the target window's title (e.g. "claude" or "Windows PowerShell"). If left empty, the command is sent to whichever window is in the foreground.

### System Tray

Right-click the tray icon for:

* **Settings** — change shortcuts, toggles, API key
* **Open Project Folder** — opens the project directory
* **Quit**

## Data Formats

### transcriptions.jsonl

```JSON
{"timestamp": "2026-04-07T14:30:00", "text": "Remember to fix the auth flow"}
```

### annotations.jsonl

```JSON
{"timestamp": "2026-04-07T14:32:00", "text": "This button should be moved left", "screenshot": "screenshots/2026-04-07_14-32-00.png"}
```

### config.json

```JSON
{
  "openai_api_key": "",
  "shortcut_a": "ctrl+shift+a",
  "shortcut_b": "ctrl+shift+b",
  "copy_to_clipboard": true,
  "insert_at_caret": false,
  "save_audio": false,
  "wake_word_enabled": false,
  "wake_word_mode": "simple_input",
  "wake_word_model": "hey_jarvis",
  "wake_word_sensitivity": 0.5,
  "wake_word_silence_duration": 1.5,
  "wake_word_max_duration": 15,
  "wake_word_max_duration_plus": 120,
  "claude_delivery": "new_session",
  "claude_terminal_title": ""
}
```

## Building an Executable

To compile into a standalone `.exe` (no Python required to run):

```Shell
pip install pyinstaller
pyinstaller --onefile --windowed --name WisprDrawer src/main.py
```

The executable will be at `dist/WisprDrawer.exe`. You can add it to your Windows Startup folder to launch automatically on boot.
