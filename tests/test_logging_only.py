from pathlib import Path
import sys
import types

# Provide stubs for optional dependencies used by video_utils
sys.modules.setdefault('yaml', types.SimpleNamespace())
sys.modules.setdefault('speech_recognition', types.SimpleNamespace(Recognizer=object, AudioFile=object))
moviepy_stub = types.SimpleNamespace(VideoFileClip=object, TextClip=object, CompositeVideoClip=object, ColorClip=object, concatenate_videoclips=lambda *args, **kwargs: None)
sys.modules.setdefault('moviepy', types.SimpleNamespace(editor=moviepy_stub))
sys.modules.setdefault('moviepy.editor', moviepy_stub)

# Add lib to path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'lib'))

from video_utils import initialize_logging


def test_logging_only():
    logger = initialize_logging()
    log_file = Path('logs') / 'tja.log'

    before = log_file.read_text() if log_file.exists() else ''

    test_message = 'logging test entry'
    logger.info(test_message)

    assert log_file.exists()
    after = log_file.read_text()
    assert test_message in after and len(after) >= len(before)
