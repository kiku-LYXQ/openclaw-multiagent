from __future__ import annotations

import math
from typing import Dict

try:
    import simpleaudio as sa
except ImportError:
    sa = None

SAMPLE_RATE = 44100
DURATION = 0.2
BASE_FREQS: Dict[str, float] = {
    "piano": 440.0,
    "violin": 660.0,
}
_waves: Dict[str, "sa.WaveObject"] = {}


def _build_wave(freq: float) -> "sa.WaveObject":
    if sa is None:
        raise RuntimeError("simpleaudio not installed")
    num_samples = int(SAMPLE_RATE * DURATION)
    wave_data = bytearray()
    for i in range(num_samples):
        sample = 0.5 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
        packed = int(sample * 32767)
        wave_data += packed.to_bytes(2, "little", signed=True)
    return sa.WaveObject(bytes(wave_data), 1, 2, SAMPLE_RATE)


def play_instrument_sound(label: str) -> None:
    if sa is None:
        return
    instrument = label.lower()
    freq = BASE_FREQS.get(instrument, 440.0)
    wave = _waves.get(instrument)
    if wave is None:
        wave = _build_wave(freq)
        _waves[instrument] = wave
    wave.play()
