# Result: IG vs Tim's FB reel outside the (x, y, t) masks (claude, 2026-10-30)

Pre-registration `00_PREREGISTRATION.md` + `00_PREREGISTRATION.sha256` (7/7 OK checked just before the run). Code `compare.py`,
per-frame numbers `compare_frames.tsv` (973 rows), totals `compare_summary.json`. Nothing changed after the run.

| | frames passing (of 973) | numbers |
|---|---|---|
| C1 mean difference outside the masks <= 20 | **973** | mean 3.72, worst 4.5 (frame 45) |
| C2 masked dHash, whole + every third <= 6 | **937** | worst: whole 7, top 5, middle 8, bottom 10 |

- The 36 C2 misses: 33 bottom third only, 2 middle only, 1 whole + bottom. In all 36, at least 2 of the 3 bands pass (John's
  2-of-3 rule, stated earlier today but not written into this pre-registration). C1 at those frames is at most 4.0.
- Inside the masks (info, not scored): logo 53-56, handle 50-52, link banner 92 mean difference while on.
- Check after the run (not part of the rule): the difference in rings just outside the banner hull is 4.1-5.0 at 0-3 px and 3.3-4.0
  at 20-40 px, about the same as the top half of the frame (3.4-4.4). So no shadow from the banner leaks past the hull; the bottom-band
  misses fit dHash on a flat band (asphalt + the grey-painted banner) where codec noise of ~4 levels flips near-equal neighbours.

Reading: outside what Tim's copy adds (the logo and handle, which move as one, and the link banner), every one of the 973 shared
frames is latterdaychad's picture, within a mean difference of 4.5 of 255.

— claude
