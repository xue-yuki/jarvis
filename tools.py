import os
import subprocess
import time
import json
import requests
from datetime import datetime

_mpv_process = None


def open_app(app_name: str) -> str:
    try:
        subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Opened {app_name}."
    except FileNotFoundError:
        return f"App '{app_name}' not found."


def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Command executed."
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error: {e}"


def get_time() -> str:
    now = datetime.now()
    return now.strftime("It's %A, %B %d, %Y at %I:%M %p.")


def get_weather(location: str = "Purwokerto") -> str:
    try:
        res = requests.get(
            f"https://wttr.in/{location}?format=j1",
            timeout=8,
            headers={"User-Agent": "curl/7.0"}
        )
        data = res.json()
        current = data["current_condition"][0]
        today = data["weather"][0]

        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        max_c = today["maxtempC"]
        min_c = today["mintempC"]

        return (
            f"Weather in {location}: {desc}, {temp_c} degrees Celsius, "
            f"feels like {feels_like}. "
            f"Humidity {humidity}%. "
            f"Today's high is {max_c} and low is {min_c}."
        )
    except Exception as e:
        return f"Could not get weather for {location}: {e}"


def play_music(query: str) -> str:
    global _mpv_process
    if _mpv_process and _mpv_process.poll() is None:
        _mpv_process.terminate()
    search = f"ytdl://ytsearch1:{query}"
    _mpv_process = subprocess.Popen(
        ["mpv", "--no-video", "--ytdl-format=bestaudio", search],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return f"Playing: {query}"


def stop_music() -> str:
    global _mpv_process
    if _mpv_process and _mpv_process.poll() is None:
        _mpv_process.terminate()
        _mpv_process = None
        return "Music stopped."
    return "No music is playing."


PROJECTS_DIR = os.path.expanduser("~/Projects")


CLAUDE_BIN = "/home/elamgah/.npm-global/bin/claude"

def delegate_to_claude(task: str, project_name: str = "") -> str:
    import re
    if project_name:
        safe_name = re.sub(r'[^\w\-]', '-', project_name).strip('-')
    else:
        words = re.sub(r'[^\w\s]', '', task.lower()).split()
        safe_name = '-'.join(words[:4]) or "project"

    project_path = os.path.join(PROJECTS_DIR, safe_name)
    os.makedirs(project_path, exist_ok=True)

    # Open VSCode with the project folder
    subprocess.Popen(['code', project_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Open ptyxis terminal in project dir, launch claude with the task as initial prompt
    escaped = task.replace("'", "'\\''")
    subprocess.Popen(
        ['ptyxis', '--', 'bash', '-c',
         f"cd '{project_path}' && '{CLAUDE_BIN}' '{escaped}'; exec bash"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    return f"Opened VSCode and Claude Code terminal in project '{safe_name}'. Task: {task}"


def create_project(project_name: str, template: str = "html") -> str:
    import re
    safe_name = re.sub(r'[^\w\-]', '-', project_name).strip('-')
    project_path = os.path.join(PROJECTS_DIR, safe_name)
    os.makedirs(project_path, exist_ok=True)

    templates = {
        "html": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>Hello, {name}!</h1>
  <script src="script.js"></script>
</body>
</html>""".format(name=project_name),
            "style.css": "* { margin: 0; padding: 0; box-sizing: border-box; }\nbody { font-family: sans-serif; background: #111; color: #eee; display: flex; justify-content: center; align-items: center; height: 100vh; }\n",
            "script.js": "// Your JavaScript here\nconsole.log('Project started!');\n",
        },
        "html-game": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{name}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="gameCanvas" width="800" height="600"></canvas>
  <script src="game.js"></script>
</body>
</html>""".format(name=project_name),
            "style.css": "* { margin: 0; padding: 0; box-sizing: border-box; }\nbody { background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }\ncanvas { border: 2px solid #333; }\n",
            "game.js": """const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const player = { x: 400, y: 300, size: 20, speed: 4, color: '#00ff88' };
const keys = {};

document.addEventListener('keydown', e => keys[e.key] = true);
document.addEventListener('keyup', e => keys[e.key] = false);

function update() {
  if (keys['ArrowLeft'] || keys['a']) player.x -= player.speed;
  if (keys['ArrowRight'] || keys['d']) player.x += player.speed;
  if (keys['ArrowUp'] || keys['w']) player.y -= player.speed;
  if (keys['ArrowDown'] || keys['s']) player.y += player.speed;
  player.x = Math.max(player.size, Math.min(canvas.width - player.size, player.x));
  player.y = Math.max(player.size, Math.min(canvas.height - player.size, player.y));
}

function draw() {
  ctx.fillStyle = '#111';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = player.color;
  ctx.beginPath();
  ctx.arc(player.x, player.y, player.size, 0, Math.PI * 2);
  ctx.fill();
}

function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}
loop();
""",
        },
        "python": {
            "main.py": f'def main():\n    print("Hello from {project_name}!")\n\nif __name__ == "__main__":\n    main()\n',
            "requirements.txt": "# Add your dependencies here\n",
        },
        "node": {
            "index.js": f'console.log("Hello from {project_name}!");\n',
            "package.json": '{{\n  "name": "{name}",\n  "version": "1.0.0",\n  "main": "index.js"\n}}\n'.format(name=safe_name),
        },
    }

    files = templates.get(template, templates["html"])
    created = []
    for filename, content in files.items():
        filepath = os.path.join(project_path, filename)
        with open(filepath, "w") as f:
            f.write(content)
        created.append(filename)

    subprocess.Popen(["code", project_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Project '{project_name}' created at {project_path} with files: {', '.join(created)}. Opened in VSCode."


def write_file(file_path: str, content: str) -> str:
    if not os.path.isabs(file_path):
        file_path = os.path.join(PROJECTS_DIR, file_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)
    return f"File written: {file_path}"


def get_notion_tasks() -> str:
    from config import NOTION_TOKEN, NOTION_DATABASE_ID
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return "Notion is not configured yet."
    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        def _query_db(db_id):
            payload = {
                "filter": {"property": "Selesai", "checkbox": {"equals": False}},
                "sorts": [{"property": "Deadline", "direction": "ascending"}],
                "page_size": 15,
            }
            return requests.post(
                f"https://api.notion.com/v1/databases/{db_id}/query",
                headers=headers, json=payload, timeout=10
            )

        r = _query_db(NOTION_DATABASE_ID)

        # If page ID given instead of database ID, find the database inside it
        if r.status_code == 400:
            children = requests.get(
                f"https://api.notion.com/v1/blocks/{NOTION_DATABASE_ID}/children",
                headers=headers, timeout=10
            ).json()
            db_id = next(
                (b["id"] for b in children.get("results", []) if b["type"] == "child_database"),
                None
            )
            if not db_id:
                return "Could not find database in the Notion page."
            r = _query_db(db_id.replace("-", ""))

        if r.status_code != 200:
            return f"Notion error {r.status_code}: {r.text[:120]}"

        results = r.json().get("results", [])
        if not results:
            return "No pending tasks in your Notion."

        tasks = []
        for page in results:
            props = page.get("properties", {})
            title_prop = props.get("Nama Tugas", {}).get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_prop).strip()

            subject = ""
            mp = props.get("Mata Pelajaran", {})
            if mp.get("select") and mp["select"].get("name"):
                subject = f" [{mp['select']['name']}]"

            deadline = ""
            dl = props.get("Deadline", {}).get("date")
            if dl and dl.get("start"):
                deadline = f" — due {dl['start']}"

            if title:
                tasks.append(f"{title}{subject}{deadline}")

        if not tasks:
            return "All tasks are done, nothing pending."

        count = len(tasks)
        task_list = "; ".join(tasks)
        return f"You have {count} pending task{'s' if count > 1 else ''}: {task_list}"
    except Exception as e:
        return f"Failed to fetch Notion tasks: {e}"


def web_search(query: str) -> str:
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
        if not results:
            return "No results found."
        summary = []
        for r in results:
            summary.append(f"{r['title']}: {r['body'][:180]}")
        return "\n\n".join(summary)
    except Exception as e:
        return f"Search failed: {e}"


def set_timer(seconds: int, label: str = "Timer") -> str:
    import threading
    def _ring():
        time.sleep(seconds)
        send_notification(label, f"{label} is done!")
        subprocess.Popen(
            ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    threading.Thread(target=_ring, daemon=True).start()
    mins = seconds // 60
    secs = seconds % 60
    if mins and secs:
        duration = f"{mins} minute{'s' if mins>1 else ''} and {secs} seconds"
    elif mins:
        duration = f"{mins} minute{'s' if mins>1 else ''}"
    else:
        duration = f"{secs} seconds"
    return f"Timer set for {duration}. I'll let you know when it's done."


def send_notification(title: str, message: str) -> str:
    try:
        subprocess.Popen(["notify-send", title, message])
        return f"Notification sent: {title}"
    except FileNotFoundError:
        return "notify-send not available."


TOOL_MAP = {
    "open_app": lambda args: open_app(**args),
    "run_command": lambda args: run_command(**args),
    "get_time": lambda args: get_time(),
    "send_notification": lambda args: send_notification(**args),
    "play_music": lambda args: play_music(**args),
    "stop_music": lambda args: stop_music(),
    "get_weather": lambda args: get_weather(**args),
    "create_project": lambda args: create_project(**args),
    "write_file": lambda args: write_file(**args),
    "delegate_to_claude": lambda args: delegate_to_claude(**args),
    "get_notion_tasks": lambda args: get_notion_tasks(),
    "web_search": lambda args: web_search(**args),
    "set_timer": lambda args: set_timer(**args),
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application on Linux",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "CLI command of the app, e.g. firefox, code, nautilus"}
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a bash command in the terminal",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time and date",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Send a desktop notification",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["title", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Search and play music from YouTube via mpv. Use for any play music request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Song name, artist, or search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_music",
            "description": "Stop the currently playing music.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_notion_tasks",
            "description": "Get today's tasks and to-do list from Notion. Use when user asks about their tasks, schedule, or what they need to do today.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information, news, facts, or anything not in training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_timer",
            "description": "Set a timer that rings with a sound and notification when done. Use for study sessions, breaks, reminders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "integer", "description": "Duration in seconds"},
                    "label": {"type": "string", "description": "Timer label, e.g. 'Pomodoro', 'Break', 'Build timer'"}
                },
                "required": ["seconds"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_claude",
            "description": "Delegate a coding task to Claude Code inside VSCode. Creates a project folder, opens VSCode, and launches Claude Code in the integrated terminal with the task prompt. Use this for any coding/building request where the user wants code written.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The full coding task description to pass to Claude Code, e.g. 'build a portfolio website with HTML CSS JS, dark theme, with sections for about, projects, and contact'"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Optional project folder name, e.g. 'portfolio-site'. If empty, auto-generated from task."
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Create a new coding project with scaffold files in ~/Projects/. Always use this when user wants to start a new project. Opens VSCode automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project, e.g. 'my-game', 'school-project'"
                    },
                    "template": {
                        "type": "string",
                        "enum": ["html", "html-game", "python", "node"],
                        "description": "Template: 'html' for basic web, 'html-game' for canvas game, 'python' for Python app, 'node' for Node.js"
                    }
                },
                "required": ["project_name", "template"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file inside a project. Use this to add new files or update existing code in a project. Path relative to ~/Projects/ or absolute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path like 'my-game/game.js' or absolute path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write"
                    }
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather and today's forecast for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g. Purwokerto, Bekasi, Jakarta. Defaults to Purwokerto."
                    }
                },
                "required": [],
            },
        },
    },
]
