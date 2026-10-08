import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("cxi", Path(__file__).resolve().parent.parent / "bin" / "compare_x_ig.py")
cxi = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cxi)


def _x(case, tid, text, created, urls=()):
    d = {"id_str": tid, "text": text, "created_at": created,
         "entities": {"urls": [{"expanded_url": u} for u in urls], "user_mentions": [], "hashtags": []}}
    p = case / "x" / "raw" / (tid + ".json")
    p.write_text(json.dumps(d))
    cxi.custody(case, "test", "x", p)


def _case(tmp_path, ig_posts):
    case = tmp_path / "case"
    for d in ("x/raw", "x/media", "ig/capture", "ig/media", "out"):
        (case / d).mkdir(parents=True)
    p = case / "ig" / "capture" / "posts.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in ig_posts))
    cxi.custody(case, "test", "ig", p)
    return case


def _run(case):
    cxi.main(["compare", str(case), "--account", "acct"])
    rows = (case / "out" / "pairs.csv").read_text().splitlines()
    return {(r.split(",")[0], r.split(",")[3]): r.split(",")[8] for r in rows[1:]}


def test_classes(tmp_path):
    shared = "the quick brown fox jumps over the lazy dog near the old mill today"
    case = _case(tmp_path, [
        {"code": "A", "owner": "acct", "taken_at": 1786500000, "caption": shared},
        {"code": "B", "owner": "acct", "taken_at": 1786500000, "caption": "see https://example.org/report here",
         "collaborators": []},
        {"code": "C", "owner": "acct", "taken_at": 1786500000,
         "caption": "sigmachi hazing bohemian fraternity rituals"},
    ])
    _x(case, "1", shared, "2026-08-11T22:00:00.000Z")
    _x(case, "2", "read this", "2026-08-11T22:00:00.000Z", urls=["https://example.org/report?utm_source=x"])
    _x(case, "3", "sigmachi hazing bohemian fraternity talk", "2026-08-11T22:00:00.000Z")
    _x(case, "4", "nothing in common at all whatsoever", "2026-08-11T22:00:00.000Z")
    got = _run(case)
    assert got[("A", "1")] == "IDENTICAL"
    assert got[("B", "2")] == "IDENTICAL"          # same link after normalizing
    assert got[("C", "3")] == "TOPIC ONLY"
    assert got[("A", "4")] == "NOTHING SHARED"
    assert (case / "out" / "manifest.json").exists()


def test_stops_if_input_changed(tmp_path):
    case = _case(tmp_path, [{"code": "A", "owner": "acct", "taken_at": 1786500000, "caption": "x"}])
    _x(case, "1", "hello", "2026-08-11T22:00:00.000Z")
    (case / "x" / "raw" / "1.json").write_text("{}")   # tamper after logging
    with pytest.raises(SystemExit):
        cxi.main(["compare", str(case), "--account", "acct"])
    assert "STOPPED" in (case / "CUSTODY.log").read_text()


def test_dhash_same_and_different(tmp_path):
    from PIL import Image, ImageDraw
    a = Image.new("RGB", (200, 200), "white")
    ImageDraw.Draw(a).rectangle([20, 20, 120, 160], fill="black")
    b = a.resize((400, 400))
    c = Image.new("RGB", (200, 200), "white")
    ImageDraw.Draw(c).ellipse([100, 10, 190, 90], fill="black")
    assert cxi.hamming(cxi.dhash(a), cxi.dhash(b)) <= 6
    assert cxi.hamming(cxi.dhash(a), cxi.dhash(c)) > 12


def test_x_token_shape():
    t = cxi.x_token("2087324891087286284")
    assert t and "." not in t and "0" not in t


def test_files_inventory_finds_identical_and_durations(tmp_path):
    import subprocess
    case = _case(tmp_path, [{"code": "A", "owner": "acct", "taken_at": 1786500000, "caption": "x"}])
    vid = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=3:size=160x120:rate=10",
                    "-pix_fmt", "yuv420p", str(vid)], check=True)
    other = tmp_path / "w.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=7:size=160x120:rate=10",
                    "-pix_fmt", "yuv420p", str(other)], check=True)
    (case / "ig" / "media" / "A").mkdir(parents=True)
    for dst in (case / "x" / "media" / "111_0.mp4", case / "ig" / "media" / "A" / "A.mp4"):
        dst.write_bytes(vid.read_bytes())
        cxi.custody(case, "test", "media", dst)
    dst = case / "x" / "media" / "222_0.mp4"
    dst.write_bytes(other.read_bytes())
    cxi.custody(case, "test", "media", dst)
    cxi.main(["files", str(case)])
    rep = (case / "out" / "files_report.md").read_text()
    assert "Byte-identical files on both sides: **1**" in rep
    assert "same duration (within 0.5s): **1**" in rep
    assert (case / "out" / "files.csv").read_text().count("\n") == 4
