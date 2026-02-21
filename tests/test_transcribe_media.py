import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "bin" / "transcribe_media.py"
SPEC = importlib.util.spec_from_file_location("transcribe_media", SCRIPT_PATH)
transcribe_media = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(transcribe_media)


def test_resolve_source_url_from_jsonl_fixture(tmp_path):
    fixture = Path(__file__).resolve().parents[0] / "inputs" / "whisper_index_fixture.jsonl"
    media = tmp_path / "clip_CODEX12345.mp4"
    media.write_bytes(b"fake")

    source_url = transcribe_media.resolve_source_url(media.resolve(), [str(fixture)])

    assert source_url == "https://www.instagram.com/reel/CODEX12345/"


def test_no_metadata_skips_jsonl_and_writes_null_source(monkeypatch, tmp_path):
    media = tmp_path / "input.wav"
    media.write_bytes(b"wave")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("resolve_source_url should not be called when --no-metadata is set")

    monkeypatch.setattr(transcribe_media, "ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr(transcribe_media, "resolve_source_url", fail_if_called)
    monkeypatch.setattr(
        transcribe_media,
        "run_whisper",
        lambda *_args, **_kwargs: {
            "text": "hello world",
            "segments": [{"start": 0.0, "end": 1.0, "text": "hello world"}],
        },
    )

    exit_code = transcribe_media.main(
        [str(media), "--no-metadata", "--jsonl", str(tmp_path / "missing.jsonl")]
    )
    assert exit_code == 0

    manifest_path = tmp_path / "input.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_url"] is None
