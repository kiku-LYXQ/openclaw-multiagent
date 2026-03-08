from __future__ import annotations

import random
import time
from collections import defaultdict, deque
from typing import Any, Callable, Dict, Iterable, List

from models import (
    AgentState,
    BeatTimelineEntry,
    GameState,
    RhythmEvent,
    RhythmResult,
    ScoreState,
)


class BaseAgent:
    def __init__(self, name: str, role: str, sound_label: str, color: str, timing_tolerance: float = 0.25) -> None:
        self.name = name
        self.role = role
        self.sound_label = sound_label
        self.color = color
        self.timing_tolerance = timing_tolerance
        self.status = "Idle"
        self.combo = 0
        self._cooldown_until = 0.0
        self._last_action = "Ready"

    def tick(self, timestamp: float) -> None:
        if timestamp >= self._cooldown_until:
            self.status = "Ready"
        self._last_action = self.status

    def input(self, event: RhythmEvent) -> RhythmResult:
        now = event.timestamp
        drift = abs(random.uniform(-self.timing_tolerance, self.timing_tolerance))
        success = drift < self.timing_tolerance or random.random() > 0.15
        status_label = "Perfect" if drift < self.timing_tolerance / 2 else "Good"
        if not success:
            status_label = "Miss"
        self.status = "Action" if success else "Cooldown"
        self._cooldown_until = now + 0.4
        if success:
            self.combo += 1
        else:
            self.combo = 0
        self._last_action = status_label
        return RhythmResult(success=success, timing=drift, status_label=status_label)

    def state(self, next_window: float) -> AgentState:
        return AgentState(
            name=self.name,
            role=self.role,
            status=self.status,
            next_window=next_window,
            combo=self.combo,
            sound_label=self.sound_label,
            color=self.color,
        )


class PianoAgent(BaseAgent):
    def __init__(self, name: str = "Piano") -> None:
        super().__init__(name=name, role="Keys", sound_label="♪ PIANO", color="cyan1", timing_tolerance=0.2)


class ViolinAgent(BaseAgent):
    def __init__(self, name: str = "Violin") -> None:
        super().__init__(name=name, role="Strings", sound_label="♪ VIOLIN", color="magenta3", timing_tolerance=0.3)


class Scheduler:
    def __init__(self, agents: Iterable[BaseAgent], pattern: Iterable[Dict[str, Any]]) -> None:
        self.agents: Dict[str, BaseAgent] = {agent.name: agent for agent in agents}
        self.pattern_map = self._group_pattern(pattern)
        self.score = 0
        self.combo = 0
        self.high_score = 0
        self.last_judgement = "Waiting"
        self.beat_timeline: deque[BeatTimelineEntry] = deque(maxlen=16)
        self.recent_judgements: deque[str] = deque(maxlen=6)
        self.current_beat = 0

    @staticmethod
    def _group_pattern(pattern: Iterable[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for entry in pattern:
            beat = int(entry.get("beat", 0))
            grouped[beat].append(entry)
        return grouped

    def handle_beat(self, signal: "BeatSignal") -> None:
        self.current_beat = signal.beat_index
        entries = self.pattern_map.get(signal.beat_index, [])
        for agent in self.agents.values():
            agent.tick(signal.timestamp)
        if not entries:
            self._add_timeline_entry(signal, success=True, agent_name="---", label="(rest)", color="grey50")
            return
        for entry in entries:
            agent = self.agents.get(entry.get("agent"))
            if not agent:
                continue
            event = RhythmEvent(
                beat_index=signal.beat_index,
                agent_name=agent.name,
                action=entry.get("action", "hit"),
                timestamp=signal.timestamp,
            )
            result = agent.input(event)
            self._update_score(result)
            sound_label = agent.sound_label
            color = agent.color
            self._add_timeline_entry(signal, success=result.success, agent_name=agent.name, label=sound_label, color=color)
            self.recent_judgements.appendleft(result.status_label)

    def _update_score(self, result: RhythmResult) -> None:
        if result.success:
            self.combo += 1
            gain = 100 + self.combo * 5
            self.score += gain
            self.last_judgement = result.status_label
            self.high_score = max(self.high_score, self.score)
        else:
            self.combo = 0
            self.last_judgement = result.status_label

    def _add_timeline_entry(
        self,
        signal: "BeatSignal",
        success: bool,
        agent_name: str,
        label: str,
        color: str,
    ) -> None:
        entry = BeatTimelineEntry(
            beat_index=signal.beat_index,
            agent_name=agent_name,
            label=label,
            color=color,
            success=success,
            timestamp=signal.timestamp,
        )
        self.beat_timeline.appendleft(entry)

    def build_state(self, bpm: float) -> GameState:
        agent_states = []
        next_window = float(self.current_beat + 1)
        for agent in self.agents.values():
            agent_states.append(agent.state(next_window=next_window))
        score_state = ScoreState(
            score=self.score,
            combo=self.combo,
            high_score=self.high_score,
            last_judgement=self.last_judgement,
        )
        return GameState(
            bpm=bpm,
            current_beat=self.current_beat,
            score_state=score_state,
            agent_states=agent_states,
            beat_timeline=list(self.beat_timeline),
            recent_judgements=list(self.recent_judgements),
        )
