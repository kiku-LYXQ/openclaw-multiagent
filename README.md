# new-app Beat UI Demo

This directory contains a minimal rhythm game experience powered by a **beat engine**, **scheduler**, and **beautiful terminal UI** (using [Rich](https://github.com/Textualize/rich)). The CLI entry point is `run.py` which integrates the timing loop with a scheduler and `Renderer` that displays:

- BPM, score, combo, high score, and judgement legend in a banner.
- Color-coded beat timeline panels representing the piano & violin instrumentation with their `sound_label` and status icons.
- Agent status table showing name, role, status, combo, next beat window, and instrument label.
- Overlay panels triggered by `H` (help) and `P` (pause) that summarize controls and pause state.
- Recent judgements stream below the agent view.

## Requirements

The demo relies on the following Python packages:

```bash
pip install rich readchar
```

`rich` is used for layout, colors, and the live display. `readchar` enables non-blocking single-key input for `H`/`P` toggles.

## Running the demo

From this directory run:

```bash
python run.py
```

It will play a short predefined beat pattern (~24 beats) at 128 BPM. You will see the beat timeline update, agent panels, and scoring banner. Press:

- `H` to show/hide the help overlay that summarizes key bindings and UI sections.
- `P` to pause or resume the beat engine. The overlay will signal when the loop is paused and prevents new beats from firing until resumed.
- `Ctrl+C` if you want to exit early before the pattern finishes.

## Notes

- The scheduler uses a deterministic sample pattern and randomised judgement timing to simulate misses and perfect hits.
- Help and pause overlays render before the rest of the layout (they appear as stacked panels). This keeps the UI curses-friendly without low-level terminal control.
- The CLI is self-contained inside `new-app/run.py` so you can experiment with different patterns/agents if you need to expand the demo.
