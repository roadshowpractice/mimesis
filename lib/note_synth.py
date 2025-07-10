import json
import math
import wave
from array import array
from typing import List, Dict

# Mapping of note names to semitone offsets from C
_NOTE_OFFSETS = {
    "C": 0,
    "C#": 1,
    "D": 2,
    "D#": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "G": 7,
    "G#": 8,
    "A": 9,
    "A#": 10,
    "B": 11,
}

# Length of note relative to quarter note
_DURATION_MAP = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "sixteenth": 0.25,
}


def note_to_frequency(note: str) -> float:
    """Return frequency in Hz for a musical note like ``"A4"``."""
    if note in ("rest", "REST"):
        return 0.0
    # Support sharp notes only (e.g. "C#4").
    if len(note) == 3:
        name = note[:2]
        octave = int(note[2])
    else:
        name = note[0]
        octave = int(note[1])
    semitone = _NOTE_OFFSETS[name] + (octave + 1) * 12
    return 440.0 * 2 ** ((semitone - 69) / 12)


def synthesize_notes(
    notes: List[Dict[str, str]], tempo_bpm: int, output_path: str, sample_rate: int = 44100
) -> None:
    """Create a WAV file from a list of notes.

    Parameters
    ----------
    notes:
        Sequence of note dictionaries each containing ``"pitch"`` and ``"duration"``.
    tempo_bpm:
        Tempo in beats (quarter notes) per minute.
    output_path:
        File path of the resulting ``.wav`` file.
    sample_rate:
        Sample rate of the audio in Hz.
    """
    beat_duration = 60.0 / tempo_bpm
    audio = array("h")

    for item in notes:
        length = _DURATION_MAP.get(item.get("duration", "quarter"), 1.0)
        seconds = beat_duration * length
        samples = int(sample_rate * seconds)

        pitch = item.get("pitch", "rest")
        freq = note_to_frequency(pitch)

        if freq == 0.0:
            wave_data = [0] * samples
        else:
            amplitude = 16383  # moderate volume
            wave_data = [
                int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
                for i in range(samples)
            ]
        audio.extend(wave_data)

    # Normalize to int16 range
    max_val = max(abs(s) for s in audio) or 1
    scale = 32767 / max_val
    int_samples = array(
        "h", [int(s * scale) for s in audio]
    )

    with wave.open(output_path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(int_samples.tobytes())


def synthesize_from_json(json_path: str, output_path: str) -> None:
    """Load notes from a JSON file and create a WAV file."""
    with open(json_path, "r") as fh:
        data = json.load(fh)
    notes = data.get("notes", [])
    tempo = data.get("tempo_bpm", 120)
    synthesize_notes(notes, tempo, output_path)
