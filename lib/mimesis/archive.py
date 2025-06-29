# Moved from archive_utils.py

import logging
import os
import tarfile
import re
import requests
from url_utils import detect_host

logger = logging.getLogger(__name__)

_GDRIVE_RE = re.compile(r"(?:/file/d/|id=)([\w-]{10,})")


def _extract_gdrive_id(url: str) -> str | None:
    """Extract file ID from various Google Drive URL patterns."""
    m = _GDRIVE_RE.search(url)
    return m.group(1) if m else None


def download_gdrive_file(url: str, dest_path: str) -> str:
    """Download a file from Google Drive to ``dest_path``."""
    file_id = _extract_gdrive_id(url)
    if not file_id:
        raise ValueError(f"Could not parse Google Drive ID from {url}")
    dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    logger.info("Downloading from %s", dl_url)
    resp = requests.get(dl_url, stream=True)
    if resp.status_code != 200:
        raise RuntimeError(f"Download failed with status {resp.status_code}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)
    logger.info("Saved %s", dest_path)
    return dest_path


def untar_archive(tar_path: str, extract_dir: str) -> list[str]:
    """Extract ``tar_path`` into ``extract_dir`` and return list of files."""
    logger.info("Extracting %s to %s", tar_path, extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    files = []
    with tarfile.open(tar_path, "r:*") as tf:
        tf.extractall(path=extract_dir)
        files = [os.path.join(extract_dir, m.name) for m in tf.getmembers() if m.isfile()]
    logger.info("Extracted %d files", len(files))
    return files


def handle_gdrive_tar(params: dict) -> dict:
    """Download a Google Drive tar archive and extract it."""
    url = params.get("url")
    download_path = params.get("download_path", ".")
    tar_dest = os.path.join(download_path, "archive.tar")
    extracted_dir = os.path.join(download_path, "extracted")

    host = detect_host(url)
    if host != "google_drive":
        raise ValueError("URL is not recognized as Google Drive")

    downloaded = download_gdrive_file(url, tar_dest)
    files = untar_archive(downloaded, extracted_dir)

    return {"archive_path": downloaded, "extracted": files}
