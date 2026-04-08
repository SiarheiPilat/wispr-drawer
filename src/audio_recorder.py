import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
from datetime import datetime


class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, device=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device  # None = system default
        self._frames = []
        self._recording = False
        self._stream = None
        self._lock = threading.Lock()

    @staticmethod
    def list_input_devices():
        """Return list of (index, name) for available input devices."""
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                result.append((i, d['name']))
        return result

    def start(self):
        with self._lock:
            self._frames = []
            self._recording = True
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata, frames, time_info, status):
        if self._recording:
            self._frames.append(indata.copy())

    def stop(self) -> np.ndarray | None:
        with self._lock:
            self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return None
        return np.concatenate(self._frames, axis=0)

    def save_wav(self, audio_data: np.ndarray, project_dir: str) -> str:
        recordings_dir = os.path.join(project_dir, "recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(recordings_dir, f"{timestamp}.wav")
        sf.write(filepath, audio_data, self.sample_rate)
        return filepath

    @staticmethod
    def is_silent(audio_data: np.ndarray, threshold=0.01) -> bool:
        """Return True if audio RMS is below threshold (i.e. just silence/noise)."""
        rms = np.sqrt(np.mean(audio_data ** 2))
        return rms < threshold

    def save_temp_wav(self, audio_data: np.ndarray) -> str:
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        sf.write(path, audio_data, self.sample_rate)
        return path
