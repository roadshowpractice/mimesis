import logging
import os
import json

from mimesis.archive import handle_gdrive_tar
from mimesis.video import extract_audio_from_video, load_app_config

try:
    import whisper
except Exception:  # pragma: no cover - whisper may not be installed
    whisper = None

logger = logging.getLogger(__name__)


def transcribe_and_translate(audio_path: str, model_size: str = "base") -> str:
    """Return English transcription using Whisper."""
    if whisper is None:
        raise RuntimeError("whisper package not available")
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, task="translate", language="en")
    return result.get("text", "")


def process_drive_tar_and_transcribe(url: str, work_dir: str) -> dict:
    """Download tar from Google Drive, extract, transcribe, translate."""
    cfg = load_app_config()
    params = {"url": url, "download_path": work_dir}
    logger.info("Starting Google Drive download")
    result = handle_gdrive_tar(params)
    transcripts = {}
    for path in result.get("extracted", []):
        base = os.path.splitext(os.path.basename(path))[0]
        audio_path = os.path.join(work_dir, base + ".wav")
        logger.info("Extracting audio: %s", path)
        extract_audio_from_video(path, 0, None, audio_path)
        logger.info("Transcribing with Whisper")
        text = transcribe_and_translate(audio_path)
        transcripts[path] = text
    out_path = os.path.join(work_dir, "transcripts.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(transcripts, fh, indent=2)
    logger.info("Wrote transcripts to %s", out_path)
    return transcripts
