#!/bin/bash
set -euo pipefail

# ---- config ----
VENV_DIR="${VENV_DIR:-venv}"
PIP_TIMEOUT="${PIP_TIMEOUT:-120}"
PIP_RETRIES="${PIP_RETRIES:-10}"

# Prefer system Python 3.8 on Ubuntu 20.04 machines (your box)
PYTHON_BIN="${PYTHON_BIN:-python3.8}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

# Refuse to run inside conda (easy way to poison the build)
if [[ -n "${CONDA_PREFIX:-}" ]]; then
  echo "❌ You appear to be inside conda: CONDA_PREFIX=${CONDA_PREFIX}"
  echo "   Run: conda deactivate (until (base) disappears), then re-run."
  exit 1
fi

echo "✅ Using: $($PYTHON_BIN -V)"

rm -rf "$VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Make pip resilient to slow PyPI downloads
export PIP_DEFAULT_TIMEOUT="$PIP_TIMEOUT"

# Tooling first (setuptools<81 keeps pkg_resources available)
python -m pip install --upgrade "pip<26" "setuptools<81" wheel

# Install deps (retry/timeout hardened)
python -m pip install --retries "$PIP_RETRIES" --timeout "$PIP_TIMEOUT" -r requirements.txt

# Whisper last
WHISPER_VERSION="${WHISPER_VERSION:-20230314}"
python -m pip install --retries "$PIP_RETRIES" --timeout "$PIP_TIMEOUT" --no-build-isolation "openai-whisper==${WHISPER_VERSION}"

echo "✅ venv ready: source $VENV_DIR/bin/activate"
python -c "import numpy, cv2, whisper; print('numpy', numpy.__version__); print('cv2', cv2.__version__); print('whisper ok')"
