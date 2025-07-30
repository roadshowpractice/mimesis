from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

from note_synth import note_to_frequency


def test_note_to_frequency_a4():
    assert abs(note_to_frequency("A4") - 440.0) < 1e-6

