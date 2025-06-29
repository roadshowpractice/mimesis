# Moved from watermarker2.py

import os
import shutil
from pathlib import Path
import logging

def add_watermark(params: dict) -> dict:
    """A lightweight stand-in for video watermarking.

    This helper avoids heavy video processing dependencies. It simply
    copies the input video to a new file with a ``_wm`` suffix and
    returns the path to that new file.

    Parameters expected in ``params``:
        - ``input_video_path`` (str): path to the source video file.
        - ``download_path`` (str, optional): directory for the output file.

    Returns:
        dict: ``{"to_process": <output_path>}`` when successful.
    """
    logger = logging.getLogger(__name__)

    input_video = params.get("input_video_path")
    if not input_video or not os.path.isfile(input_video):
        logger.error("Input video missing for watermarking")
        return {"to_process": None}

    output_dir = params.get("download_path") or os.path.dirname(input_video)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    stem = Path(input_video).stem
    output_path = os.path.join(output_dir, f"{stem}_wm.mp4")

    try:
        shutil.copy(input_video, output_path)
        logger.info(f"Watermarked video created: {output_path}")
        return {"to_process": output_path}
    except Exception as exc:
        logger.error(f"Failed to create watermarked copy: {exc}")
        return {"to_process": None}
