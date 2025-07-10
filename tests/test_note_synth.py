from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

from note_synth import note_to_frequency, synthesize_notes
import wave


def test_note_to_frequency_a4():
    assert abs(note_to_frequency("A4") - 440.0) < 1e-6


def test_synthesize_notes(tmp_path):
    notes = [
        {"pitch": "A4", "duration": "quarter"},
        {"pitch": "rest", "duration": "quarter"},
        {"pitch": "A4", "duration": "quarter"},
    ]
    output = tmp_path / "out.wav"
    synthesize_notes(notes, 120, str(output))
    assert output.exists()
    with wave.open(str(output), "r") as wf:
        frames = wf.getnframes()
        assert frames > 0
