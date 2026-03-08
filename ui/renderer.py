from __future__ import annotations

from typing import List

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models import AgentState, BeatTimelineEntry, GameState


class Renderer:
    def __init__(self) -> None:
        self.help_visible = False
        self.paused = False

    def toggle_help(self) -> None:
        self.help_visible = not self.help_visible

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    def render(self, state: GameState) -> RenderableType:
        layout = Layout()
        layout.split_column(
            Layout(self._render_header(state), size=5, name="header"),
            Layout(name="body", ratio=1),
            Layout(self._render_footer(state), size=4, name="footer"),
        )
        layout["body"].split_row(
            Layout(self._render_timeline(state.beat_timeline), ratio=2),
            Layout(self._render_agents(state.agent_states, state.recent_judgements), ratio=1),
        )

        if self.help_visible or self.paused:
            overlay_panels = []
            if self.help_visible:
                overlay_panels.append(self._render_help_overlay())
            if self.paused:
                overlay_panels.append(self._render_pause_overlay())
            overlay = self._render_overlay(overlay_panels)
            return Group(overlay, layout)
        return layout

    def _render_header(self, state: GameState) -> Panel:
        score = Text.assemble(
            (f" BPM {state.bpm:0.1f} ", "bold white on dark_blue"),
            (" ", ""),
            (f"Score: {state.score_state.score} ", "bold bright_white"),
            (f"Combo: {state.score_state.combo} ", "bold spring_green1"),
            (f"High: {state.score_state.high_score}", "bold magenta"),
            (f" Last: {state.score_state.last_judgement}", "bold yellow"),
        )
        title = f"Beat #{state.current_beat}"
        return Panel(score, title=title, border_style="bright_blue", padding=(0, 1))

    def _render_timeline(self, timeline: List[BeatTimelineEntry]) -> Panel:
        displayed = list(reversed(timeline))[:12]
        if not displayed:
            return Panel(Text("waiting for beats...", style="italic grey50"), border_style="grey37")
        columns = []
        for entry in displayed:
            status = "✔" if entry.success else "✖"
            text = Text(justify="center")
            text.append(f"{entry.agent_name}\n", style="bold " + entry.color)
            text.append(f"{entry.label}\n", style=entry.color)
            text.append(f"Beat {entry.beat_index} {status}", style="bold white")
            border = entry.color if entry.success else "red"
            columns.append(Panel(text, border_style=border, box=box.ROUNDED, padding=(0, 1)))
        return Panel(Columns(columns, expand=True), title="Beat Timeline", border_style="bright_blue")

    def _render_agents(self, agents: List[AgentState], judgements: List[str]) -> Panel:
        table = Table.grid(expand=True)
        table.add_column("Agent", justify="left", ratio=2)
        table.add_column("Status", justify="center", ratio=2)
        table.add_column("Combo", justify="center", ratio=1)
        table.add_column("Next", justify="center", ratio=1)
        table.add_column("Sound", justify="left", ratio=2)
        for agent in agents:
            name_text = Text(agent.name, style=agent.color)
            status = Text(agent.status, style="bold white")
            combo = Text(str(agent.combo), style="bold green4")
            next_window = Text(f"{agent.next_window:0.1f}", style="bold yellow")
            sound = Text(agent.sound_label, style=agent.color)
            table.add_row(name_text, status, combo, next_window, sound)
        footer = Text("Recent: ", style="bold magenta")
        footer.append(
            ", ".join(judgements[:3]) if judgements else "—",
            style="bold white",
        )
        panel = Panel(Group(table, Align.left(footer)), title="Agents", border_style="cyan", padding=1)
        return panel

    def _render_footer(self, state: GameState) -> Panel:
        judgement_text = Text.assemble(
            ("Judgements in flight: ", "bold white"),
            (", ".join(state.recent_judgements[:4]) or "none", "bold yellow"),
        )
        help_hint = Text("Press H for Help, P to Pause/Resume", style="italic grey60")
        return Panel(Group(judgement_text, help_hint), border_style="grey37")

    def _render_help_overlay(self) -> Panel:
        help_text = Text(
            "Controls:\n"
            "  H - Toggle help overlay\n"
            "  P - Pause / resume beat engine\n"
            "  Ctrl+C - Exit cleanly\n"
            "UI:\n"
            "  Timeline shows beat history + color-coded instruments\n"
            "  Score and combo banner updates per judgement\n"
            "  Agent panel lists status, upcoming window, and sound label",
            justify="left",
        )
        return Panel(help_text, title="Help Overlay", border_style="bright_green", padding=(1, 2))

    def _render_pause_overlay(self) -> Panel:
        text = Text("Paused. Press P to resume.", justify="center", style="bold white")
        return Panel(text, title="Game Paused", border_style="yellow", padding=(1, 2))

    def _render_overlay(self, overlays: List[Panel]) -> RenderableType:
        return Panel(Group(*overlays), box=box.DOUBLE, border_style="bright_white", padding=(1, 1))
