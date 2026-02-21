# Mimesis – Audio Transcription + Source Comparison Toolkit

## Quickstart

1. Set up environment (installs repo deps + compatible Whisper version):
    ./setup_venv.sh

   Optional: pick a different Whisper build:
    WHISPER_VERSION=20230918 ./setup_venv.sh

2. Run full transcription:
    ./run.sh data/original.mp4

Outputs:
- Full transcript (.txt)
- Per-minute JSON
- Captions (.srt, .vtt)
- Source article scrape

## New Local Whisper CLI (No Scraping)

Use `bin/transcribe_media.py` to transcribe a local media file directly (mp4/mov/mp3/wav) with optional JSONL metadata lookup. This workflow does **not** scrape articles, parse HTML, compare sources, or create run snapshots.

Example:

```bash
python bin/transcribe_media.py /path/to/input.mp4 --srt --vtt --minute-json \
  --jsonl /path/to/index.jsonl
```

Notes:
- `--txt` and `--json` outputs are enabled by default.
- Add `--no-metadata` to skip all metadata lookup.
- `bin/call_whisper_transcribe.py` and `bin/call_whisper.py` are legacy scripts.

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
The base config now includes a `target_usb` path which download
scripts use as the default mount point for removable storage.

## Requirements

- Python 3.9+
- ffmpeg
- OpenAI Whisper (pinned older version for compatibility):
    pip install openai-whisper==20230314

  If you need to override locally, set `WHISPER_VERSION` when running `setup_venv.sh`.
  The setup script also installs setuptools/wheel and uses `--no-build-isolation`
  to avoid `ModuleNotFoundError: pkg_resources` when building older Whisper releases
  in newer Python environments.
- Others:
    pip install -r requirements.txt

## Credits

Developed by The Tim Ballard Defamation League – March 2025

mimesis/
├── bin/               # CLI scripts
├── conf/              # Configs
├── data/              # Media input
├── lib/
│   └── mimesis/       # Consolidated helper package
├── README.md          # ✔️ Exists
├── requirements.txt   # ✔️ Exists



## Further Reading

For ideas on simplifying the internal modules, see
[`docs/library_consolidation.md`](docs/library_consolidation.md).
