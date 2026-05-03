import asyncio
import json
import threading
import websockets

_clients = set()
_loop = None


async def _handler(ws):
    _clients.add(ws)
    try:
        await ws.wait_closed()
    finally:
        _clients.discard(ws)


async def _serve():
    async with websockets.serve(_handler, "localhost", 8765):
        await asyncio.Future()


def start():
    global _loop

    def _run():
        global _loop
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _loop.run_until_complete(_serve())

    threading.Thread(target=_run, daemon=True).start()


def _send_all(msg: str):
    if _loop is None:
        return
    async def _send():
        for ws in list(_clients):
            try:
                await ws.send(msg)
            except Exception:
                pass
    asyncio.run_coroutine_threadsafe(_send(), _loop)


def broadcast(state: str):
    _send_all(json.dumps({"type": "state", "state": state}))


def send_chat(role: str, text: str):
    _send_all(json.dumps({"type": "chat", "role": role, "text": text}))
