#!/usr/bin/env python3
"""Step 1 (decide the boxes): find where and when the overlays sit in Tim's FB reel, from FB frames ONLY
(no Instagram pixels are read here). claude, 2026-10-30, for John ("3-d x, y, t" boxes).
Templates are cut from FB frames at 5.0 s (watermark top-right) and 12.0 s (watermark left-middle);
every FB frame (30 fps) is then searched in a window around each spot (normalised cross-correlation).
Reason (rule 7): no tool locates moving overlays per frame; text_boxes.py (same day) has fixed OCR boxes only.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2

HERE = Path(__file__).resolve().parent
FB = Path.home() / "boner_vault/dl_wm_outputs/2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"
W, H = 720, 1280
def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        yield np.frombuffer(b, np.uint8).reshape(H, W)
allf = list(frames(FB)); print("FB frames:", len(allf), file=sys.stderr)
f5, f12 = allf[150], allf[360]          # 5.0 s, 12.0 s
# watermark unit = IG logo + handle; template boxes (x0,y0,x1,y1) read off the 5.0/12.0 s crops by eye
T = {"wm_top_right":   (f5,  (518, 312, 670, 408)),
     "wm_left_middle": (f12, (50, 712, 200, 806)),
     "link":           (f5,  (72, 1196, 648, 1266))}
res = {}
for k, (src, (x0, y0, x1, y1)) in T.items():
    tpl = src[y0:y1, x0:x1].astype(np.float32)
    m = 24; sx0, sy0, sx1, sy1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
    rows = []
    for i, f in enumerate(allf):
        r = cv2.matchTemplate(f[sy0:sy1, sx0:sx1].astype(np.float32), tpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(r)
        rows.append((i, round(float(mx), 3), sx0 + loc[0] - x0, sy0 + loc[1] - y0))
    res[k] = {"box": [x0, y0, x1, y1], "rows": rows}
json.dump(res, open(HERE / "locate_raw.json", "w"))
for k, v in res.items():
    s = np.array([r[1] for r in v["rows"]])
    print(k, "score quantiles 5/25/50/75/95:", np.round(np.percentile(s, [5, 25, 50, 75, 95]), 2))
