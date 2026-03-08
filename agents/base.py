from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union


@dataclass(frozen=True)
class RhythmPatternEvent:
    agent: str
    action: str
    time: float


@dataclass
class RhythmEvent:
    action: str
    timestamp: float


@dataclass
class RhythmResult:
    success: bool
    timing: float
    status_label: str


SAMPLE_RHYTHM_PATTERN: List[RhythmPatternEvent] = [
    RhythmPatternEvent(agent="piano", action="hit", time=0.5),
    RhythmPatternEvent(agent="violin", action="hit", time=1.25),
    RhythmPatternEvent(agent="piano", action="hit", time=2.0),
    RhythmPatternEvent(agent="violin", action="hit", time=2.75),
]


class BaseMusicAgent:
    """Base logic for a rhythm-based instrument agent."""

    def __init__(
        self,
        name: str,
        role: str,
        sound_label: str,
        color: str,
        timing_tolerance: float,
    ) -> None:
        self.name = name
        self.role = role
        self.sound_label = sound_label
        self.color = color
        self.timing_tolerance = timing_tolerance

        self._status = "Idle"
        self._status_label = "Idle"
        self._combo = 0
        self._scheduled_event: Optional[RhythmPatternEvent] = None
        self._next_window: Optional[Tuple[float, float]] = None
        self._last_result: Optional[RhythmResult] = None
        self._cooldown_until: Optional[float] = None

    # Interface enforced by design doc -------------------------------------------------
    def tick(self, timestamp: float) -> Optional[RhythmResult]:
        """Advance time, detect misses, and expire cooldown."""
        if self._status == "Cooldown" and self._cooldown_until is not None:
            if timestamp >= self._cooldown_until:
                self._status = "Idle"
                self._status_label = "Idle"
                self._cooldown_until = None

        if self._scheduled_event and self._status == "Ready":
            _, window_end = self._next_window or (0.0, self._scheduled_event.time)
            if timestamp > window_end:
                timing = timestamp - self._scheduled_event.time
                return self._finalize_result(False, timing)
        return None

    def input(self, event: RhythmEvent) -> RhythmResult:
        """Record player input and judge success/miss."""
        if not self._scheduled_event:
            result = RhythmResult(False, event.timestamp, "Idle")
            self._status_label = "Idle"
            self._last_result = result
            return result

        expected_time = self._scheduled_event.time
        timing = event.timestamp - expected_time
        success = abs(timing) <= self.timing_tolerance
        return self._finalize_result(success, timing)

    def state(self) -> Dict[str, Union[str, int, Tuple[float, float], float, None]]:
        """Return a serializable state snapshot for renderers."""
        return {
            "name": self.name,
            "role": self.role,
            "status": self._status,
            "status_label": self._status_label,
            "next_window": self._next_window,
            "combo": self._combo,
            "sound_label": self.sound_label,
            "color": self.color,
            "timing_tolerance": self.timing_tolerance,
        }

    # Helpers ------------------------------------------------------------------------
    def schedule_event(self, pattern_event: RhythmPatternEvent) -> None:
        """Schedule the next expected rhythm pattern element."""
        self._scheduled_event = pattern_event
        center = pattern_event.time
        self._next_window = (
            center - self.timing_tolerance,
            center + self.timing_tolerance,
        )
        self._status = "Ready"
        self._status_label = f"Expecting {pattern_event.action.title()}"

    def _finalize_result(self, success: bool, timing: float) -> RhythmResult:
        """Handle success/failure and build the judgement result."""
        target_time = self._scheduled_event.time if self._scheduled_event else 0.0
        if success:
            self._combo += 1
            status_label = f"Hit x{self._combo}"
            self._status = "Cooldown"
            self._cooldown_until = target_time + self.timing_tolerance
        else:
            status_label = "Miss"
            self._combo = 0
            self._status = "Idle"
            self._cooldown_until = None

        result = RhythmResult(success, timing, status_label)
        self._last_result = result
        self._status_label = status_label
        self._clear_pending()
        return result

    def _clear_pending(self) -> None:
        self._scheduled_event = None
        self._next_window = None
