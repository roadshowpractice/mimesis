import io
import tarfile
from pathlib import Path
import logging
import pytest
import types

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))
sys.modules.setdefault("requests", types.SimpleNamespace())

import mimesis.archive as archive_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GDRIVE_URL = "https://drive.google.com/file/d/1-POht303zzZVyMmSlejvH0LPBjCuTd03/view?usp=drive_link"


def _make_tar_bytes():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo(name="hello.txt")
        data = b"hello world"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    buf.seek(0)
    return buf.getvalue()


def test_download_and_extract_success(tmp_path, monkeypatch):
    tar_bytes = _make_tar_bytes()

    class FakeResp:
        status_code = 200
        def iter_content(self, chunk_size=8192):
            yield tar_bytes

    def fake_get(url, stream=True):
        return FakeResp()

    monkeypatch.setattr(archive_utils, "requests", types.SimpleNamespace(get=fake_get))

    params = {"url": GDRIVE_URL, "download_path": str(tmp_path)}
    result = archive_utils.handle_gdrive_tar(params)
    saved = Path(result["archive_path"])
    assert saved.exists()
    extracted = result["extracted"]
    assert len(extracted) == 1
    assert Path(extracted[0]).read_text() == "hello world"


def test_download_failure(tmp_path, monkeypatch):
    class BadResp:
        status_code = 404
        def iter_content(self, chunk_size=8192):
            return []
    monkeypatch.setattr(
        archive_utils,
        "requests",
        types.SimpleNamespace(get=lambda url, stream=True: BadResp()),
    )

    params = {"url": GDRIVE_URL, "download_path": str(tmp_path)}
    with pytest.raises(RuntimeError):
        archive_utils.handle_gdrive_tar(params)
