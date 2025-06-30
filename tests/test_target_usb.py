import json
import platform
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

from mimesis.video import load_app_config


def test_target_usb_loaded_correctly():
    config = load_app_config()
    system = platform.system()
    config_path = Path(__file__).resolve().parents[1] / "conf" / "config.json"
    expected = None
    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
            expected = data.get(system, {}).get("target_usb")
    assert "target_usb" in config
    assert expected is None or config["target_usb"] == expected
