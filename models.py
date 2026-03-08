from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class RhythmEvent:
    beat_index: int
    agent_name: str
    action: str
    timestamp: float


@dataclass
class RhythmResult:
    success: bool
    timing: float
    status_label: str


@dataclass
class ScoreState:
    score: int
    combo: int
    high_score: int
    last_judgement: str


@dataclass
class AgentState:
    name: str
    role: str
    status: str
    next_window: float
    combo: int
    sound_label: str
    color: str


@dataclass
class BeatTimelineEntry:
    beat_index: int
    agent_name: str
    label: str
    color: str
    success: bool
    timestamp: float


@dataclass
class GameState:
    bpm: float
    current_beat: int
    score_state: ScoreState
    agent_states: List[AgentState]
    beat_timeline: List[BeatTimelineEntry]
    recent_judgements: List[str]
