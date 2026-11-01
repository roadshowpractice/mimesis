#!/usr/bin/env python3
"""Find where still images (cut from a thumbnail) occur in a video, by image fingerprint. Pixels only, no metadata.

Built for the left-or-right game on the ldsabuse twins case (Oct 2026): the S6E89 thumbnail has a guest photo on the
left and a host photo on the right. Which one shows up first in the episode itself?

One command does the whole test, so anyone can repeat it:

  still_in_video.py CASE --url VIDEO_URL --thumb THUMB.jpg --still left=40,0,285,608 --still right=810,0,1075,500
  still_in_video.py CASE --video B1=a.mp4 --video B2=b.mp4 --fps 5 --thumb ... --still ...   (videos already on disk)

Steps (each logged to CASE/CUSTODY.log with sha256):
  1. fetch   download the video with yt-dlp into CASE/derived/video/ (skipped if already there; hash checked)
  2. stills  cut each named box out of the thumbnail -> CASE/derived/stills/<name>.png
  3. search  sample 1 frame per second (ffmpeg, grayscale 320x180) and score every still against every frame:
               (a) whole frame:  dHash(frame) vs dHash(still)           (the rule as first written)
               (b) region:       the still's shape slid across the frame at several sizes, best window scored
             The fingerprint is the same 64-bit difference hash as T4 (9x8 grayscale, compare neighbours), taken from
             block averages: a coarse pass (4 px, 5% size steps) then a fine pass (1 px, 1.25%) around the 3 best;
             match = Hamming distance <= --max. Self-test: a video made of the thumbnail itself finds both stills.
  4. report  CASE/out/still_in_video/result.json + result.md: per still, best distance, its time, the first time
             at or under the threshold, and which still comes first.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


W, H = 320, 180                  # frame size the search works at (--frame; "auto" keeps each video's own shape, long side 320)
SCALES = tuple(round(1.0 - 0.05 * i, 3) for i in range(16))   # coarse: window height / frame height, 1.0 ... 0.25
STEP = 4                         # coarse window position step, pixels (on the 320x180 frame)
TOP = 3                          # then a fine search (1 px, 1.25% size) around the 3 best coarse windows


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def custody(case, step, msg, path=None):
    line = "{}\t{}\t{}".format(utc_now(), step, msg)
    if path is not None:
        line += "\t{}\tsha256={}".format(os.path.relpath(str(path), str(case)), sha256_file(path))
    with open(Path(case) / "CUSTODY.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch(case, url, ytdlp):
    vdir = case / "derived" / "video"; vdir.mkdir(parents=True, exist_ok=True)
    have = [p for p in sorted(vdir.glob("video.*")) if not p.name.endswith(".json")]
    if have:
        print("video already here:", have[0]); return have[0]
    cmd = [ytdlp, "-f", "bv*[height<=480][ext=mp4]/bv*[height<=480]/b[height<=480]", "--no-playlist",
           "--write-info-json", "-o", str(vdir / "video.%(ext)s"), url]
    print(" ".join(cmd)); subprocess.run(cmd, check=True)
    v = [p for p in sorted(vdir.glob("video.*")) if not p.name.endswith(".json")][0]
    custody(case, "still_in_video fetch", "downloaded " + url, v)
    for j in vdir.glob("video.info.json"):
        custody(case, "still_in_video fetch", "yt-dlp info for " + url, j)
    return v


def cut_stills(case, thumb, specs):
    sdir = case / "derived" / "stills"; sdir.mkdir(parents=True, exist_ok=True)
    im = Image.open(thumb).convert("RGB"); out = {}
    custody(case, "still_in_video stills", "thumbnail", Path(thumb))
    for spec in specs:
        name, box = spec.split("=")
        x0, y0, x1, y1 = (int(v) for v in box.split(","))
        p = sdir / f"{name}.png"; im.crop((x0, y0, x1, y1)).save(p)
        custody(case, "still_in_video stills", f"{name} = box {x0},{y0},{x1},{y1}", p)
        out[name] = p
    return out


def frames(video, fps=1.0):
    """yield (seconds into the video, grayscale float array HxW), fps frames per second"""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    t = 0
    while True:
        buf = p.stdout.read(W * H)
        if len(buf) < W * H:
            break
        yield round(t / fps, 2), np.frombuffer(buf, np.uint8).reshape(H, W).astype(np.float64)
        t += 1
    p.wait()


def integral(g):
    I = np.zeros((g.shape[0] + 1, g.shape[1] + 1)); I[1:, 1:] = g.cumsum(0).cumsum(1); return I


def grid_bits(I, x0, y0, w, h):
    """difference hash (9x8 block means, 64 bits) of windows (x0[i], y0[i], w, h) on integral image I -> (N, 8, 8) bool"""
    xs = np.rint(x0[:, None] + w * np.arange(10) / 9).astype(int)      # 9 columns -> 10 edges
    ys = np.rint(y0[:, None] + h * np.arange(9) / 8).astype(int)       # 8 rows -> 9 edges
    xa, xb, ya, yb = xs[:, None, :-1], xs[:, None, 1:], ys[:, :-1, None], ys[:, 1:, None]
    s = I[yb, xb] - I[ya, xb] - I[yb, xa] + I[ya, xa]
    m = s / np.maximum((xb - xa) * (yb - ya), 1)
    return m[:, :, 1:] > m[:, :, :-1]


def image_bits(img):
    g = np.asarray(img.convert("L"), dtype=np.float64)
    return grid_bits(integral(g), np.array([0.0]), np.array([0.0]), g.shape[1], g.shape[0])[0]


def window_grid(aspect):
    """per scale: (w, h, x0 array, y0 array) of every window of the still's aspect on a WxH frame"""
    out = []
    for s in SCALES:
        h = H * s; w = h * aspect
        if w > W:
            w = W; h = w / aspect
        if w < 12 or h < 12:
            continue
        xx, yy = np.meshgrid(np.arange(0, W - w + 1e-9, STEP), np.arange(0, H - h + 1e-9, STEP))
        out.append((w, h, xx.ravel(), yy.ravel()))
    return out


def fine(I, bits, cx, cy, w0, h0):
    """every window within +-4 px and +-5% size (1 px / 1.25% steps) of a coarse hit; returns (best distance, box)"""
    aspect = w0 / h0; best = (99, None)
    for f in np.arange(0.95, 1.0501, 0.0125):
        h = h0 * f; w = h * aspect
        if w > W or h > H or w < 12:
            continue
        xx, yy = np.meshgrid(np.arange(cx - 4, cx + 4.01, 1.0), np.arange(cy - 4, cy + 4.01, 1.0))
        x0, y0 = xx.ravel(), yy.ravel()
        ok = (x0 >= 0) & (y0 >= 0) & (x0 + w <= W) & (y0 + h <= H)
        if not ok.any():
            continue
        x0, y0 = x0[ok], y0[ok]
        dist = (grid_bits(I, x0, y0, w, h) != bits).sum(axis=(1, 2))
        k = int(dist.argmin())
        if dist[k] < best[0]:
            best = (int(dist[k]), [round(float(x0[k]), 1), round(float(y0[k]), 1), round(w, 1), round(h, 1)])
    return best


def frame_size(video, spec):
    """'WxH' as given, or 'auto': the video's display aspect with the long side 320 (even numbers)."""
    if spec != "auto":
        w, h = (int(x) for x in spec.lower().split("x"))
        if w % 2 or h % 2: sys.exit("--frame needs even width and height (yuv420p)")
        return w, h
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation:stream_tags=rotate",
                          "-of", "json", str(video)], capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]; vw, vh = int(st["width"]), int(st["height"])
    rot = next((int(float(d["rotation"])) for d in st.get("side_data_list", []) if "rotation" in d), 0)
    rot = rot or int(st.get("tags", {}).get("rotate", 0))
    if abs(rot) % 180 == 90: vw, vh = vh, vw     # phone reels carry a 90-degree flag; ffmpeg autorotates the frames
    k = 320 / max(vw, vh)
    return max(2, int(round(vw * k / 2)) * 2), max(2, int(round(vh * k / 2)) * 2)


def search(stills, video, maxd, fps=1.0):
    sb = {n: image_bits(Image.open(p)) for n, p in stills.items()}
    grids = {n: window_grid(Image.open(p).size[0] / Image.open(p).size[1]) for n, p in stills.items()}
    best = {n: {"whole": (99, None), "region": (99, None, None)} for n in stills}
    first = {n: {"whole": None, "region": None} for n in stills}
    n = 0
    for t, g in frames(video, fps):
        n += 1
        I = integral(g)
        whole = grid_bits(I, np.array([0.0]), np.array([0.0]), W, H)[0]
        for name, bits in sb.items():
            d = int((whole != bits).sum())
            if d < best[name]["whole"][0]:
                best[name]["whole"] = (d, t)
            if d <= maxd and first[name]["whole"] is None:
                first[name]["whole"] = t
            cands = []
            for w, h, x0, y0 in grids[name]:
                dist = (grid_bits(I, x0, y0, w, h) != bits).sum(axis=(1, 2))
                for k in np.argsort(dist)[:TOP]:
                    cands.append((int(dist[k]), float(x0[k]), float(y0[k]), w, h))
            cands.sort(key=lambda c: c[0])
            bd, bw = 99, None
            for d0, cx, cy, w0, h0 in cands[:TOP]:
                d1, b1 = fine(I, bits, cx, cy, w0, h0)
                if d1 < bd:
                    bd, bw = d1, b1
            if bd < best[name]["region"][0]:
                best[name]["region"] = (bd, t, bw)
            if bd <= maxd and first[name]["region"] is None:
                first[name]["region"] = t
        if n % 600 == 0:
            print(f"  {n} frames scanned", flush=True)
    return n, best, first


def hms(t):
    if t is None:
        return "—"
    t = float(t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case"); ap.add_argument("--thumb", required=True)
    ap.add_argument("--url", help="download this video first (step 1) and search it")
    ap.add_argument("--video", action="append", default=[], help="label=path of a video already on disk (repeatable)")
    ap.add_argument("--still", action="append", required=True, help="name=x0,y0,x1,y1 box in the thumbnail")
    ap.add_argument("--max", type=int, default=5, help="dHash match threshold (default 5, as in T4)")
    ap.add_argument("--fps", type=float, default=1.0, help="frames sampled per second of video (default 1)")
    ap.add_argument("--out", default="still_in_video", help="report folder name under CASE/out/")
    ap.add_argument("--ytdlp", default="yt-dlp")
    ap.add_argument("--frame", default="320x180",
                    help="WxH the frames are scaled to (default 320x180, landscape). 'auto' = each video's own aspect, long side 320: "
                         "needed for portrait reels, where 320x180 squeezes the picture ~3x and nothing can match (found 2026-10-30)")
    a = ap.parse_args(argv)
    case = Path(a.case)
    videos = []
    if a.url:
        videos.append((a.url, fetch(case, a.url, a.ytdlp)))
    for v in a.video:
        label, path = v.split("=", 1); path = Path(path)
        custody(case, "still_in_video input", f"video {label}", path); videos.append((label, path))
    if not videos:
        sys.exit("give --url and/or --video")
    stills = cut_stills(case, a.thumb, a.still)
    out = case / "out" / a.out; out.mkdir(parents=True, exist_ok=True)
    res = dict(made_at=utc_now(), threshold=a.max, fps=a.fps, coarse_scales=SCALES, coarse_step_px=STEP,
               fine="+-4 px, +-5% size around top 3", frame_spec=a.frame,
               stills={n: [s for s in a.still if s.startswith(n + "=")][0].split("=")[1] for n in stills}, videos=[])
    md = [f"# Stills in videos ({utc_now()})", "", f"{a.fps:g} frames per second, match = dHash <= {a.max} (region search; whole frame shown too).", "",
          "| Video | Frames | Still | Region: best distance (at) | first match | Whole frame: best |", "|---|---|---|---|---|---|"]
    global W, H
    for label, video in videos:
        W, H = frame_size(video, a.frame)
        print(f"searching {label}: {video} (frames {W}x{H})", flush=True)
        nframes, best, first = search(stills, video, a.max, a.fps)
        res["videos"].append(dict(label=label, path=str(video), sha256=sha256_file(video), frames=nframes, frame_size=[W, H],
                                  stills={n: dict(region_best=best[n]["region"], region_first_match_s=first[n]["region"],
                                                  whole_best=best[n]["whole"]) for n in stills}))
        for n in stills:
            r = best[n]["region"]
            md.append(f"| {label} | {nframes} | {n} | {r[0]} ({hms(r[1])}) | {hms(first[n]['region'])} | {best[n]['whole'][0]} |")
    found = [(v["label"], n) for v in res["videos"] for n, d in v["stills"].items() if d["region_first_match_s"] is not None]
    res["matches"] = found
    md += ["", "**Matches (dHash <= {}):** {}".format(a.max, ", ".join(f"{n} in {l}" for l, n in found) if found else "none"), ""]
    sizes = {tuple(v["frame_size"]) for v in res["videos"]}
    res["frame_size"] = list(sizes.pop()) if len(sizes) == 1 else None   # old key kept; None when --frame auto mixes shapes
    (out / "result.json").write_text(json.dumps(res, indent=2) + "\n")
    (out / "result.md").write_text("\n".join(md))
    custody(case, "still_in_video report", "wrote", out / "result.json")
    custody(case, "still_in_video report", "wrote", out / "result.md")
    print("\n".join(md))


if __name__ == "__main__":
    main()
