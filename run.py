from __future__ import annotations

import threading
import time
import termios
import traceback

from readchar import readkey
from rich.live import Live

from engine.beat_engine import BeatEngine
from engine.scheduler import PianoAgent, Scheduler, ViolinAgent
from ui.renderer import Renderer


SAMPLE_PATTERN = [
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


def start_keyboard_watcher(renderer: Renderer, engine: BeatEngine, stop_event: threading.Event) -> threading.Thread:
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


def main() -> None:
    bpm = 128.0
    max_beats = max(entry["beat"] for entry in SAMPLE_PATTERN) + 8
    renderer = Renderer()
    agents = [PianoAgent(), ViolinAgent()]
    scheduler = Scheduler(agents=agents, pattern=SAMPLE_PATTERN)
    engine = BeatEngine()
    engine.register_listener(scheduler.handle_beat)
    stop_event = threading.Event()
    keyboard_thread = start_keyboard_watcher(renderer, engine, stop_event)

    engine.start(bpm=bpm, max_beats=max_beats)

    try:
        with Live(screen=True, refresh_per_second=12) as live:
            while engine.is_running() or renderer.help_visible:
                state = scheduler.build_state(bpm=bpm)
                live.update(renderer.render(state))
                time.sleep(0.1)
            # final frame to let players see final score
            state = scheduler.build_state(bpm=bpm)
            live.update(renderer.render(state))
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        stop_event.set()
        engine.stop()
        keyboard_thread.join(timeout=1.0)
        print("Run complete. Thank you for sampling the beat engine.")


if __name__ == "__main__":
    main()
