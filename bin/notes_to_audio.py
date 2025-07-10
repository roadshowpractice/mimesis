import os
import sys

# Add lib path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib")
sys.path.append(lib_path)

from note_synth import synthesize_from_json


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python notes_to_audio.py <notes.json> <output.wav>")
        sys.exit(1)
    synthesize_from_json(sys.argv[1], sys.argv[2])
