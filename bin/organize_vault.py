#!/usr/bin/env python3
"""Move watermarked videos (from `add_watermark` task) and update JSON metadata."""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path


def setup_logging(verbose: bool) -> logging.Logger:
    logger = logging.getLogger("organize_vault")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def process_json(json_path: Path, logger: logging.Logger) -> None:
    logger.debug(f"Processing: {json_path}")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"Skipping {json_path.name}: can't parse JSON ({e})")
        return

    tasks = data.get("default_tasks", {})
    value = tasks.get("add_watermark")

    if not isinstance(value, str):
        logger.debug(f"Skipping: 'add_watermark' not a path in {json_path.name}")
        return

    wm_path = Path(value)
    if not wm_path.is_absolute():
        wm_path = json_path.parent / wm_path

    if not wm_path.is_file():
        logger.warning(f"Skipping: File not found - {wm_path}")
        return

    vault_dir = json_path.parent / "distro" / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    new_video_path = vault_dir / wm_path.name
    new_json_path = vault_dir / json_path.name

    try:
        shutil.move(str(wm_path), new_video_path)
        logger.info(f"Moved video: {wm_path} → {new_video_path}")
        tasks["add_watermark"] = str(new_video_path)
        data["default_tasks"] = tasks

        with open(new_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        if json_path.resolve() != new_json_path.resolve():
            json_path.unlink(missing_ok=True)

        logger.info(f"Updated metadata: {new_json_path}")
    except Exception as e:
        logger.error(f"Error moving/updating {json_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Organize watermarked videos into vault")
    parser.add_argument("collection", help="Top-level directory to scan for JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    logger = setup_logging(args.verbose)
    collection_dir = Path(args.collection)

    if not collection_dir.is_dir():
        logger.error(f"Directory does not exist: {collection_dir}")
        sys.exit(1)

    json_files = list(collection_dir.rglob("*.json"))
    if not json_files:
        logger.warning("No JSON files found.")
        return

    for json_file in json_files:
        process_json(json_file, logger)


if __name__ == "__main__":
    main()
