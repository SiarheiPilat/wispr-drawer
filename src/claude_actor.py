import os
import subprocess
import tempfile


def send_to_claude(text: str, working_dir: str = None):
    """Send a voice command to Claude Code in a visible terminal window."""
    # Write to temp file to avoid shell escaping issues
    fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="wispr_cmd_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)

    # Open a visible console: pipe temp file into claude, then clean up
    tmp_win = tmp_path.replace("/", "\\")
    inner = f"type {tmp_win} | claude --print & del {tmp_win}"
    subprocess.Popen(
        ["cmd.exe", "/c", "start", "Claude Code", "cmd", "/k", inner],
        cwd=working_dir,
    )
    print(f"Sent to Claude Code: {text[:80]}")
