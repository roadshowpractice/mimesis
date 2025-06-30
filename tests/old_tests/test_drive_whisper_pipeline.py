import io
import tarfile
import logging
from pathlib import Path
import types

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("yaml", types.SimpleNamespace())
sys.modules.setdefault(
    "speech_recognition", types.SimpleNamespace(Recognizer=object, AudioFile=object)
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

import codex_pipeline
from mimesis import archive as m_archive
from mimesis import video as m_video


URL = "https://drive.google.com/file/d/12rH-ul3Baj0H3UWPCqM8YitSosrjRFBM/view?usp=share_link"


def _make_tar(tmp_dir: Path) -> bytes:
    vid_path = tmp_dir / "dummy.mp4"
    vid_path.write_bytes(b"dummy video")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo(name="dummy.mp4")
        data = vid_path.read_bytes()
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    buf.seek(0)
    return buf.getvalue()


def test_drive_pipeline_logs(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    tar_bytes = _make_tar(tmp_path)

    class FakeResp:
        status_code = 200

        def iter_content(self, chunk_size=8192):
            yield tar_bytes

    monkeypatch.setattr(m_archive, "requests", types.SimpleNamespace(get=lambda *a, **k: FakeResp()))

    def fake_extract(*args, **kwargs):
        tar_path = Path(args[0])
        tar_path.write_bytes(tar_bytes)
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
            tf.extractall(tmp_path)
            return [str(tmp_path / m.name) for m in tf.getmembers()]

    monkeypatch.setattr(m_archive, "download_gdrive_file", lambda url, dest_path: str(tmp_path / "archive.tar"))
    monkeypatch.setattr(m_archive, "untar_archive", lambda tar_path, extract_dir: fake_extract(tar_path, extract_dir))
    monkeypatch.setattr(m_video, "extract_audio_from_video", lambda *a, **k: str(tmp_path / "audio.wav"))
    monkeypatch.setattr(codex_pipeline, "extract_audio_from_video", lambda *a, **k: str(tmp_path / "audio.wav"))

    class FakeModel:
        def transcribe(self, path, task=None, language=None):
            return {"text": "hello"}

    monkeypatch.setattr(codex_pipeline, "whisper", types.SimpleNamespace(load_model=lambda *a, **k: FakeModel()))

    codex_pipeline.process_drive_tar_and_transcribe(URL, str(tmp_path))

    assert any("Starting Google Drive download" in r.message for r in caplog.records)
    assert caplog.records
