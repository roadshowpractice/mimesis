from pathlib import Path
import types
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib" / "python_utils"))

# Provide a stub yt_dlp so downloader5 can be imported without the real package
class _FakeYDL:
    def __init__(self, *a, **k):
        pass
    def download(self, urls):
        pass

sys.modules['yt_dlp'] = types.SimpleNamespace(YoutubeDL=_FakeYDL)
sys.modules['requests'] = types.SimpleNamespace()

import downloader5
import watermarker2


def test_download_and_watermark(tmp_path, monkeypatch):
    """Exercise downloader and watermark helpers with stubs."""

    # --- stub yt_dlp so no network access is needed ---
    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def download(self, urls):
            out = self.opts.get("outtmpl")
            Path(out).write_text("dummy video")

    monkeypatch.setattr(downloader5, "yt_dlp", types.SimpleNamespace(YoutubeDL=FakeYDL))

    target = tmp_path / "video.mp4"
    params = {
        "url": "https://example.com/video",
        "original_filename": str(target),
        "video_download": {},
    }
    result = downloader5.download_video(params)
    assert result["to_process"] == str(target)
    assert target.exists()

    wm_params = {"input_video_path": result["to_process"], "download_path": tmp_path}
    wm_result = watermarker2.add_watermark(wm_params)
    wm_path = Path(wm_result["to_process"])
    assert wm_path.exists()
