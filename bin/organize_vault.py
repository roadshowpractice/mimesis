#!/usr/bin/env python3
"""Organize watermarked videos and metadata into a central vault.

This utility searches a collection directory for metadata JSON files. If the
metadata specifies a path for a completed watermark task and that file exists,
the video and its JSON are moved into a ``distro/vault`` directory under the
same collection date. The JSON is updated to reflect the new location.
"""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path

# Add local ``lib`` to ``sys.path`` so we can reuse helpers
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(CURRENT_DIR, "../lib")
sys.path.append(LIB_PATH)

from video_utils import initialize_logging  # type: ignore

logger = initialize_logging()


def process_metadata(json_path: Path) -> None:
    """Move watermarked video referenced in ``json_path`` to the vault."""
    try:
        with open(json_path, "r") as fh:
            data = json.load(fh)
    except Exception as exc:
        logger.error("Failed to load %s: %s", json_path, exc)
        return

    tasks = data.get("default_tasks", {})
    wm_key = None
    video_path = None
    for key in ("add_watermark", "apply_watermark"):
        val = tasks.get(key)
        if isinstance(val, str):
            wm_key = key
            video_path = Path(val)
            break

    if wm_key and video_path and video_path.is_file():
        vault_dir = json_path.parent / "distro" / "vault"
        vault_dir.mkdir(parents=True, exist_ok=True)
        new_video = vault_dir / video_path.name
        if video_path.resolve() != new_video.resolve():
            try:
                shutil.move(str(video_path), new_video)
                logger.info("Moved %s -> %s", video_path, new_video)
            except Exception as exc:
                logger.error("Could not move %s: %s", video_path, exc)
                return
        tasks[wm_key] = str(new_video)
        data["default_tasks"] = tasks
        new_json = vault_dir / json_path.name
        try:
            with open(new_json, "w") as fh:
                json.dump(data, fh, indent=4)
            if json_path.resolve() != new_json.resolve():
                json_path.unlink(missing_ok=True)
            logger.info("Updated metadata saved to %s", new_json)
        except Exception as exc:
            logger.error("Failed to write updated JSON: %s", exc)
    else:
        logger.debug("No watermarked video to move for %s", json_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize watermark assets")
    parser.add_argument("collection", help="Path to top-level collection")
    args = parser.parse_args()

    base = Path(args.collection)
    for json_file in base.rglob("*.json"):
        process_metadata(json_file)


if __name__ == "__main__":
    main()
