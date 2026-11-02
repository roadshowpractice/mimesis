#!/usr/bin/env python3
"""Is FB 1653357746398669 scene 2 (frames 973-2070) LDC's IG reel DeaBysIPTSx ("here I am at work")?
Same fingerprints and rule as mimesis docs/cases/ldc-car-scene2-extra-footage/compare_scenes.py (band_hashes unchanged,
grey 180x320, match = 2 or 3 of 3 bands <= 6). Scan offsets, then report matches at the best one.
Retest first (known answer): IG Decca9IB4mM vs FB scene 1 same index must give 968/973.
Reason for a one-off (rule 7): compare_scenes.py compares the two scenes inside one file; this lines up a third file
by offset. Its frames/hashes/dist code is copied here unchanged. claude, 2026-11-01."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path.home() / "Documents/repos/mimesis/bin"))
from compare_x_ig import band_hashes
V = Path.home() / "boner_vault/dl_wm_outputs"
FB = V / "2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"
B = V / "2026-10-13/instagram__Decca9IB4mM/instagram__Decca9IB4mM.mp4"
A = V / "2026-10-13/instagram__DeaBysIPTSx/instagram__DeaBysIPTSx.mp4"
W, H, CUT = 180, 320, 973
def frames(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H}", "-pix_fmt", "gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W)
def hashes(fr):
    out = []
    for f in fr:
        w, b = band_hashes(Image.fromarray(f))
        out.append([int(str(x), 16) if not isinstance(x, int) else x for x in (w, b["top"], b["middle"], b["bottom"])])
    return np.array(out, dtype=np.uint64)
def pairdist(X, Y):  # row-wise Hamming per column, X and Y same length
    x = np.bitwise_xor(X, Y)
    return np.unpackbits(x.view(np.uint8).reshape(len(X), 4, 8), axis=2).sum(axis=2)
ok = lambda d: (d[:, 1:] <= 6).sum(axis=1) >= 2
hf, hb, ha = hashes(frames(FB)), hashes(frames(B)), hashes(frames(A))
print("frames FB", len(hf), "B", len(hb), "A", len(ha))
n = min(CUT, len(hb)); rt = int(ok(pairdist(hb[:n], hf[:n])).sum()); print(f"retest B vs FB scene 1: {rt}/{n}")
s2 = hf[CUT:]
scan = []
for off in range(-150, 151):   # FB scene-2 frame j  <->  A frame j + off
    j0, j1 = max(0, -off), min(len(s2), len(ha) - off)
    if j1 - j0 < 200: continue
    m = ok(pairdist(s2[j0:j1], ha[j0 + off:j1 + off]))
    scan.append((off, int(m.sum()), j1 - j0))
best = max(scan, key=lambda r: r[1] / r[2]); off = best[0]
j0, j1 = max(0, -off), min(len(s2), len(ha) - off)
d = pairdist(s2[j0:j1], ha[j0 + off:j1 + off]); m = ok(d)
zero = [r for r in scan if r[0] == 0][0]
unmatched = [int(CUT + j0 + i) for i in np.where(~m)[0]]
summ = {"retest_B_vs_FB_scene1": f"{rt}/{n}", "frames_FB": len(hf), "frames_A": len(ha), "frames_FB_scene2": len(s2),
        "best_offset_frames": off, "best_offset_s": round(off / 30, 3), "compared": j1 - j0, "match_2of3": int(m.sum()),
        "match_3of3": int(((d[:, 1:] <= 6).sum(axis=1) == 3).sum()), "offset0_match": f"{zero[1]}/{zero[2]}",
        "FB_scene2_frames_covered": f"{CUT + j0}-{CUT + j1 - 1}", "A_frames_used": f"{j0 + off}-{j1 + off - 1}",
        "unmatched_FB_frames_first20": unmatched[:20], "unmatched_count": len(unmatched)}
json.dump(summ, open("summary.json", "w"), indent=1)
open("offset_scan.tsv", "w").write("offset\tmatch\tcompared\n" + "".join(f"{a}\t{b}\t{c}\n" for a, b, c in scan))
print(json.dumps(summ, indent=1))

# --- bottom third only (added 2026-11-01 after the first run: A carries a big caption over the top and middle thirds,
# so 2-of-3 cannot pass). Every FB scene-2 frame vs every A frame, bottom band <= 6 bits. Control: same test, FB scene 1
# vs Decca9IB4mM at the same index (known same footage).
def hd(a, B): return np.unpackbits(np.bitwise_xor(B, a).view(np.uint8).reshape(len(B), 8), axis=1).sum(axis=1)
ctrl = int((np.array([hd(hb[i, 3], hf[i:i+1, 3])[0] for i in range(n)]) <= 6).sum())
best = np.array([hd(a, ha[:, 3]).min() for a in s2[:, 3]]); arg = np.array([int(hd(a, ha[:, 3]).argmin()) for a in s2[:, 3]])
bot = {"control_bottom_only_B_vs_FB_scene1": f"{ctrl}/{n}", "FB_scene2_frames_with_bottom_match_in_A": f"{int((best <= 6).sum())}/{len(s2)}",
       "median_best_bottom_bits": float(np.median(best)), "min_best_bottom_bits": int(best.min())}
lags = arg[best <= 6] - (np.where(best <= 6)[0])
bot["offset_A_minus_FB_among_matches_median"] = float(np.median(lags)) if len(lags) else None
json.dump(bot, open("summary_bottom.json", "w"), indent=1)
open("bottom_nearest.tsv", "w").write("fb_frame\tnearest_A_frame\tbottom_bits\n" + "".join(f"{CUT+j}\t{arg[j]}\t{best[j]}\n" for j in range(len(s2))))
print(json.dumps(bot, indent=1))
