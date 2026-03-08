from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.service import GameService, serialize_game_state

app = FastAPI(title="Beat HUD Backend",
              description="Web API and WebSocket interface for the rhythm game HUD state.")
game_service = GameService()


@app.post("/pause")
def pause_game() -> Dict[str, Any]:
    """Pause the beat engine and emit the current state."""

    game_service.pause()
    return {"status": "paused", "state": serialize_game_state(game_service.get_state())}


@app.post("/resume")
def resume_game() -> Dict[str, Any]:
    """Resume the beat engine loop."""

    game_service.resume()
    return {"status": "running", "state": serialize_game_state(game_service.get_state())}


@app.post("/reset")
def reset_game() -> Dict[str, Any]:
    """Reset the engine and replay the score chronicle."""

    game_service.reset()
    return {"status": "reset", "state": serialize_game_state(game_service.get_state())}


@app.get("/logs")
def read_logs() -> Dict[str, Any]:
    """Retrieve the server log history."""

    return {"logs": game_service.get_log_history()}


@app.get("/history")
def read_history() -> Dict[str, Any]:
    """Retrieve the captured GameState history."""

    return {"history": game_service.get_state_history()}


@app.websocket("/ws/state")
async def state_feed(websocket: WebSocket) -> None:
    """Stream the latest GameState to connected WebSocket clients."""

    await websocket.accept()
    try:
        while True:
            state = serialize_game_state(game_service.get_state())
            await websocket.send_json(state)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
