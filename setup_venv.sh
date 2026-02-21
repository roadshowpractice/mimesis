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
# openai-whisper==20230314 fails to build metadata on Python 3.13, so fall back
# to a newer release automatically if the pinned build cannot be installed.
WHISPER_VERSION="${WHISPER_VERSION:-20230314}"
WHISPER_FALLBACK_VERSION="${WHISPER_FALLBACK_VERSION:-20240930}"

if pip install --no-build-isolation "openai-whisper==${WHISPER_VERSION}"; then
  INSTALLED_WHISPER_VERSION="${WHISPER_VERSION}"
else
  echo "⚠️  Failed to install openai-whisper==${WHISPER_VERSION}."
  echo "   Retrying with openai-whisper==${WHISPER_FALLBACK_VERSION} (recommended for Python 3.13+)."
  pip install --no-build-isolation "openai-whisper==${WHISPER_FALLBACK_VERSION}"
  INSTALLED_WHISPER_VERSION="${WHISPER_FALLBACK_VERSION}"
fi

echo "✅ Virtual environment ready."
echo "   Activate with: source venv/bin/activate"
echo "   Whisper version installed: ${INSTALLED_WHISPER_VERSION}"
