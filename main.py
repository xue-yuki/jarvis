import threading
import time
import os
import subprocess
import numpy as np
import sounddevice as sd

from config import (
    CLAP_THRESHOLD, CLAP_COOLDOWN, DOUBLE_CLAP_WINDOW,
    SAMPLE_RATE, USER_NAME, MIC_DEVICE
)
from launcher import launch_all
from tts import speak, preload_tts
from stt import record_until_silence, transcribe, preload_model
from agent import chat, reset_conversation
import ws_server
from ws_server import send_chat

_jarvis_active = False
_exit_event = threading.Event()
_clap_paused = threading.Event()
_window_ref = []


def _get_greeting() -> str:
    from datetime import datetime
    hour = datetime.now().hour
    if 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "afternoon"
    elif 17 <= hour < 21:
        period = "evening"
    else:
        period = "night"
    return f"Good {period}, {USER_NAME}. Your workspace is ready."


def _is_exit_command(text: str) -> bool:
    text = text.lower()
    return any(phrase in text for phrase in ["goodbye jarvis", "bye jarvis", "exit jarvis", "stop jarvis"])


def _morning_briefing() -> str:
    from datetime import datetime
    from tools import get_weather, get_notion_tasks
    hour = datetime.now().hour
    if not (5 <= hour < 12):
        return ""
    weather = get_weather("Purwokerto")
    tasks = get_notion_tasks()
    task_line = ""
    if "Notion is not configured" not in tasks and "Failed" not in tasks:
        task_line = f" {tasks}"
    return f"Morning briefing: {weather}{task_line} Have a productive day!"


def _standby_loop():
    global _jarvis_active
    speak(_get_greeting())
    briefing = _morning_briefing()
    if briefing:
        speak(briefing)
    speak("What are you working on today?")

    while not _exit_event.is_set():
        print("[stt] Listening for your voice...")
        audio = record_until_silence()
        if audio.size == 0:
            continue

        print("[stt] Voice detected, transcribing...")
        text = transcribe(audio)
        if not text:
            print("[stt] Could not transcribe, listening again...")
            continue

        print(f"[you] {text}")
        send_chat("user", text)

        if _is_exit_command(text):
            speak("Goodbye, Erlangga. See you next time.")
            reset_conversation()
            _jarvis_active = False
            _clap_paused.clear()
            ws_server.broadcast("idle")
            if _window_ref:
                _window_ref[0].minimize()
            return

        try:
            ws_server.broadcast("thinking")
            response = chat(text)
            send_chat("jarvis", response)
            speak(response)
        except RuntimeError:
            ws_server.broadcast("listening")
            speak("Sorry, I am having trouble connecting right now. Please try again in a moment.")


def _on_double_clap():
    global _jarvis_active
    if _jarvis_active:
        return
    _jarvis_active = True
    _clap_paused.set()
    print("[main] Double clap detected! Launching workspace...")
    if _window_ref:
        _window_ref[0].restore()
        time.sleep(0.3)
        os.system('wmctrl -r "JARVIS" -b add,above -a "JARVIS" 2>/dev/null')
    launch_all()
    threading.Thread(target=_standby_loop, daemon=True).start()


def _clap_detection_loop():
    chunk_duration = 0.02
    chunk_size = int(SAMPLE_RATE * chunk_duration)

    print("[main] JARVIS ready. Double clap to start.")
    ws_server.broadcast("idle")

    while not _exit_event.is_set():
        if _clap_paused.is_set():
            time.sleep(0.2)
            continue

        last_clap_time = 0.0
        first_clap_time = 0.0
        clap_count = 0

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", device=MIC_DEVICE) as stream:
                while not _exit_event.is_set() and not _clap_paused.is_set():
                    chunk, _ = stream.read(chunk_size)
                    amplitude = float(np.abs(chunk).max())
                    now = time.time()

                    if amplitude > CLAP_THRESHOLD:
                        if now - last_clap_time > CLAP_COOLDOWN:
                            last_clap_time = now
                            if clap_count == 0:
                                first_clap_time = now
                                clap_count = 1
                                print(f"[clap] First clap (peak={amplitude:.3f})")
                            elif clap_count == 1:
                                if now - first_clap_time <= DOUBLE_CLAP_WINDOW:
                                    clap_count = 0
                                    print("[clap] Double clap! Launching...")
                                    _on_double_clap()
                                else:
                                    first_clap_time = now
                                    clap_count = 1
                                    print(f"[clap] First clap (peak={amplitude:.3f})")
        except Exception as e:
            print(f"[clap] Stream error: {e}")
            time.sleep(0.5)


def main():
    import webview
    os.environ.setdefault('GDK_BACKEND', 'x11')

    ws_server.start()
    time.sleep(0.3)

    preload_tts()
    preload_model()

    threading.Thread(target=_clap_detection_loop, daemon=True).start()

    def _minimize_on_ready():
        time.sleep(1.5)
        if _window_ref:
            _window_ref[0].minimize()
            print("[main] Visual minimized. Double clap to activate.")

    threading.Thread(target=_minimize_on_ready, daemon=True).start()

    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "visualizer.html"))

    WIN_W, WIN_H = 800, 600
    WIN_W, WIN_H = 800, 600
    margin = 20
    try:
        r = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=2)
        for line in r.stdout.split('\n'):
            if 'dimensions' in line:
                res = line.split()[1].split('x')
                sw, sh = int(res[0]), int(res[1])
                break
        else:
            sw, sh = 1920, 1080
    except Exception:
        sw, sh = 1920, 1080

    win_x = sw - WIN_W - margin
    win_y = sh - WIN_H - margin - 40

    class Api:
        def __init__(self):
            self._win_x = win_x
            self._win_y = win_y
            self._mx = 0
            self._my = 0

        def start_drag(self, screen_x, screen_y):
            self._mx = int(screen_x)
            self._my = int(screen_y)

        def drag_to(self, screen_x, screen_y):
            dx = int(screen_x) - self._mx
            dy = int(screen_y) - self._my
            self._mx = int(screen_x)
            self._my = int(screen_y)
            self._win_x += dx
            self._win_y += dy
            _window_ref[0].move(self._win_x, self._win_y)

        def close(self):
            _window_ref[0].destroy()

        def minimize(self):
            _window_ref[0].minimize()

    api = Api()
    window = webview.create_window(
        "JARVIS",
        f"file://{html_path}",
        width=WIN_W,
        height=WIN_H,
        x=win_x,
        y=win_y,
        resizable=True,
        frameless=True,
        on_top=True,
        background_color="#000000",
        js_api=api,
    )
    _window_ref.append(window)

    def _force_on_top():
        time.sleep(2)
        os.system('wmctrl -r "JARVIS" -b add,above 2>/dev/null')

    threading.Thread(target=_force_on_top, daemon=True).start()

    webview.start()
    _exit_event.set()


if __name__ == "__main__":
    main()
