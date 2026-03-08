from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Iterable, List, Optional

from engine.beat_engine import BeatEngine
from engine.scheduler import PianoAgent, Scheduler, ViolinAgent
from models import GameState

DEFAULT_PATTERN = [
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


def serialize_game_state(state: GameState) -> Dict[str, Any]:
    """Convert the GameState dataclass to a JSON-friendly dictionary."""

    return asdict(state)


class GameService:
    def __init__(self, bpm: float = 128.0, pattern: Optional[Iterable[Dict[str, Any]]] = None) -> None:
        self.bpm = bpm
        self.pattern = list(pattern) if pattern else list(DEFAULT_PATTERN)
        self.log_history: Deque[Dict[str, str]] = deque(maxlen=256)
        self.state_history: Deque[Dict[str, Any]] = deque(maxlen=64)
        self._history_lock = threading.Lock()
        self._log_lock = threading.Lock()
        self._engine_lock = threading.Lock()
        self._collector_running = True
        self._reset_engine()
        self._collector_thread = threading.Thread(target=self._collect_states, daemon=True)
        self._collector_thread.start()

    def _reset_engine(self) -> None:
        with self._engine_lock:
            if hasattr(self, "engine"):
                self.engine.stop()
            agents = [PianoAgent(), ViolinAgent()]
            self.scheduler = Scheduler(agents=agents, pattern=self.pattern)
            self.engine = BeatEngine()
            self.engine.register_listener(self.scheduler.handle_beat)
            self.engine.start(bpm=self.bpm)
            self.log_action(f"Engine started at {self.bpm} BPM")
            self._append_history(self.get_state())

    def _collect_states(self) -> None:
        while self._collector_running:
            try:
                state = self.get_state()
                self._append_history(state)
            except Exception:
                pass
            time.sleep(0.25)

    def _append_history(self, state: GameState) -> None:
        with self._history_lock:
            self.state_history.append(serialize_game_state(state))

    def log_action(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {"timestamp": timestamp, "message": message}
        with self._log_lock:
            self.log_history.append(entry)

    def get_state(self) -> GameState:
        return self.scheduler.build_state(self.bpm)

    def get_state_history(self) -> List[Dict[str, Any]]:
        with self._history_lock:
            return list(self.state_history)

    def get_log_history(self) -> List[Dict[str, str]]:
        with self._log_lock:
            return list(self.log_history)

    def pause(self) -> None:
        self.engine.pause()
        self.log_action(f"Paused at beat {self.scheduler.current_beat}")

    def resume(self) -> None:
        self.engine.resume()
        self.log_action(f"Resumed at beat {self.scheduler.current_beat}")

    def reset(self) -> None:
        self.log_action("Reset triggered")
        with self._history_lock:
            self.state_history.clear()
        self._reset_engine()

    def shutdown(self) -> None:
        self._collector_running = False
        self.engine.stop()
