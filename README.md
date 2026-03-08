# new-app Beat UI Demo

This directory houses our rhythm game demo powered by a **beat engine**, **scheduler**, and **beautiful terminal UI** (using [Rich](https://github.com/Textualize/rich)). The CLI entry point is `run.py`, which integrates the timing loop with the scheduler and `Renderer` that displays:

- BPM, score, combo, high score, and judgement legend in a banner.
- Color-coded beat timeline panels representing the piano & violin instrumentation with their `sound_label` and status icons.
- Agent status table showing name, role, status, combo, next beat window, and instrument label.
- Overlay panels triggered by `H` (help) and `P` (pause) that summarize controls and pause state.
- Recent judgements stream below the agent view.


## Quick Commands

Use the provided Makefile to run/test/lint the project from this directory:
```bash
make run          # execute run.py (Rich UI or headless summary)
make run-server   # launch the FastAPI/WebSocket HUD service (uvicorn new_app.server:app)
make test         # run pytest tests
make lint         # run python -m py_compile agents/*.py engine/*.py ui/*.py models.py run.py server.py backend/*.py
```
The Makefile simply wraps these commands; running them inside another directory will fail.

## Requirements

The demo relies on the following Python packages:

```bash
pip install rich readchar simpleaudio fastapi uvicorn httpx
```

The newly added backend HUD service depends on FastAPI for its HTTP/WebSocket interface and Uvicorn for hosting the server. The FastAPI test suite uses `httpx`, so installing it keeps `pytest` happy when validating the REST/WebSocket surface.

`rich` is used for layout, colors, and the live display. `readchar` enables non-blocking single-key input for `H`/`P` toggles.

## Running the demo

From this directory run `python run.py`. This will play a predefined beat pattern (~24 beats) at 128 BPM and show the beat timeline, agent panel, and scoring banner. Press:

- `H` to toggle the help overlay with key bindings and UI cues.
- `P` to pause/resume the beat engine (Rich layout will show the pause overlay).
- `Ctrl+C` to exit early.

If you run in a non-interactive terminal (`tty` not available), the script prints a periodic headless summary (score/combo) and automatically ends after the pattern completes; the Rich UI is only visible when running in a real terminal.

## Notes

- The scheduler uses a deterministic sample pattern and randomised judgement timing to simulate misses and perfect hits.
- Help and pause overlays render as stacked panels, keeping the CLI curses-friendly.
- The CLI is self-contained inside `run.py`, so you can experiment with different patterns/agents.
- After normal completion the script runs `stty sane` to restore the terminal state so you can continue using the shell.

## Backend HUD Service

The HUD backend exposes the rhythm game state over HTTP and WebSocket so web dashboards or other clients can stay in sync with the beat engine.

1. Start the server with `make run-server` (which runs `uvicorn new_app.server:app`) or `python -m new_app.server` for a vanilla Python launch.
2. REST control/log surface:
   - `POST /pause` – pause the engine and add an action log entry.
   - `POST /resume` – resume the engine and log the transition back to running.
   - `POST /reset` – stop and rebuild the scheduler/engine, clear the cached history, and log the reset event.
   - `GET /logs` – returns `{ "logs": [...] }`, where each entry carries a timestamp, message, log level, and optional details.
   - `GET /history` – returns `{ "history": [...] }`. Each record is `{ "beat": <number>, "timestamp": <unix>, "state": <GameState dict> }` and contains the serialized `models.GameState` snapshot that mirrors the CLI HUD data shape.
3. WebSocket stream:
   - Connect to `ws://<host>/ws/state` (also served at the legacy `ws://<host>/ws/game-state`) to receive every broadcasted beat update. Each message is a JSON record identical to the history entries: `{ "beat": ..., "timestamp": ..., "state": { ... } }`, where `state` includes `bpm`, `current_beat`, `score_state`, `agent_states`, `beat_timeline`, and `recent_judgements`.
   - REST 控制也接受跨源请求（CORS 已开启），HUD 可直接从 Vite dev server 链接 `http://localhost:8000`。

The service reuses the same `models.GameState`/`AgentState`/`BeatTimelineEntry` shapes as the CLI renderer, so downstream consumers can mirror the HUD layout with minimal translation.

