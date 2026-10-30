# Pre-registration: IG vs Tim's FB reel outside the (x, y, t) masks (claude, 2026-10-30)

Written before compare.py reads any Instagram pixel. decide.py read FB frames only.

**Pair.** latterdaychad IG Decca9IB4mM (2026-10-13 download) vs Tim Ballard FB reel 1653357746398669 (2026-10-16 download),
frames 0..972 (0-32.433 s, the shared part; Opie 10-29: first added frame is 973).

**Masks (frozen: masks.json + masks.npz, made by decide.py).** One convex hull per piece Tim's copy adds, grown 3 px; on in these frames:

| piece | area px | frames (30 fps) |
|---|---|---|
| IG logo, top right | 1835 | 6-269, 540-811 |
| @LATTERDAYCHAD, top right | 2970 | 6-269, 540-811 |
| IG logo, left middle | 1835 | 272-539, 812-972 |
| @LATTERDAYCHAD, left middle | 2970 | 272-539, 812-972 |
| GoFundMe link banner | 47243 | 24-972 |

The top-right logo/handle are the left-middle glyphs shifted (570, -400) / (470, -399). Not masked: the title "What happened to
Chad's Car" (on both copies).

**Rule.** Inside a mask nothing counts. Per frame, outside the masks:
- C1: mean |IG - FB| <= 20 (of 255), the published same-reel cutoff;
- C2: masks painted grey in both, 64-bit dHash of whole frame and each third <= 6 (house IDENTICAL; banded rule 2026-10-30).
Reported: how many of 973 frames pass C1, C2; worst frames; mean difference inside each mask (info only, not scored).
No verdict threshold on the count is set here (in-house run, not a contest).
