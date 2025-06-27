from pathlib import Path
import json
import pytest

# Import directly — no sys.path hacks needed
from lib import initialize_logging

# Setup logging
logger = initialize_logging()
logger.info("Test session started.")

def _load_inputs():
    input_path = Path(__file__).parent / "inputs" / "task_aware_video_inputs.json"
    assert input_path.exists(), f"Missing input file: {input_path}"
    with input_path.open(encoding="utf-8") as fh:
        return json.load(fh)

@pytest.mark.parametrize("task_entry", _load_inputs())
def test_task_queue_entry(task_entry):
    logger.info(f"Testing task for: {task_entry['url']}")

    required_keys = {"url", "title", "date", "tasks"}
    assert required_keys.issubset(task_entry.keys())

    assert task_entry["url"].startswith(("http://", "https://"))

    expected_flags = [
        "perform_download",
        "apply_watermark",
        "make_clips",
        "extract_audio",
        "generate_captions",
        "post_process",
    ]
    for flag in expected_flags:
        assert flag in task_entry["tasks"]
        assert isinstance(task_entry["tasks"][flag], bool)

    logger.info(f"✅ Valid task for: {task_entry['title']}")

