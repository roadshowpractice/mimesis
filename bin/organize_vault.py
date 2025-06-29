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
    logger.info("Processing: %s", json_path)
    try:
        with open(json_path, "r") as fh:
            data = json.load(fh)
    except Exception as exc:
        logger.error("Failed to load %s: %s", json_path, exc)
        return

    orig_path_str = data.get("original_filename") or data.get("to_process")
    if not orig_path_str:
        logger.debug("No original_filename or to_process in %s", json_path)
        return

    orig_path = Path(orig_path_str)
    if not orig_path.is_file():
        logger.debug("Original video file does not exist: %s", orig_path)
        return

    # Guess the watermarked version
    wm_path = orig_path.with_name(orig_path.stem + "_watermarked.mp4")
    if not wm_path.is_file():
        logger.debug("Watermarked video not found: %s", wm_path)
        return

    vault_dir = json_path.parent / "distro" / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    new_video = vault_dir / wm_path.name
    new_json = vault_dir / json_path.name

    try:
        shutil.move(str(wm_path), new_video)
        logger.info("Moved watermarked video: %s -> %s", wm_path, new_video)
        data["watermarked_file"] = str(new_video)
        with open(new_json, "w") as fh:
            json.dump(data, fh, indent=4)
        if json_path.resolve() != new_json.resolve():
            json_path.unlink(missing_ok=True)
        logger.info("Saved updated metadata: %s", new_json)
    except Exception as exc:
        logger.error("Failed to move/update for %s: %s", json_path, exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize watermark assets")
    parser.add_argument("collection", help="Path to top-level collection")
    args = parser.parse_args()

    base = Path(args.collection)
    for json_file in base.rglob("*.json"):
        process_metadata(json_file)


if __name__ == "__main__":
    main()
