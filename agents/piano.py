from .base import BaseMusicAgent


class PianoAgent(BaseMusicAgent):
    """A rhythm agent tuned for piano lines."""

    def __init__(
        self,
        name: str = "Piano",
        role: str = "melody",
        timing_tolerance: float = 0.15,
    ) -> None:
        super().__init__(
            name=name,
            role=role,
            sound_label="♪ PIANO",
            color="cyan",
            timing_tolerance=timing_tolerance,
        )
