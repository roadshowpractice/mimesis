#!/usr/bin/env python3
"""Step 1b: watermark presence per FB frame from its white glyph pixels only (FB frames only, no IG).
Glyph mask = pixels >= 220 in the box at the frame where the watermark is there, and < 220 at the frame where it's away
(5.0 s vs 12.0 s). Score = share of glyph pixels >= 200 in each frame. claude 2026-10-30.
"""
import json, subprocess
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
FB = Path.home() / "boner_vault/dl_wm_outputs/2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"
W, H = 720, 1280
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(FB), "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
F = []
while (b := p.stdout.read(W * H)) and len(b) == W * H: F.append(np.frombuffer(b, np.uint8).reshape(H, W))
B = {"wm_top_right": ((518, 312, 670, 408), 150, 360), "wm_left_middle": ((50, 712, 200, 806), 360, 150)}
out = {}
for k, ((x0, y0, x1, y1), here, away) in B.items():
    g = (F[here][y0:y1, x0:x1] >= 220) & (F[away][y0:y1, x0:x1] < 220)
    ys, xs = np.nonzero(g)
    out[k] = {"glyph_px": int(g.sum()), "glyph_bbox": [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1)],
              "score": [round(float((f[y0:y1, x0:x1][g] >= 200).mean()), 3) for f in F]}
json.dump(out, open(HERE / "locate2_raw.json", "w"))
for k, v in out.items():
    s = np.array(v["score"]); print(k, "glyph px", v["glyph_px"], "bbox", v["glyph_bbox"], "score quantiles", np.round(np.percentile(s, [5, 25, 50, 75, 95]), 2))
    on = s >= 0.5; segs = []; i = 0
    while i < len(s):
        if on[i]:
            j = i
            while j + 1 < len(s) and on[j + 1]: j += 1
            segs.append((i, j)); i = j + 1
        else: i += 1
    print("  on (>=0.5):", [(a, b, f"{a/30:.3f}-{(b+1)/30:.3f}s") for a, b in segs])
    for a, b in segs[:6]:
        print("   edges", a, s[max(0,a-3):a+3].tolist(), b, s[b-2:b+4].tolist())
