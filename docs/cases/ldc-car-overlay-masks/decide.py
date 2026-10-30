#!/usr/bin/env python3
"""DECIDE THE MASKS (x, y, t) from Tim's FB frames ONLY; no Instagram pixel is read here. claude, 2026-10-30.
John: "define a rectangle around the logo as it appears ... first decide where and when ... 3-d x, y, t";
"we want the smallest convex set we can find ... it's a choice, so we can make a good one."
Choice made:
 - shapes: one convex hull per added piece (IG logo, @handle, link banner), not one box for all; each hull grown by
   GROW px (anti-aliased edges / soft shadow);
 - logo & handle: glyph pixels = white (>=220) at the left-middle spot at 12.0 s and not white there at 5.0 s (plain asphalt
   behind); split into logo / handle at the widest empty band of rows; the same glyphs are shifted to the top-right spot by
   template match on the 5.0 s frame (one shift per piece: the layout differs between spots);
 - link: banner = dark (<=60) or white (>=220) pixels in y >= 1150 at frame 30 that were not so at frame 20; hull;
 - time: a piece is "on" in a frame if its glyph contrast (mean glyph px - mean of a 4-px ring around them) >= CON;
   each on-span is then widened by TPAD frames each side to catch the fade ends. Only frames 0..972 (the shared part) matter.
Output: masks.json (hull polygons + frame spans) and masks.npz (the per-piece pixel masks). These are frozen before compare.py.
"""
import json, subprocess
from pathlib import Path
import numpy as np, cv2
HERE = Path(__file__).resolve().parent
FB = Path.home() / "boner_vault/dl_wm_outputs/2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"
W, H, LAST = 720, 1280, 972
GROW, CON, TPAD = 3, 25, 3
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(FB), "-frames:v", str(LAST + 1), "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
F = []
while (b := p.stdout.read(W * H)) and len(b) == W * H: F.append(np.frombuffer(b, np.uint8).reshape(H, W))
F = np.stack(F); assert len(F) == LAST + 1

def hull_mask(pts):
    m = np.zeros((H, W), np.uint8); h = cv2.convexHull(pts.astype(np.int32)); cv2.fillConvexPoly(m, h, 1)
    if GROW: m = cv2.dilate(m, np.ones((2 * GROW + 1, 2 * GROW + 1), np.uint8))
    return m.astype(bool), h.reshape(-1, 2).tolist()

pieces = {}
# glyphs measured at the left-middle spot (plain asphalt behind them): white at 12.0 s, not white at 5.0 s
x0, y0, x1, y1 = 50, 712, 200, 806
g = np.zeros((H, W), bool)
g[y0:y1, x0:x1] = (F[360][y0:y1, x0:x1] >= 220) & (F[150][y0:y1, x0:x1] < 220)
ys, xs = np.nonzero(g)
rows = np.unique(ys); gap = int(np.argmax(np.diff(rows)))              # logo above, handle below: widest empty band of rows
split = rows[gap]
for part, sel in (("logo", ys <= split), ("handle", ys > split)):
    glyph = np.zeros((H, W), bool); glyph[ys[sel], xs[sel]] = True
    gy, gx = np.nonzero(glyph)
    m, poly = hull_mask(np.c_[gx, gy])
    pieces[f"{part}_left_middle"] = {"mask": m, "glyph": glyph, "poly": poly}
    # same artwork at the top-right spot: find its shift on the 5.0 s frame by template match in a search window
    bx0, by0, bx1, by1 = gx.min() - 2, gy.min() - 2, gx.max() + 3, gy.max() + 3
    tpl = F[360][by0:by1, bx0:bx1].astype(np.float32)
    sx0, sy0, sx1, sy1 = 480, 290, 720, 420
    r = cv2.matchTemplate(F[150][sy0:sy1, sx0:sx1].astype(np.float32), tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(r)
    dx, dy = sx0 + loc[0] - bx0, sy0 + loc[1] - by0
    tg = np.zeros((H, W), bool); tg[gy + dy, gx + dx] = True
    m, poly = hull_mask(np.c_[gx + dx, gy + dy])
    pieces[f"{part}_top_right"] = {"mask": m, "glyph": tg, "poly": poly, "shift": [int(dx), int(dy)], "match": round(float(score), 3)}
d = (((F[30] <= 60) | (F[30] >= 220)) & ~((F[20] <= 60) | (F[20] >= 220))); d[:1150] = False
d = cv2.morphologyEx(d.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
ys, xs = np.nonzero(d); m, poly = hull_mask(np.c_[xs, ys])
pieces["link_banner"] = {"mask": m, "glyph": d, "poly": poly}

def contrast(glyph):
    ring = cv2.dilate(glyph.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~glyph
    return F[:, glyph].mean(1) - F[:, ring].mean(1)
def spans(on):
    s, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j + 1 < len(on) and on[j + 1]: j += 1
            s.append([max(0, i - TPAD), min(LAST, j + TPAD)]); i = j + 1
        else: i += 1
    out = []                                   # merge spans that touch after padding
    for a, b in s:
        if out and a <= out[-1][1] + 1: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out
J = {"rule": __doc__, "params": {"GROW": GROW, "CON": CON, "TPAD": TPAD, "last_shared_frame": LAST}, "pieces": {}}
for k, v in pieces.items():
    c = contrast(v["glyph"])
    on = np.abs(c) >= CON                      # dark banner: contrast is negative
    J["pieces"][k] = {"hull": v["poly"], "shift_from_left_middle": v.get("shift"), "match": v.get("match"), "area_px": int(v["mask"].sum()), "frame_spans": spans(on),
                      "contrast_q05_50_95": np.round(np.percentile(c, [5, 50, 95]), 1).tolist()}
# one watermark, one fade: logo and handle at a spot share the union of their spans
for spot in ("top_right", "left_middle"):
    u = []
    for x, y in sorted(iv for k in (f"logo_{spot}", f"handle_{spot}") for iv in J["pieces"][k]["frame_spans"]):
        if u and x <= u[-1][1] + 1: u[-1][1] = max(u[-1][1], y)
        else: u.append([x, y])
    for k in (f"logo_{spot}", f"handle_{spot}"): J["pieces"][k]["frame_spans"] = [[max(0, a), min(LAST, b)] for a, b in u]
np.savez_compressed(HERE / "masks.npz", **{k: v["mask"] for k, v in pieces.items()})
json.dump(J, open(HERE / "masks.json", "w"), indent=1)
for k, v in J["pieces"].items():
    print(k, "area", v["area_px"], "contrast", v["contrast_q05_50_95"], "spans", [(a, b, f"{a/30:.2f}-{(b+1)/30:.2f}s") for a, b in v["frame_spans"]])
