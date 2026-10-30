#!/usr/bin/env python3
"""Tight rectangles around the FB-only overlay text (OCR word boxes), and a check that
FB differs from IG inside them and matches outside them. claude, 2026-10-30.
Reason (house rule 7): Opie's overlay_measure.py gives 5th/95th-percentile line boxes and fixed
hand-set stamp boxes, not per-text tight boxes; mimesis has no box step yet (banded hash in progress).
Dated one-off; inputs: Opie's ocr_raw_{fb,ig}.tsv (10-29) + the two held mp4s, read-only.
"""
import csv, json, statistics as st, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OCR = Path.home() / "Desktop/claude/2026-10-29/opencode/ldc_scenes_text"
V = {"ig": Path.home() / "boner_vault/dl_wm_outputs/2026-10-13/instagram__Decca9IB4mM/instagram__Decca9IB4mM.mp4",
     "fb": Path.home() / "boner_vault/dl_wm_outputs/2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"}
PAD = 4          # px around the OCR box (anti-aliased glyph edges)
CUT = 32.4       # last shared frame time; compare up to here

def kind(txt):
    t = txt.lower()
    if "gofundme" in t or "chad-replace" in t or "modal=donations" in t: return "url"
    if ("atterda" in t or "tterday" in t) and "-" not in t and "/" not in t: return "stamp"
    return None

def words(tag):
    out = []
    for r in csv.DictReader(open(OCR / f"ocr_raw_{tag}.tsv"), delimiter="\t"):
        k = kind(r["text"])
        if k and float(r["conf"]) >= 30:
            x, y, w, h = (int(r[c]) for c in ("left", "top", "width", "height"))
            if k == "stamp" and y > 1150: continue   # inside the link band: link fragment, not the stamp
            out.append((float(r["t"]), k, x, y, x + w, y + h, r["text"]))
    return out

fb, ig = words("fb"), words("ig")
# group: url = union of its words per frame; stamp = split by position (top-right vs left-middle)
per = {}
for t, k, x0, y0, x1, y1, _ in fb:
    if k == "stamp": k = "stamp_top_right" if x0 > 360 else "stamp_left_middle"
    b = per.setdefault(k, {}).setdefault(t, [x0, y0, x1, y1])
    b[:] = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
boxes = {}
for k, d in per.items():
    bs = list(d.values())
    med = [int(st.median(b[i] for b in bs)) for i in range(4)]
    boxes[k] = {"x0": med[0] - PAD, "y0": med[1] - PAD, "x1": med[2] + PAD, "y1": med[3] + PAD,
                "ocr_frames": len(bs), "t_first": min(d), "t_last": max(d)}

def frame(tag, t):
    p = HERE / "frames" / f"{tag}_{t:05.1f}.png"
    if not p.exists():
        p.parent.mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(V[tag]), "-frames:v", "1", str(p)], check=True)
    return np.asarray(Image.open(p).convert("L"), dtype=np.int16)

rows = []
for i in range(0, int(CUT * 2) + 1):
    t = i / 2
    a, b = frame("ig", t), frame("fb", t)
    d = np.abs(a - b)
    outside = np.ones(d.shape, bool)
    row = {"t": t}
    for k, bx in boxes.items():
        on = bx["t_first"] - 0.5 <= t <= bx["t_last"] + 0.5
        sl = d[bx["y0"]:bx["y1"], bx["x0"]:bx["x1"]]
        row[k] = round(float(sl.mean()), 1)
        row[k + "_on"] = int(on)
        outside[bx["y0"]:bx["y1"], bx["x0"]:bx["x1"]] = False
    row["outside"] = round(float(d[outside].mean()), 1)
    rows.append(row)

with open(HERE / "box_diff.tsv", "w") as f:
    w = csv.DictWriter(f, rows[0].keys(), delimiter="\t"); w.writeheader(); w.writerows(rows)
json.dump({"boxes": boxes, "pad_px": PAD, "ig_ocr_hits": len(ig), "frame_size": list(frame("fb", 0).shape[::-1])},
          open(HERE / "boxes.json", "w"), indent=1)

# picture: copy of an FB frame with the rectangles drawn (raw frame kept in frames/)
t = 5.0
im = Image.open(HERE / "frames" / f"fb_{t:05.1f}.png").convert("RGB")
dr = ImageDraw.Draw(im)
for k, bx in boxes.items():
    dr.rectangle([bx["x0"], bx["y0"], bx["x1"], bx["y1"]], outline=(255, 0, 0), width=3)
    dr.text((bx["x0"], bx["y0"] - 14), k, fill=(255, 0, 0))
im.save(HERE / f"2026-10-30_fb_text_boxes_t{t:04.1f}.png")
print(json.dumps(boxes, indent=1)); print("IG OCR hits for these texts:", len(ig))
