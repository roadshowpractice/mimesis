#!/bin/bash
set -euo pipefail

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Use an older Whisper build by default for compatibility with this repo.
WHISPER_VERSION="${WHISPER_VERSION:-20230314}"
pip install "openai-whisper==${WHISPER_VERSION}"

echo "✅ Virtual environment ready."
echo "   Activate with: source venv/bin/activate"
echo "   Whisper version installed: ${WHISPER_VERSION}"
