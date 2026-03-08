from .base import BaseMusicAgent


class ViolinAgent(BaseMusicAgent):
    """A rhythm agent tuned for violin lines."""

    def __init__(
        self,
        name: str = "Violin",
        role: str = "lead",
        timing_tolerance: float = 0.12,
    ) -> None:
        super().__init__(
            name=name,
            role=role,
            sound_label="♪ VIOLIN",
            color="magenta",
            timing_tolerance=timing_tolerance,
        )
