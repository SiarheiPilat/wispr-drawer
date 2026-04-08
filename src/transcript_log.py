import json
import os
from datetime import datetime


def append_transcription(project_dir: str, text: str, audio_path: str = None):
    path = os.path.join(project_dir, "transcriptions.jsonl")
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "text": text,
    }
    if audio_path:
        entry["recording"] = os.path.relpath(audio_path, project_dir)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def append_annotation(project_dir: str, text: str, screenshot_path: str, audio_path: str = None):
    path = os.path.join(project_dir, "annotations.jsonl")
    # Store relative path to screenshot
    rel_path = os.path.relpath(screenshot_path, project_dir)
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "text": text,
        "screenshot": rel_path,
    }
    if audio_path:
        entry["recording"] = os.path.relpath(audio_path, project_dir)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
