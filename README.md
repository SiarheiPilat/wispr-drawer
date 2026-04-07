# Wispr Drawer

A Windows background utility for voice-to-text transcription and annotated screenshots. Runs in the system tray with global hotkeys.

## Requirements

- Python 3.10+
- OpenAI API key (for Whisper transcription)
- Microphone

## Setup

```bash
pip install -r requirements.txt
python src/main.py
```

On first launch you'll be prompted for your OpenAI API key and asked to select a project folder. The app then minimizes to the system tray.

## Features

### Voice Memo (Ctrl+Shift+A)

Hold the shortcut to record, release to transcribe. Transcriptions are saved to `transcriptions.jsonl` in your project folder.

Toggle options in Settings:
- **Copy to clipboard** (default ON) — transcription goes to clipboard
- **Insert at caret** (default OFF) — types transcription at your cursor position
- **Save audio** (default OFF) — saves WAV files to `recordings/`

### Annotated Screenshot (Ctrl+Shift+B)

Hold the shortcut to record voice and draw on screen with a red pen. Release to capture a screenshot with your drawings composited on top.

Saves to your project folder:
- `screenshots/YYYY-MM-DD_HH-MM-SS.png` — screenshot with drawings
- `annotations.jsonl` — transcription with reference to the screenshot

### System Tray

Right-click the tray icon for:
- **Settings** — change shortcuts, toggles, API key
- **Open Project Folder** — opens the project directory
- **Quit**

## Data Formats

### transcriptions.jsonl

```json
{"timestamp": "2026-04-07T14:30:00", "text": "Remember to fix the auth flow"}
```

### annotations.jsonl

```json
{"timestamp": "2026-04-07T14:32:00", "text": "This button should be moved left", "screenshot": "screenshots/2026-04-07_14-32-00.png"}
```

### config.json

```json
{
  "openai_api_key": "",
  "shortcut_a": "ctrl+shift+a",
  "shortcut_b": "ctrl+shift+b",
  "copy_to_clipboard": true,
  "insert_at_caret": false,
  "save_audio": false
}
```

## Building an Executable

To compile into a standalone `.exe` (no Python required to run):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name WisprDrawer src/main.py
```

The executable will be at `dist/WisprDrawer.exe`. You can add it to your Windows Startup folder to launch automatically on boot.
