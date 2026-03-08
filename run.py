from __future__ import annotations

import threading
import time
import termios
import traceback
import sys

from readchar import readkey
from rich.live import Live

from engine.beat_engine import BeatEngine
from engine.scheduler import PianoAgent, Scheduler, ViolinAgent
from ui.renderer import Renderer

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


def start_keyboard_watcher(renderer: Renderer, engine: BeatEngine, stop_event: threading.Event, interactive: bool) -> threading.Thread:
    if not interactive:
        thread = threading.Thread(target=lambda: None, daemon=True)
        thread.start()
        return thread

    def runner() -> None:
        while not stop_event.is_set():
            try:
                key = readkey()
            except (KeyboardInterrupt, EOFError, termios.error):
                stop_event.set()
                break
            upper = key.upper()
            if upper == "H":
                renderer.toggle_help()
            elif upper == "P":
                paused = renderer.toggle_pause()
                if paused:
                    engine.pause()
                else:
                    engine.resume()
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return thread


def pretty_headless_summary(state):
    print(
        f"[Headless] Beat {state.current_beat} | Score {state.score_state.score} | Combo {state.score_state.combo} | Last {state.score_state.last_judgement}"
    )


def main() -> None:
    bpm = 128.0
    max_beats = max(entry["beat"] for entry in PATTERN) + 8
    renderer = Renderer()
    agents = [PianoAgent(), ViolinAgent()]
    scheduler = Scheduler(agents=agents, pattern=PATTERN)
    engine = BeatEngine()
    engine.register_listener(scheduler.handle_beat)
    stop_event = threading.Event()
    interactive = sys.stdout.isatty() and sys.stdin.isatty()
    keyboard_thread = start_keyboard_watcher(renderer, engine, stop_event, interactive)

    engine.start(bpm=bpm, max_beats=max_beats)

    try:
        if interactive:
            with Live(screen=True, refresh_per_second=12) as live:
                while engine.is_running() or renderer.help_visible:
                    state = scheduler.build_state(bpm=bpm)
                    live.update(renderer.render(state))
                    time.sleep(0.1)
                state = scheduler.build_state(bpm=bpm)
                live.update(renderer.render(state))
                time.sleep(0.5)
        else:
            while engine.is_running():
                state = scheduler.build_state(bpm=bpm)
                pretty_headless_summary(state)
                time.sleep(0.5)
            state = scheduler.build_state(bpm=bpm)
            pretty_headless_summary(state)
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        stop_event.set()
        engine.stop()
        keyboard_thread.join(timeout=1.0)
        try:
            import os
            os.system("stty sane")
        except Exception:
            pass
        print("Run complete. Thank you for sampling the beat engine. (terminal restored)")


if __name__ == "__main__":
    main()
