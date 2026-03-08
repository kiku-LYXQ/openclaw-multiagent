from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class BeatSignal:
    timestamp: float
    beat_index: int


class BeatEngine:
    def __init__(self) -> None:
        self.bpm: float = 0
        self._beat_duration: float = 0
        self._listeners: List[Callable[[BeatSignal], None]] = []
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._current_beat = 0
        self._max_beats: Optional[int] = None

    @property
    def current_beat(self) -> int:
        return self._current_beat

    def register_listener(self, callback: Callable[[BeatSignal], None]) -> None:
        self._listeners.append(callback)

    def start(self, bpm: float, max_beats: Optional[int] = None) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.bpm = bpm
        self._beat_duration = 60.0 / max(self.bpm, 1)
        self._max_beats = max_beats
        self._running.set()
        self._paused.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=1.0)

    def is_running(self) -> bool:
        return self._running.is_set() and (not self._thread or self._thread.is_alive())

    def _broadcast(self, signal: BeatSignal) -> None:
        for listener in self._listeners:
            try:
                listener(signal)
            except Exception:
                continue

    def _run_loop(self) -> None:
        self._current_beat = 0
        start = time.perf_counter()
        next_beat = start
        while self._running.is_set():
            if self._paused.is_set():
                time.sleep(0.05)
                continue
            now = time.perf_counter()
            if now + 1e-4 >= next_beat:
                self._current_beat += 1
                signal = BeatSignal(timestamp=time.time(), beat_index=self._current_beat)
                self._broadcast(signal)
                next_beat += self._beat_duration
                if self._max_beats and self._current_beat >= self._max_beats:
                    self._running.clear()
                    break
            else:
                time.sleep(min(next_beat - now, 0.01))
