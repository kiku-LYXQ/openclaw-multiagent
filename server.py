from __future__ import annotations

import asyncio
import dataclasses
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Set

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from engine.beat_engine import BeatEngine, BeatSignal
from engine.scheduler import PianoAgent, Scheduler, ViolinAgent


PATTERN = [
    {"beat": 1, "agent": "Piano", "action": "hit"},
    {"beat": 2, "agent": "Violin", "action": "hit"},
    {"beat": 3, "agent": "Piano", "action": "hit"},
    {"beat": 4, "agent": "Violin", "action": "hit"},
    {"beat": 5, "agent": "Piano", "action": "hold"},
    {"beat": 6, "agent": "Violin", "action": "hit"},
    {"beat": 7, "agent": "Piano", "action": "hit"},
    {"beat": 8, "agent": "Violin", "action": "hit"},
    {"beat": 9, "agent": "Piano", "action": "hit"},
    {"beat": 10, "agent": "Violin", "action": "hit"},
    {"beat": 11, "agent": "Piano", "action": "hit"},
    {"beat": 12, "agent": "Violin", "action": "hit"},
    {"beat": 13, "agent": "Piano", "action": "hit"},
    {"beat": 14, "agent": "Violin", "action": "hit"},
    {"beat": 15, "agent": "Piano", "action": "hit"},
    {"beat": 16, "agent": "Violin", "action": "hit"},
]


class GameServer:
    """Manages the beat engine scheduler lifecycle and broadcasts GameState updates."""

    def __init__(self, bpm: float = 128.0, max_history: int = 64, max_logs: int = 64) -> None:
        self.bpm = bpm
        self.pattern = PATTERN
        beats = [entry.get("beat", 0) for entry in self.pattern]
        self.max_beats = max(beats) + 8 if beats else 64
        self.history: Deque[Dict[str, Any]] = deque(maxlen=max_history)
        self.logs: Deque[Dict[str, Any]] = deque(maxlen=max_logs)
        self._lock = threading.Lock()
        self._connection_lock: Optional[asyncio.Lock] = None
        self._connections: Set[WebSocket] = set()
        self.state_queue: Optional[asyncio.Queue] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._broadcast_task: Optional[asyncio.Task] = None
        self.engine: Optional[BeatEngine] = None
        self.scheduler: Optional[Scheduler] = None
        self.latest_record: Optional[Dict[str, Any]] = None
        self._started = False

    def _log(self, message: str, level: str = "info", details: Optional[Dict[str, Any]] = None) -> None:
        entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "details": details or {},
        }
        with self._lock:
            self.logs.appendleft(entry)

    def _create_agents(self) -> List[Any]:
        return [PianoAgent(), ViolinAgent()]

    def _initialize_engine(self) -> None:
        self.engine = BeatEngine()
        self.scheduler = Scheduler(agents=self._create_agents(), pattern=self.pattern)
        self.engine.register_listener(self.scheduler.handle_beat)
        self.engine.register_listener(self._on_beat)
        self.engine.start(bpm=self.bpm, max_beats=self.max_beats)
        self._log("Beat engine initialized", details={"bpm": self.bpm, "max_beats": self.max_beats})

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._started:
            return
        self.loop = loop
        self.state_queue = asyncio.Queue()
        self._connection_lock = asyncio.Lock()
        self._broadcast_task = loop.create_task(self._broadcast_loop())
        with self._lock:
            self.history.clear()
            self.latest_record = None
        self._initialize_engine()
        self._log("Game server started")
        self._started = True

    async def shutdown(self) -> None:
        if not self._started:
            return
        if self.engine:
            self.engine.stop()
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
            self._broadcast_task = None
        self.state_queue = None
        self.loop = None
        self._connection_lock = None
        self._connections.clear()
        self._started = False
        self._log("Game server shutdown")

    def pause(self) -> None:
        if self.engine:
            self.engine.pause()
            self._log("Game paused")

    def resume(self) -> None:
        if self.engine:
            self.engine.resume()
            self._log("Game resumed")

    def reset(self) -> None:
        self._log("Game reset requested")
        if self.engine:
            self.engine.stop()
        self._clear_queue()
        with self._lock:
            self.history.clear()
            self.latest_record = None
        self._initialize_engine()
        self._log("Game reset complete")

    def _clear_queue(self) -> None:
        if not self.state_queue:
            return
        while not self.state_queue.empty():
            try:
                self.state_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def _on_beat(self, signal: "BeatSignal") -> None:
        if not self.scheduler or not self.loop or not self.state_queue:
            return
        state = self.scheduler.build_state(bpm=self.bpm)
        payload = dataclasses.asdict(state)
        record = {"beat": signal.beat_index, "timestamp": signal.timestamp, "state": payload}
        with self._lock:
            self.history.appendleft(record)
            self.latest_record = record
        self.loop.call_soon_threadsafe(self.state_queue.put_nowait, record)

    async def _broadcast_loop(self) -> None:
        if not self.state_queue:
            return
        try:
            while True:
                record = await self.state_queue.get()
                await self._dispatch(record)
        except asyncio.CancelledError:
            pass

    async def _dispatch(self, record: Dict[str, Any]) -> None:
        if not self._connection_lock:
            return
        async with self._connection_lock:
            connections = list(self._connections)
        for websocket in connections:
            try:
                await websocket.send_json(record)
            except Exception:  # pragma: no cover - best effort send
                await self._remove_connection(websocket)

    async def _remove_connection(self, websocket: WebSocket) -> None:
        if self._connection_lock:
            async with self._connection_lock:
                self._connections.discard(websocket)
        try:
            await websocket.close()
        except Exception:  # pragma: no cover
            pass

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        if not self._connection_lock:
            raise RuntimeError("Game server not ready for WebSocket connections")
        async with self._connection_lock:
            self._connections.add(websocket)
        if self.latest_record:
            await websocket.send_json(self.latest_record)

    async def disconnect(self, websocket: WebSocket) -> None:
        await self._remove_connection(websocket)

    def get_logs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.logs)

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.history)


_game_server = GameServer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.game_server = _game_server
    _game_server.start(asyncio.get_running_loop())
    try:
        yield
    finally:
        await _game_server.shutdown()


app = FastAPI(
    title="Beat HUD Server",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_game_server() -> GameServer:
    server = getattr(app.state, "game_server", None)
    if not server:
        raise RuntimeError("Game server not initialized")
    return server


@app.post("/pause")
async def pause_game(server: GameServer = Depends(get_game_server)) -> JSONResponse:
    server.pause()
    return JSONResponse({"status": "paused"})


@app.post("/resume")
async def resume_game(server: GameServer = Depends(get_game_server)) -> JSONResponse:
    server.resume()
    return JSONResponse({"status": "running"})


@app.post("/reset")
async def reset_game(server: GameServer = Depends(get_game_server)) -> JSONResponse:
    server.reset()
    return JSONResponse({"status": "reset"})


@app.get("/logs")
async def read_logs(server: GameServer = Depends(get_game_server)) -> JSONResponse:
    return JSONResponse({"logs": server.get_logs()})


@app.get("/history")
async def read_history(server: GameServer = Depends(get_game_server)) -> JSONResponse:
    return JSONResponse({"history": server.get_history()})


@app.websocket("/ws/state")
@app.websocket("/ws/game-state")
async def websocket_endpoint(websocket: WebSocket, server: GameServer = Depends(get_game_server)) -> None:
    await server.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await server.disconnect(websocket)


def main() -> None:
    import uvicorn

    uvicorn.run("new_app.server:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
