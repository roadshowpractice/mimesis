#!/bin/bash
set -euo pipefail

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Older Whisper releases can require pkg_resources at build time.
# Ensure setuptools is available in this venv and disable build isolation so
# the dependency is visible while building pinned Whisper versions.
pip install "setuptools<81" wheel

# Use an older Whisper build by default for compatibility with this repo.
WHISPER_VERSION="${WHISPER_VERSION:-20230314}"
pip install --no-build-isolation "openai-whisper==${WHISPER_VERSION}"

echo "✅ Virtual environment ready."
echo "   Activate with: source venv/bin/activate"
echo "   Whisper version installed: ${WHISPER_VERSION}"
