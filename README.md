# JARVIS — Voice AI Assistant for Linux

A fully local, voice-activated AI assistant for Linux. Trigger with a double clap, speak naturally, and let JARVIS handle the rest — from answering questions and playing music to scaffolding projects and delegating tasks to Claude Code.

![Demo](https://img.shields.io/badge/platform-Linux-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-green) ![License](https://img.shields.io/badge/license-MIT-orange)

---

## Features

- **Double clap activation** — no button, no keyboard shortcut
- **Voice STT** — Whisper medium model (fast, accurate, bilingual EN/ID)
- **AI Agent** — OpenRouter (Kimi/Qwen) with tool use
- **Natural TTS** — ElevenLabs primary, Kokoro ONNX fallback, edge-tts last resort
- **Neural network visualizer** — Three.js animated brain reacts to JARVIS state
- **Music playback** — search and stream from YouTube via yt-dlp + mpv
- **Weather info** — real-time via wttr.in (no API key needed)
- **Web search** — DuckDuckGo search
- **Notion tasks** — reads your pending tasks from a Notion database
- **Timer / Pomodoro** — set timers by voice with sound alert
- **Project scaffolding** — creates project folders and delegates coding to Claude Code
- **Morning briefing** — weather + Notion tasks on first activation each morning
- **Frameless native window** — pywebview, always-on-top, draggable, bottom-right corner

---

## Requirements

### System dependencies

```bash
# Fedora/RHEL
sudo dnf install mpv yt-dlp xdotool wmctrl libportaudio notify-send

# Ubuntu/Debian
sudo apt install mpv yt-dlp xdotool wmctrl portaudio19-dev libnotify-bin
```

### Python 3.11+

```bash
pip install -r requirements.txt
```

### Kokoro TTS model files

Download and place in the project root:
- `kokoro-v1.0.onnx`
- `voices-v1.0.bin`

From: https://github.com/thewh1teagle/kokoro-onnx/releases

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/jarvis.git
cd jarvis
pip install -r requirements.txt
```

### 2. Configure `config.py`

Copy and edit the config:

```python
USER_NAME = "YourName"

# OpenRouter — get key at openrouter.ai
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENROUTER_MODEL = "qwen/qwen-turbo"  # or moonshotai/kimi-k2.6

# ElevenLabs TTS — get key at elevenlabs.io (free tier works)
ELEVENLABS_API_KEY = "sk_..."
ELEVENLABS_VOICE_ID = "cgSgspJ2msm6clMCkdW9"  # Jessica (or any voice ID)

# Notion (optional) — for reading your tasks
NOTION_TOKEN = "ntn_..."
NOTION_DATABASE_ID = "your-database-id"

# Clap detection sensitivity (lower = more sensitive)
CLAP_THRESHOLD = 0.06

# Apps to launch on double clap
LAUNCH_APPS = [
    ["code"],
    ["firefox", "https://open.spotify.com"],
    # add more as needed
]
```

### 3. Get your API keys

| Service | Where to get | Free tier |
|---|---|---|
| OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | Yes (limited) |
| ElevenLabs | [elevenlabs.io](https://elevenlabs.io) | 10k chars/month |
| Notion | [notion.so/my-integrations](https://notion.so/my-integrations) | Yes |

### 4. Notion setup (optional)

1. Go to [notion.so/my-integrations](https://notion.so/my-integrations) → New integration → copy token
2. Open your tasks database in Notion → `...` → Connections → add your integration
3. Copy the database ID from the URL: `notion.so/Your-Page-{DATABASE_ID}`
4. Paste token and database ID into `config.py`

> Your database needs these properties: `Nama Tugas` (title), `Selesai` (checkbox), `Deadline` (date)

### 5. Calibrate your mic (optional)

```bash
python calibrate.py
```

Clap near your mic and adjust `CLAP_THRESHOLD` in `config.py` until detection is reliable.

---

## Run

```bash
python main.py
```

The window appears in the bottom-right corner and minimizes after 1.5 seconds. **Double clap** to activate.

---

## Usage

| Say... | JARVIS does... |
|---|---|
| *"Play lo-fi music"* | Streams from YouTube via mpv |
| *"What's the weather?"* | Real-time weather for your city |
| *"Search for latest AI news"* | DuckDuckGo web search |
| *"What are my tasks today?"* | Reads pending tasks from Notion |
| *"Set a timer for 25 minutes"* | Pomodoro timer with sound alert |
| *"Build a portfolio website"* | Creates project folder + opens Claude Code |
| *"Goodbye Jarvis"* | Deactivates and minimizes |

---

## Project Structure

```
jarvis/
├── main.py           # Entry point, clap detection, pywebview window
├── agent.py          # OpenRouter AI agent with tool loop
├── tools.py          # All tool functions (music, weather, search, etc.)
├── stt.py            # Speech-to-text (faster-whisper)
├── tts.py            # Text-to-speech (ElevenLabs → Kokoro → edge-tts)
├── ws_server.py      # WebSocket server for visualizer state sync
├── launcher.py       # App launcher on activation
├── calibrate.py      # Mic calibration utility
├── visualizer.html   # Three.js neural network visualizer
├── config.py         # All configuration
└── requirements.txt
```

---

## TTS Fallback Chain

1. **ElevenLabs** (primary — most natural, free tier available)
2. **Kokoro ONNX** (local fallback — no internet needed)
3. **edge-tts** (Microsoft Azure TTS — always available)

---

## Troubleshooting

**Window not draggable / position wrong**
- Make sure you're running on X11 or XWayland. The app sets `GDK_BACKEND=x11` automatically.

**Clap not detected**
- Run `python calibrate.py` and adjust `CLAP_THRESHOLD` in `config.py`
- Default is `0.06` — lower if not sensitive enough, raise if false triggers

**Wrong microphone**
- Check device list: `python -c "import sounddevice as sd; print(sd.query_devices())"`
- Set `MIC_DEVICE = <device_index>` in `config.py`

**Whisper transcription inaccurate**
- Try switching `WHISPER_MODEL_SIZE` to `"large-v3"` for better accuracy (slower)
- Make sure your mic sample rate is 16kHz or higher

**ElevenLabs 402 error**
- Free tier credits exhausted — get a new API key or switch to Kokoro (set `ELEVENLABS_API_KEY = ""`)

**OpenRouter rate limit**
- The agent automatically falls back through model chain: kimi-k2 → qwen-turbo
- Top up credits at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits)

---

## License

MIT — do whatever you want with it.

---

Made with way too much fun by [Erlangga](https://github.com/yourusername)
