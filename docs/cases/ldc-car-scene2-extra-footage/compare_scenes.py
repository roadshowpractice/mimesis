#!/usr/bin/env python3
"""LDC car FB reel 1653357746398669: does scene 2 (added footage, frames 973-2070) reuse any frame of scene 1 (frames 0-972)?
Every scene-2 frame vs every scene-1 frame, banded dHash (mimesis compare_x_ig.band_hashes, imported unchanged).
Match = 2 or 3 of 3 bands <= 6 (John 2026-10-30); 3/3 with whole <= 6 = IDENTICAL.
Retest first: IG Decca9IB4mM frames 0-972 vs FB scene 1 (same reel, known answer) must match frame for frame.
Usage: python compare_scenes.py FB.mp4 IG.mp4   (writes summary.json + scene2_nearest_scene1.tsv in the current folder)
Reason for a one-off (rule 7): compare_x_ig pairs posts across accounts; still_in_video slides stills (slow, no bands);
neither does all-pairs frame-to-frame between two scenes. claude, 2026-10-30, for John."""
import json, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "bin"))
from compare_x_ig import band_hashes

FB = sys.argv[1]   # Tim Ballard FB reel 1653357746398669 (mp4, sha256 in SHA256SUMS)
IG = sys.argv[2]   # latterdaychad IG reel Decca9IB4mM (mp4, sha256 in SHA256SUMS)
W, H, CUT = 180, 320, 973

def frames(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}", "-pix_fmt", "gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W)

def hashes(fr):   # rows: whole, top, middle, bottom as 64-bit ints
    out = []
    for f in fr:
        w, b = band_hashes(Image.fromarray(f))
        out.append([int(str(x), 16) if not isinstance(x, int) else x for x in (w, b["top"], b["middle"], b["bottom"])])
    return np.array(out, dtype=np.uint64)

def dist(a, B):  # Hamming distance of one row a against every row of B, per column
    x = np.bitwise_xor(B, a)
    return np.unpackbits(x.view(np.uint8).reshape(len(B), 4, 8), axis=2).sum(axis=2)

fb, ig = frames(FB), frames(IG)
print("frames: FB", len(fb), "IG", len(ig))
hf, hi = hashes(fb), hashes(ig)
s1, s2 = hf[:CUT], hf[CUT:]

# retest: IG frame i vs FB frame i (same reel; Tim's overlays sit in some bands, so 2-of-3 is the expected floor)
n = min(CUT, len(hi)); rt = np.array([dist(hi[i], s1[i:i+1])[0] for i in range(n)])
rt_ok = int(((rt[:, 1:] <= 6).sum(axis=1) >= 2).sum())
print(f"retest IG vs FB scene 1, same index: {rt_ok}/{n} frames match 2-of-3 bands")

rows = []
for j, a in enumerate(s2):
    d = dist(a, s1); nb = (d[:, 1:] <= 6).sum(axis=1)
    k = int(np.lexsort((d[:, 0], -nb))[0])        # most bands passing, then smallest whole
    rows.append((CUT + j, k, int(nb[k]), *map(int, d[k]), float(np.abs(fb[CUT + j].astype(int) - fb[k]).mean())))
with open("scene2_nearest_scene1.tsv", "w") as f:
    f.write("scene2_frame\tnearest_scene1_frame\tbands_ok\twhole\ttop\tmiddle\tbottom\tmean_abs_diff\n")
    for r in rows: f.write("\t".join(map(str, r)) + "\n")
nb = np.array([r[2] for r in rows]); whole = np.array([r[3] for r in rows])
summ = {"scene1_frames": CUT, "scene2_frames": len(s2), "retest_match_2of3": f"{rt_ok}/{n}",
        "scene2_frames_3of3": int((nb == 3).sum()), "scene2_frames_2of3": int((nb == 2).sum()),
        "scene2_frames_identical": int(((nb == 3) & (whole <= 6)).sum()),
        "best_whole": int(whole.min()), "median_best_whole": float(np.median(whole))}
json.dump(summ, open("summary.json", "w"), indent=1); print(json.dumps(summ, indent=1))
