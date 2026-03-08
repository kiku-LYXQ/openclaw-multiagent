import sys
from pathlib import Path
from typing import Optional

# Ensure the new-app directory is on sys.path when tests run from the workspace root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.base import RhythmEvent, SAMPLE_RHYTHM_PATTERN
from agents.piano import PianoAgent
from agents.violin import ViolinAgent


def test_piano_hit_within_tolerance() -> None:
    agent = PianoAgent()
    piano_patterns = [entry for entry in SAMPLE_RHYTHM_PATTERN if entry.agent == "piano"]
    assert piano_patterns, "Expected at least one piano pattern event"

    pattern = piano_patterns[0]
    agent.schedule_event(pattern)

    state = agent.state()
    assert state["status"] == "Ready"
    assert state["next_window"] == (
        pattern.time - agent.timing_tolerance,
        pattern.time + agent.timing_tolerance,
    )

    hit_event = RhythmEvent(action=pattern.action, timestamp=pattern.time + 0.03)
    result = agent.input(hit_event)

    assert result.success
    assert result.status_label == "Hit x1"
    assert agent.state()["combo"] == 1
    assert agent.state()["status"] == "Cooldown"

    cooldown_exit = pattern.time + agent.timing_tolerance + 0.1
    agent.tick(cooldown_exit)
    assert agent.state()["status"] == "Idle"


def test_violin_miss_after_window() -> None:
    agent = ViolinAgent()
    violin_patterns = [entry for entry in SAMPLE_RHYTHM_PATTERN if entry.agent == "violin"]
    assert violin_patterns

    pattern = violin_patterns[0]
    agent.schedule_event(pattern)

    miss_time = pattern.time + agent.timing_tolerance + 0.15
    result = agent.tick(miss_time)

    assert result is not None
    assert not result.success
    assert result.status_label == "Miss"
    assert agent.state()["combo"] == 0
    assert agent.state()["status"] == "Idle"
    assert agent.state()["next_window"] is None


def test_combo_accumulates_on_sequential_hits() -> None:
    agent = PianoAgent()
    piano_patterns = [entry for entry in SAMPLE_RHYTHM_PATTERN if entry.agent == "piano"]
    assert len(piano_patterns) >= 2

    first, second = piano_patterns[:2]
    agent.schedule_event(first)
    first_result = agent.input(
        RhythmEvent(action=first.action, timestamp=first.time + agent.timing_tolerance / 2)
    )
    assert first_result.success
    assert first_result.status_label == "Hit x1"

    agent.tick(first.time + agent.timing_tolerance + 0.05)
    assert agent.state()["status"] == "Idle"

    agent.schedule_event(second)
    second_result = agent.input(
        RhythmEvent(action=second.action, timestamp=second.time - agent.timing_tolerance / 10)
    )
    assert second_result.success
    assert second_result.status_label == "Hit x2"
    assert agent.state()["combo"] == 2
