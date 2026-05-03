import asyncio
import os
import tempfile
import threading

import pygame
import soundfile as sf
from config import EDGE_TTS_VOICE, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

pygame.mixer.init()

_kokoro_pipeline = None


def _get_kokoro():
    global _kokoro_pipeline
    if _kokoro_pipeline is None:
        print("[tts] Loading Kokoro model...")
        from kokoro_onnx import Kokoro
        _kokoro_pipeline = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        print("[tts] Kokoro ready.")
    return _kokoro_pipeline


def preload_tts():
    try:
        _get_kokoro()
    except Exception as e:
        print(f"[tts] Kokoro preload failed: {e}, will use edge-tts fallback")


def _play_audio(path: str):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(100)


def _speak_elevenlabs(text: str) -> bool:
    try:
        import requests
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.18,
                "similarity_boost": 0.70,
                "style": 0.65,
                "use_speaker_boost": True,
            },
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code != 200:
            print(f"[tts] ElevenLabs failed ({r.status_code}): {r.text[:100]}")
            return False
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
        with open(tmp_path, "wb") as f:
            f.write(r.content)
        _play_audio(tmp_path)
        os.unlink(tmp_path)
        return True
    except Exception as e:
        print(f"[tts] ElevenLabs error: {e}")
        return False


def _speak_kokoro(text: str) -> bool:
    try:
        import numpy as np
        kokoro = _get_kokoro()
        samples, sample_rate = kokoro.create(text, voice="af_heart", speed=1.0, lang="en-us")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
        sf.write(tmp_path, samples, sample_rate)
        _play_audio(tmp_path)
        os.unlink(tmp_path)
        return True
    except Exception as e:
        print(f"[tts] Kokoro failed: {e}")
        return False


def _speak_edge(text: str):
    import edge_tts

    async def _run():
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
        communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
        await communicate.save(tmp_path)
        _play_audio(tmp_path)
        os.unlink(tmp_path)

    asyncio.run(_run())


def _strip_emoji(text: str) -> str:
    import re
    return re.sub(r'[^\x00-\x7FÀ-ɏḀ-ỿ]+', '', text).strip()


def _enhance_prosody(text: str) -> str:
    import re
    # Ensure sentence-ending punctuation exists (helps ElevenLabs know where to breathe)
    text = re.sub(r'([a-zA-Z])(\s+[A-Z])', r'\1. \2', text)
    # Ellipsis after thinking fillers → natural pause
    text = re.sub(r'\b(Hmm|Hm|Well|Alright|Let me|Let\'s see|Okay|Oh)(,?\s)', r'\1... ', text, flags=re.IGNORECASE)
    # Dash for mid-sentence pause
    text = re.sub(r'\s+-\s+', ' — ', text)
    return text


def speak(text: str, blocking: bool = True):
    def _run():
        import ws_server
        clean = _strip_emoji(text)
        clean = _enhance_prosody(clean)
        print(f"[jarvis] {clean}")
        ws_server.broadcast("speaking")
        if not _speak_elevenlabs(clean):
            print("[tts] Falling back to Kokoro...")
            if not _speak_kokoro(clean):
                print("[tts] Falling back to edge-tts...")
                _speak_edge(clean)
        ws_server.broadcast("listening")

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()
