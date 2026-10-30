# ldc-car-overlay-masks

Same pair as `../ldc-car-two-scenes/`: latterdaychad's Instagram video (https://www.instagram.com/p/Decca9IB4mM/) and Tim Ballard's
Facebook reel of it (https://www.facebook.com/reel/1653357746398669/). This case covers the shared part only, frames 0-972 at 30 fps
(0-32.433 s; the first added frame is 973, which refines the 32.48 s used in `ldc-car-two-scenes`).

Tim's copy adds three things on top of latterdaychad's picture: an Instagram logo, the handle @LATTERDAYCHAD (the two move together
between a top-right and a left-middle spot), and a GoFundMe link banner along the bottom. Here each added piece gets a mask in
(x, y, t): the smallest convex shape around it, in the frames where it is on. Inside a mask nothing counts, match or not; everything
outside is compared.

- `decide.py`: makes the masks from the **Facebook frames only** (no Instagram pixel is read). Writes `masks.json` (hull polygons,
  frame spans) and `masks.npz` (pixel masks; not committed, binary; `decide.py` rebuilds it, sha256 in `00_PREREGISTRATION.sha256`).
- `00_PREREGISTRATION.md` / `.sha256`: the masks and the rule, hashed before `compare.py` read any Instagram pixel.
- `compare.py`: per frame, outside the masks, C1 mean |IG - FB| <= 20 and C2 banded dHash (whole frame + each third <= 6).
  Output `compare_frames.tsv` (973 rows), `compare_summary.json`, `result.md`.
- `text_boxes/text_boxes.py`: the earlier, simpler step, tight rectangles from OCR word boxes (Tesseract TSVs from a 0.5 s pass,
  not in this repo) and the inside/outside difference on a 0.5 s grid.
- `exploratory/locate.py`, `locate2.py`: first two tries at finding the watermark per frame; not used for the masks.

| piece | frames | mean difference inside while on (info only) |
|---|---|---|
| IG logo + handle, top right | 6-269, 540-811 | 50-56 |
| IG logo + handle, left middle | 272-539, 812-972 | 52-53 |
| GoFundMe link banner | 24-972 | 92 |

| outside the masks | frames passing (of 973) |
|---|---|
| C1 mean difference <= 20 | 973 (mean 3.72, worst 4.5) |
| C2 dHash whole + every third <= 6 | 937 (all 36 misses have 2 of 3 thirds passing; 33 are the bottom third) |

Outside what Tim's copy adds, every shared frame is latterdaychad's picture. Videos are not in the repo; sha256 of both is in
`00_PREREGISTRATION.sha256`. The scripts here are the exact files that ran (paths as on the machine that ran them).
