import logging
from pathlib import Path
import sys
import types

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

# Stub heavy dependencies so mimesis.video imports cleanly
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


def test_log_kilroy():
    log_dir = Path("test_logs")
    log_file = log_dir / "kilroy.log"
    if log_dir.exists():
        for f in log_dir.glob("*"):
            f.unlink()
    log_dir.mkdir(exist_ok=True)
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    logger = initialize_logging(log_name="kilroy", log_dir=str(log_dir))
    logger.info("Kilroy was here")
    assert log_file.exists(), "log file not created"
    contents = log_file.read_text()
    assert "Kilroy was here" in contents
    # Clean up
    for f in log_dir.glob("*"):
        f.unlink()
    log_dir.rmdir()
