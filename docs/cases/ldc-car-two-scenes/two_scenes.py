#!/usr/bin/env python3
"""Two-scene comparison of the LDC basepoint pair with mimesis' own rules (00_PREREGISTRATION.md). claude 2026-10-29.
Reason (rule 7): mimesis compare_x_ig.py scores whole posts X-vs-IG; it has no scene split. This one-off imports its dhash/hamming/
tokens/shingles/longest_run and THRESHOLDS unchanged and applies them per scene. Lives in this dated folder.
Run from anywhere with the mimesis venv:  venv/bin/python docs/cases/ldc-car-two-scenes/two_scenes.py IG.mp4 FB.mp4 IG.txt FB.whisper.json OUTDIR"""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "bin"))  # mimesis/bin
from compare_x_ig import THRESHOLDS, dhash, hamming, tokens, shingles, longest_run, sha256_file  # noqa: E402

ig, fb, igtxt, fbjson, out = sys.argv[1:6]
out = Path(out); (out / "frames").mkdir(parents=True, exist_ok=True)
EVERY, CUT, N = THRESHOLDS["frame_every_s"], 32.48, THRESHOLDS["shingle_n"]


def grab(video, tag):
    d = out / "frames" / tag; d.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-vf", f"fps=1/{EVERY}", str(d / "f_%04d.png")], check=True)
    return [(i * EVERY, dhash(p)) for i, p in enumerate(sorted(d.glob("f_*.png")))]


def img_class(d):
    return "IDENTICAL" if d <= THRESHOLDS["img_identical"] else ("SAME MATERIAL" if d <= THRESHOLDS["img_near"] else "NOTHING SHARED")


def text_class(a, b):
    sa, sb = shingles(a, N), shingles(b, N)
    jac = len(sa & sb) / len(sa | sb) if sa | sb else 0.0
    run = longest_run(a, b)
    cls = ("IDENTICAL" if jac >= THRESHOLDS["shingle_jaccard_identical"] else
           "SAME MATERIAL" if run >= THRESHOLDS["common_run_material"] or len(sa & sb) >= THRESHOLDS["shared_shingles_material"] else "NOTHING SHARED")
    return {"words": len(b), "shingle_jaccard": round(jac, 3), "shared_shingles": len(sa & sb), "longest_run": run, "class": cls}


IGF, FBF = grab(ig, "ig"), grab(fb, "fb")
w = json.load(open(fbjson))
fbwords = [(x["start"], x["word"]) for s in w["segments"] for x in s.get("words", [])]
igw = tokens(open(igtxt).read())
res = {"inputs": {Path(p).name: sha256_file(p) for p in (ig, fb, igtxt, fbjson)}, "thresholds": THRESHOLDS, "every_s": EVERY, "cut_s": CUT}
for name, sel in (("S1", lambda t: t < CUT), ("S2", lambda t: t >= CUT)):
    rows = []
    for t, h in FBF:
        if not sel(t): continue
        if name == "S1":
            same = min(IGF, key=lambda x: abs(x[0] - t)); d_same = hamming(h, same[1])
        nearest = min(IGF, key=lambda x: hamming(h, x[1])); d_near = hamming(h, nearest[1])
        rows.append({"fb_t": t, **({"ig_t_same": same[0], "d_same_time": d_same} if name == "S1" else {}),
                     "ig_t_nearest": nearest[0], "d_nearest": d_near})
    key = "d_same_time" if name == "S1" else "d_nearest"
    counts = {}
    for r in rows: c = img_class(r[key]); counts[c] = counts.get(c, 0) + 1
    words = tokens(" ".join(wd for st, wd in fbwords if sel(st)))
    res[name] = {"frames": len(rows), "image_classes": counts, "image_scene_class": max(counts, key=counts.get) if counts else None,
                 "text": text_class(igw, words), "rows": rows}
json.dump(res, open(out / "result.json", "w"), indent=1)
for name in ("S1", "S2"):
    r = res[name]
    print(name, "frames", r["frames"], "image classes", r["image_classes"], "->", r["image_scene_class"], "| text", r["text"])
    print("   distances:", [(x["fb_t"], x.get("d_same_time", x["d_nearest"])) for x in r["rows"]])
