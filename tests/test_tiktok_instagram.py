# Standard library imports
from pathlib import Path
import sys
import types
import logging

# Add helpers to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

# Provide a stub yt_dlp so downloader5 can be imported
sys.modules['yt_dlp'] = types.SimpleNamespace(YoutubeDL=object)
sys.modules['requests'] = types.SimpleNamespace()

import mimesis.downloader as downloader5
from mimesis.url import detect_host, sanitize_instagram_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIKTOK_URL = "https://www.tiktok.com/@radiocentro.ec/video/7518088749880757511?q=tim%20ballard&t=1750993266853"


def test_detect_as_instagram():
    assert detect_host(TIKTOK_URL) == "instagram"
    assert sanitize_instagram_url(TIKTOK_URL) == TIKTOK_URL


def test_download_with_stub(tmp_path, monkeypatch):
    logger.debug("I can see it in the debugger")
    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        def download(self, urls):
            out = self.opts.get("outtmpl")
            Path(out).write_text("fake video")

    monkeypatch.setattr(downloader5, "yt_dlp", types.SimpleNamespace(YoutubeDL=FakeYDL))

    target = tmp_path / "video.mp4"
    params = {
        "url": TIKTOK_URL,
        "original_filename": str(target),
        "video_download": {},
    }
    result = downloader5.download_video(params)
    assert result["to_process"] == str(target)
    assert target.exists()
