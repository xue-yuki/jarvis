import subprocess
import threading
from config import LAUNCH_APPS


def _launch(cmd):
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"[launcher] App not found: {cmd[0]}")


def launch_all():
    threads = [threading.Thread(target=_launch, args=(cmd,)) for cmd in LAUNCH_APPS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("[launcher] All apps launched.")
