import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from config import WHISPER_MODEL_SIZE, SAMPLE_RATE, VAD_THRESHOLD, VAD_SILENCE_DURATION, VAD_MAX_DURATION, MIC_DEVICE

_model = None


def _get_model():
    global _model
    if _model is None:
        print("[stt] Loading Whisper model...")
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        print("[stt] Whisper model ready.")
    return _model


def preload_model():
    _get_model()


def record_until_silence() -> np.ndarray:
    import ws_server
    ws_server.broadcast("listening")
    print("[stt] Listening...")
    chunk_size = int(SAMPLE_RATE * 0.1)  # 100ms chunks
    max_chunks = int(VAD_MAX_DURATION / 0.1)
    silence_chunks_needed = int(VAD_SILENCE_DURATION / 0.1)

    recorded = []
    silence_count = 0
    speaking = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", device=MIC_DEVICE) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            amplitude = np.abs(chunk).mean()
            recorded.append(chunk.copy())

            if amplitude > VAD_THRESHOLD:
                speaking = True
                silence_count = 0
            elif speaking:
                silence_count += 1
                if silence_count >= silence_chunks_needed:
                    break

    if not speaking:
        return np.array([], dtype=np.float32)

    audio = np.concatenate(recorded, axis=0).flatten()
    return audio


ALLOWED_LANGUAGES = {"en", "id"}

def transcribe(audio: np.ndarray) -> str:
    if audio.size == 0:
        return ""
    model = _get_model()
    segments, info = model.transcribe(
        audio,
        beam_size=3,
        vad_filter=True,
        language=None,
        condition_on_previous_text=False,
        initial_prompt="Jarvis, play music, open app, create project, Claude Code, weather, what time, stop music, goodbye Jarvis.",
    )
    lang = info.language
    print(f"[stt] Detected language: {lang} ({info.language_probability:.2f})")

    if lang not in ALLOWED_LANGUAGES:
        print(f"[stt] Language '{lang}' not allowed, ignoring.")
        return ""

    text = " ".join(seg.text.strip() for seg in segments)
    text = _normalize(text)
    return text.strip()


_CORRECTIONS = [
    (r'\bcloud\s*code\b', 'Claude Code'),
    (r'\bcloud\s*co\b', 'Claude Code'),
    (r'\bkloude?\s*code\b', 'Claude Code'),
    (r'\bclod\s*code\b', 'Claude Code'),
]

def _normalize(text: str) -> str:
    import re
    for pattern, replacement in _CORRECTIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text
