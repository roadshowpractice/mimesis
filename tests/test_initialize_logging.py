import logging
from pathlib import Path
import types
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

# Stub heavy dependencies so mimesis.video can be imported without them
sys.modules.setdefault("yaml", types.SimpleNamespace())
sys.modules.setdefault(
    "speech_recognition",
    types.SimpleNamespace(Recognizer=object, AudioFile=object),
)
sys.modules.setdefault(
    "moviepy.editor",
    types.SimpleNamespace(
        VideoFileClip=object,
        TextClip=object,
        CompositeVideoClip=object,
        ColorClip=object,
        concatenate_videoclips=object,
    ),
)

from mimesis.video import initialize_logging


def test_initialize_logging_creates_log_file(tmp_path, monkeypatch):
    # Remove existing handlers so initialize_logging can set up fresh ones
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    # Run within tmp directory so logs are created there
    monkeypatch.chdir(tmp_path)
    logger = initialize_logging()
    logger.info("hello from test")

    log_file = tmp_path / "logs" / "tja.log"
    assert log_file.exists()
    contents = log_file.read_text()
    assert "hello from test" in contents
