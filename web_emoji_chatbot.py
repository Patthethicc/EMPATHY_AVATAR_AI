from __future__ import annotations

import asyncio
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Set

import websockets
from dotenv import load_dotenv

from emotion_classifier import EmotionClassifier
from gemini_client import GeminiChatClient

HTTP_PORT = 8002
WS_PORT = 8766
WEB_ROOT = Path(__file__).parent / "web_avatar"


class ClientPool:
    def __init__(self) -> None:
        self.clients: Set[websockets.WebSocketServerProtocol] = set()

    async def register(self, websocket: websockets.WebSocketServerProtocol) -> None:
        self.clients.add(websocket)

    async def unregister(self, websocket: websockets.WebSocketServerProtocol) -> None:
        self.clients.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        if not self.clients:
            return
        message = json.dumps(payload)
        await asyncio.gather(
            *[self._safe_send(ws, message) for ws in list(self.clients)],
            return_exceptions=True,
        )

    @staticmethod
    async def _safe_send(ws: websockets.WebSocketServerProtocol, message: str) -> None:
        try:
            await ws.send(message)
        except Exception:
            pass


class QuietHandler(SimpleHTTPRequestHandler):
    noisy_paths = {
        "/.well-known/appspecific/com.chrome.devtools.json",
        "/libs/pixi.min.js.map",
    }

    def log_request(self, code="-", size="-"):  # type: ignore[override]
        line = getattr(self, "requestline", "")
        if str(code) == "304" or any(path in line for path in self.noisy_paths):
            return
        super().log_request(code, size)


def serve_http() -> None:
    handler = partial(QuietHandler, directory=str(WEB_ROOT))
    httpd = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), handler)
    print(f"[info] Hosting emoji web chat at http://localhost:{HTTP_PORT}/emoji.html")
    httpd.serve_forever()


async def handle_user_message(
    pool: ClientPool,
    gemini: GeminiChatClient,
    classifier: EmotionClassifier,
    text: str,
) -> None:
    user = text.strip()
    if not user:
        return

    reply = await asyncio.to_thread(gemini.reply, user)

    user_emotion, user_score = classifier.classify(user)
    bot_emotion, bot_score = classifier.classify(reply)

    if abs(user_score) >= 0.2:
        emotion = user_emotion
        score = user_score
    else:
        emotion = bot_emotion
        score = bot_score

    print(f"User: {user}")
    print(f"Bot [{emotion} | {score:+.2f}]: {reply}")
    await pool.broadcast({"emotion": emotion, "reply": reply, "user": user})


async def websocket_handler(
    pool: ClientPool,
    gemini: GeminiChatClient,
    classifier: EmotionClassifier,
    websocket: websockets.WebSocketServerProtocol,
) -> None:
    await pool.register(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message) if isinstance(message, str) else {}
            except json.JSONDecodeError:
                continue
            text = data.get("text") or data.get("message") or ""
            await handle_user_message(pool, gemini, classifier, text)
    finally:
        await pool.unregister(websocket)


async def main() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    gemini = GeminiChatClient(api_key=api_key)
    classifier = EmotionClassifier()
    pool = ClientPool()

    # Start HTTP server
    thread = threading.Thread(target=serve_http, daemon=True)
    thread.start()

    print(f"[info] WebSocket for emoji chat at ws://localhost:{WS_PORT}")
    print("Emoji Web Chat ready. Open the browser page at /emoji.html.\n")

    ws_server = await websockets.serve(
        lambda ws: websocket_handler(pool, gemini, classifier, ws),
        "0.0.0.0",
        WS_PORT,
        max_size=2**22,
    )

    try:
        await ws_server.wait_closed()
    finally:
        ws_server.close()
        await ws_server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
