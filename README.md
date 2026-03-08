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
make run   # execute run.py (Rich UI or headless summary)
make test  # run pytest tests/test_agents.py
make lint  # run python -m py_compile agents/*.py engine/*.py ui/*.py models.py run.py
```
The Makefile simply wraps these commands; running them inside another directory will fail.

## Requirements

The demo relies on the following Python packages:

```bash
pip install rich readchar
```

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
