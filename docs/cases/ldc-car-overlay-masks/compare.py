#!/usr/bin/env python3
"""Compare Instagram vs Tim's FB reel frame by frame OUTSIDE the frozen (x, y, t) masks. claude, 2026-10-30.
Inside a mask nothing counts, match or not (John: "an area where if it doesn't match.. it doesn't count").
Per frame n = 0..972 (the shared part, 30 fps, same frame index in both files), M_n = union of the pieces whose span holds n.
  C1  mean |IG - FB| (grey, 0-255) over pixels outside M_n          pass: <= 20   (the published same-reel cutoff)
  C2  masked dHash: M_n painted grey 128 in BOTH frames, then 64-bit dHash of the whole frame and of each horizontal third
      pass: every one <= 6 (house IDENTICAL cutoff, banded rule of 2026-10-30)
Also reported, not scored: mean |IG - FB| inside each piece while it is on.
"""
import csv, json, subprocess, sys
from pathlib import Path
import numpy as np, cv2
HERE = Path(__file__).resolve().parent
V = {"ig": Path.home() / "boner_vault/dl_wm_outputs/2026-10-13/instagram__Decca9IB4mM/instagram__Decca9IB4mM.mp4",
     "fb": Path.home() / "boner_vault/dl_wm_outputs/2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"}
W, H, LAST = 720, 1280, 972
J = json.load(open(HERE / "masks.json")); MK = np.load(HERE / "masks.npz")
def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", str(LAST + 1), "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    while (b := p.stdout.read(W * H)) and len(b) == W * H: yield np.frombuffer(b, np.uint8).reshape(H, W)
def dhash(img):
    s = cv2.resize(img, (9, 8), interpolation=cv2.INTER_AREA).astype(np.int16)
    return (s[:, 1:] > s[:, :-1]).flatten()
def hashes(img):
    t = H // 3
    return [dhash(img)] + [dhash(img[i * t:(i + 1) * t]) for i in range(3)]
rows = []
for n, (a, b) in enumerate(zip(frames(V["ig"]), frames(V["fb"]))):
    on = [k for k, v in J["pieces"].items() if any(x <= n <= y for x, y in v["frame_spans"])]
    M = np.zeros((H, W), bool)
    for k in on: M |= MK[k]
    d = np.abs(a.astype(np.int16) - b)
    c1 = float(d[~M].mean())
    a2, b2 = a.copy(), b.copy(); a2[M] = 128; b2[M] = 128
    hd = [int((x != y).sum()) for x, y in zip(hashes(a2), hashes(b2))]
    r = {"frame": n, "t": round(n / 30, 3), "masked_px": int(M.sum()), "c1_mean_diff_outside": round(c1, 2),
         "c1_pass": int(c1 <= 20), "dhash_whole": hd[0], "dhash_top": hd[1], "dhash_middle": hd[2], "dhash_bottom": hd[3],
         "c2_pass": int(max(hd) <= 6), "pieces_on": "+".join(on)}
    for k in J["pieces"]: r["inside_" + k] = round(float(d[MK[k]].mean()), 1) if k in on else ""
    rows.append(r)
assert len(rows) == LAST + 1, len(rows)
with open(HERE / "compare_frames.tsv", "w") as f:
    w = csv.DictWriter(f, rows[0].keys(), delimiter="\t"); w.writeheader(); w.writerows(rows)
c1 = np.array([r["c1_mean_diff_outside"] for r in rows]); hd = np.array([[r["dhash_whole"], r["dhash_top"], r["dhash_middle"], r["dhash_bottom"]] for r in rows])
S = {"frames": len(rows), "c1_pass": int(sum(r["c1_pass"] for r in rows)), "c1_mean": round(float(c1.mean()), 2), "c1_max": float(c1.max()),
     "c1_max_frame": int(c1.argmax()), "c2_pass": int(sum(r["c2_pass"] for r in rows)),
     "dhash_max_whole_top_middle_bottom": hd.max(0).tolist(), "c2_fail_frames": [r["frame"] for r in rows if not r["c2_pass"]][:40]}
for k in J["pieces"]:
    v = [r["inside_" + k] for r in rows if r["inside_" + k] != ""]
    S["inside_" + k] = {"frames_on": len(v), "mean": round(float(np.mean(v)), 1) if v else None}
json.dump(S, open(HERE / "compare_summary.json", "w"), indent=1); print(json.dumps(S, indent=1))
