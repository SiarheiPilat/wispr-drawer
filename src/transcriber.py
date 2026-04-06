import openai
import os


def transcribe(audio_path: str, api_key: str) -> str:
    client = openai.OpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    # Clean up temp file if it's in temp directory
    import tempfile
    if audio_path.startswith(tempfile.gettempdir()):
        try:
            os.remove(audio_path)
        except OSError:
            pass
    return response.text
