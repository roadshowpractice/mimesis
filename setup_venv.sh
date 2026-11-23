#!/bin/bash
# Create a venv that can actually run this repo on this machine.
#
#   ./setup_venv.sh                       # deps only (fast); tests + download/watermark work
#   WITH_WHISPER=1 ./setup_venv.sh        # also install Whisper (pulls torch, ~0.7 GB)
#   PYTHON_BIN=python3.10 ./setup_venv.sh # choose the interpreter (needed on Python 3.13+;
#                                         #   the pinned numpy/opencv have no wheels there)
#   FORCE=1 ./setup_venv.sh               # recreate an existing $VENV_DIR
set -euo pipefail

VENV_DIR="${VENV_DIR:-venv}"
PIP_TIMEOUT="${PIP_TIMEOUT:-120}"
PIP_RETRIES="${PIP_RETRIES:-10}"
WITH_WHISPER="${WITH_WHISPER:-0}"
FORCE="${FORCE:-0}"

if [[ -n "${CONDA_PREFIX:-}" ]]; then
  echo "❌ You appear to be inside conda: CONDA_PREFIX=${CONDA_PREFIX}"
  echo "   Run: conda deactivate (until (base) disappears), then re-run."
  exit 1
fi

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PY="$PYTHON_BIN"
else
  PY=""
  for c in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
command -v "$PY" >/dev/null 2>&1 || {
  echo "❌ No Python interpreter found; set PYTHON_BIN=/path/to/python3.10"; exit 1;
}
echo "✅ Using: $("$PY" -V 2>&1)"
"$PY" -c 'import sys; raise SystemExit(0 if sys.version_info < (3, 13) else 1)' || \
  echo "⚠️  Python 3.13+ has no wheels for the pinned numpy/opencv; set PYTHON_BIN=python3.10 or 3.11 if pip fails."

if [[ -e "$VENV_DIR" ]]; then
  if [[ "$FORCE" != "1" ]]; then
    echo "❌ $VENV_DIR already exists (set FORCE=1 to recreate it)"; exit 1
  fi
  echo "♻️  removing existing $VENV_DIR (FORCE=1)"
  rm -rf "$VENV_DIR"
fi

"$PY" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

export PIP_DEFAULT_TIMEOUT="$PIP_TIMEOUT"
python -m pip install --upgrade "pip<26" "setuptools<81" wheel
python -m pip install --retries "$PIP_RETRIES" --timeout "$PIP_TIMEOUT" -r requirements.txt

if [[ "$WITH_WHISPER" == "1" ]]; then
  WHISPER_VERSION="${WHISPER_VERSION:-20230314}"
  if ! python -m pip install --retries "$PIP_RETRIES" --timeout "$PIP_TIMEOUT" \
      --no-build-isolation "openai-whisper==${WHISPER_VERSION}"; then
    echo "⚠️  Whisper install failed (usually disk quota while fetching torch)."
    echo "    Repo deps are installed and the t/ suite runs; run.sh needs Whisper."
    echo "    Free space, then: python -m pip install openai-whisper==${WHISPER_VERSION}"
    exit 1
  fi
else
  echo "ℹ️  Whisper skipped (WITH_WHISPER=0). run.sh needs it; the t/ suite does not."
fi

echo "✅ venv ready: source $VENV_DIR/bin/activate"
python - <<'PY'
import numpy, cv2
print("numpy", numpy.__version__, "cv2", cv2.__version__)
try:
    import whisper
    print("whisper ok")
except Exception:
    pass
PY
