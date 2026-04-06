# Wispr Drawer — Design Spec

## Context

A Windows 10 background utility for voice-to-text transcription and annotated screenshots, aimed at capturing thoughts and visual context while working on a project. Must be runnable without compilation (`python main.py`).

## Tech Stack

- **Language:** Python 3.10+
- **Global hotkeys:** `pynput`
- **Audio recording:** `sounddevice` + `soundfile` (WAV format)
- **Transcription:** OpenAI Whisper API (`openai` package)
- **Overlay/Drawing UI:** `tkinter` (transparent windows)
- **Screenshots:** `Pillow` (ImageGrab)
- **Clipboard:** `pyperclip`
- **Caret insertion:** `pyautogui`
- **Config persistence:** JSON file in project directory
- **Logging:** Python `logging` module

## Architecture

```
main.py                 — Entry point, tray icon, project folder selection
├── hotkey_manager.py   — Global hotkey registration/listening (pynput)
├── audio_recorder.py   — Microphone recording (sounddevice)
├── transcriber.py      — Whisper API call
├── overlay.py          — Tkinter transparent overlay (recording icon + drawing canvas)
├── screenshot.py       — Screen capture + drawing composite
├── clipboard_util.py   — Copy to clipboard / type at caret
├── config.py           — Settings load/save (JSON)
├── transcript_log.py   — Append transcriptions to log file
└── settings_ui.py      — Settings window (shortcuts, toggles)
```

## Feature A: Voice Memo (Shortcut A — default Ctrl+Shift+A)

1. User presses and holds shortcut → `audio_recorder` starts recording, `overlay` shows red pulsing recording dot (top-right corner)
2. User speaks into microphone
3. User releases shortcut → recording stops, overlay hides
4. Audio sent to Whisper API → transcription returned
5. Transcription appended to `transcriptions.jsonl` in project folder with timestamp
6. Based on toggle settings:
   - **Copy to clipboard** (default ON): transcription copied via `pyperclip`
   - **Insert at caret** (default OFF): transcription typed via `pyautogui`
   - **Save audio** (default OFF): WAV file saved to `recordings/` subfolder with timestamp filename

## Feature B: Annotated Screenshot (Shortcut B — default Ctrl+Shift+B)

1. User presses and holds shortcut → `audio_recorder` starts recording, `overlay` shows recording dot AND fullscreen transparent drawing canvas
2. Cursor changes to crosshair pen. User can draw freehand (red lines) on the transparent overlay
3. User speaks to describe what they're annotating
4. User releases shortcut → recording stops, screenshot taken, overlay captured
5. Screenshot of the actual screen is taken (without overlay). Drawing overlay is captured separately. Both are composited into a single image.
6. Audio sent to Whisper API → transcription returned
7. Saved to project folder:
   - `screenshots/YYYY-MM-DD_HH-MM-SS.png` — composited screenshot with drawings
   - Transcription appended to `annotations.jsonl` with timestamp + reference to screenshot filename

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

## UI Elements

- **System tray icon:** Shows app is running. Right-click menu: Settings, Open Project Folder, Quit
- **Recording overlay:** Small red pulsing circle, top-right corner, always-on-top, click-through
- **Drawing canvas (Feature B only):** Fullscreen transparent window, always-on-top, captures mouse for drawing. Red pen, 3px width.
- **Settings window:** Simple tkinter window for changing shortcuts, toggles, API key
- **Project folder picker:** Standard folder dialog on first launch

## Startup Flow

1. App launches → check for `config.json` in app directory
2. If no API key set → prompt for it in settings
3. Show folder picker dialog for project directory
4. Register global hotkeys
5. Minimize to system tray
6. Listen for hotkey events

## Error Handling

- No microphone: show toast notification, skip recording
- API failure: save transcription as "[transcription failed]", keep audio if save_audio enabled
- No project folder selected: re-prompt

## Verification

1. Run `python main.py`
2. Select a test project folder
3. Press Ctrl+Shift+A, speak, release → check transcriptions.jsonl has entry
4. Enable clipboard toggle → verify transcription appears in clipboard
5. Press Ctrl+Shift+B, speak + draw, release → check screenshots/ folder and annotations.jsonl
6. Open settings → change shortcuts → verify new shortcuts work
