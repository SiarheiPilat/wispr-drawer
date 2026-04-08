import threading
import winsound
import numpy as np
import sounddevice as sd
import openwakeword

# openwakeword expects 80ms chunks at 16kHz = 1280 samples
_CHUNK_SIZE = 1280

BUILTIN_MODELS = ["alexa", "hey_mycroft", "hey_jarvis", "hey_rhasspy", "timer", "weather"]


class WakeWordListener:
    """Always-on wake word detector with voice command capture."""

    LISTENING = "listening"
    CAPTURING = "capturing"
    PAUSED = "paused"

    def __init__(self, model_name, sensitivity, mic_device, on_command,
                 sample_rate=16000, silence_duration=1.5, max_duration=15):
        self.model_name = model_name
        self.sensitivity = sensitivity
        self.mic_device = mic_device
        self.on_command = on_command
        self.sample_rate = sample_rate
        self.silence_duration = silence_duration
        self.max_duration = max_duration

        self._state = self.PAUSED
        self._stream = None
        self._lock = threading.Lock()

        # Capture state
        self._capture_frames = []
        self._silence_frames = 0
        self._capture_frames_total = 0

        # Frames needed for silence/max duration
        self._silence_frames_needed = int(silence_duration * sample_rate / _CHUNK_SIZE)
        self._max_frames = int(max_duration * sample_rate / _CHUNK_SIZE)

        # Load model (onnx only, no tflite needed)
        self._oww_model = openwakeword.Model(
            wakeword_models=[model_name] if model_name in BUILTIN_MODELS else [model_name],
            inference_framework="onnx",
        )
        # Resolve the key openwakeword uses for this model
        self._model_key = list(self._oww_model.models.keys())[0]

    def start(self):
        with self._lock:
            if self._state != self.PAUSED:
                return
            self._state = self.LISTENING
        self._open_stream()
        print(f"Wake word listener started (model: {self.model_name})")

    def stop(self):
        self._close_stream()
        with self._lock:
            self._state = self.PAUSED
        print("Wake word listener stopped")

    def pause(self):
        self._close_stream()
        with self._lock:
            self._state = self.PAUSED

    def resume(self):
        with self._lock:
            if self._state != self.PAUSED:
                return
            self._state = self.LISTENING
            self._oww_model.reset()
        self._open_stream()

    def _open_stream(self):
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=_CHUNK_SIZE,
            device=self.mic_device,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _close_stream(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        chunk = indata[:, 0]  # mono

        with self._lock:
            state = self._state

        if state == self.LISTENING:
            self._handle_listening(chunk)
        elif state == self.CAPTURING:
            self._handle_capturing(chunk)

    def _handle_listening(self, chunk):
        prediction = self._oww_model.predict(chunk)
        score = prediction.get(self._model_key, 0)

        if score >= self.sensitivity:
            with self._lock:
                self._state = self.CAPTURING
                self._capture_frames = []
                self._silence_frames = 0
                self._capture_frames_total = 0
            self._oww_model.reset()
            # Beep on a thread so we don't block the audio callback
            threading.Thread(target=lambda: winsound.Beep(800, 200), daemon=True).start()
            print("Wake word detected! Listening for command...")

    def _handle_capturing(self, chunk):
        # Convert int16 to float32 for storage (matching AudioRecorder output)
        float_chunk = chunk.astype(np.float32) / 32768.0
        self._capture_frames.append(float_chunk)
        self._capture_frames_total += 1

        # RMS silence detection
        rms = np.sqrt(np.mean(float_chunk ** 2))
        if rms < 0.01:
            self._silence_frames += 1
        else:
            self._silence_frames = 0

        # Check end conditions
        done = (self._silence_frames >= self._silence_frames_needed
                or self._capture_frames_total >= self._max_frames)

        if done:
            # Trim trailing silence frames
            trim = min(self._silence_frames, len(self._capture_frames))
            if trim > 0:
                frames = self._capture_frames[:-trim]
            else:
                frames = self._capture_frames

            with self._lock:
                self._state = self.LISTENING
                self._capture_frames = []

            if frames:
                audio_data = np.concatenate(frames).reshape(-1, 1)
                threading.Thread(
                    target=self.on_command, args=(audio_data,), daemon=True
                ).start()
            else:
                print("No command audio captured.")
