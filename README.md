# Mimesis – Audio Transcription + Source Comparison Toolkit

## Quickstart

1. Set up environment:
    ./setup_venv.sh

2. Run full transcription:
    ./run.sh data/original.mp4

Outputs:
- Full transcript (.txt)
- Per-minute JSON
- Captions (.srt, .vtt)
- Source article scrape

## Project Structure

bin/        # Scripts (transcribe, captions, etc.)
conf/       # Configs
data/       # Media input
lib/        # Local Python packages
run.sh      # Run the pipeline
setup_venv.sh   # One-line environment setup
requirements.txt

## Configuration

Application defaults live in `conf/app_config.json`.  At runtime
`load_app_config()` also looks for optional per-OS overrides in
`conf/config.json` keyed by the value of `platform.system()`.  When
present, those settings are merged into the base configuration.

## Requirements

- Python 3.9+
- ffmpeg
- OpenAI Whisper:
    pip install git+https://github.com/openai/whisper.git
- Others:
    pip install -r requirements.txt

## Credits

Developed by The Tim Ballard Defamation League – March 2025

mimesis/
├── bin/               # CLI scripts
├── conf/              # Configs
├── data/              # Media input
├── lib/               # Local modules (Acme/ and helpers)
├── README.md          # ✔️ Exists
├── requirements.txt   # ✔️ Exists



## Further Reading

For ideas on simplifying the internal modules, see
[`docs/library_consolidation.md`](docs/library_consolidation.md).
