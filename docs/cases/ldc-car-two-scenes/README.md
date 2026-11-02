# ldc-car-two-scenes

> **Correction (2026-11-01).** The footage this page calls scene 2 / extra footage is not footage LDC never posted: it is LDC's own
> earlier reel **DeaBysIPTSx** ("here I am at work", 2026-10-12 19:55 UTC), posted the day before TREES. Tim's copy shows a wider
> picture than LDC's post. The frame results on this page still stand. See [`../ldc-car-two-reels/`](../ldc-car-two-reels/).

latterdaychad's Instagram video of his wrecked car (https://www.instagram.com/p/Decca9IB4mM/ , 2026-10-13 18:24 UTC) against Tim Ballard's
Facebook reel of it (https://www.facebook.com/reel/1653357746398669/ , 2026-10-14 07:23 UTC), split into two scenes and scored with this repo's
own rules: `bin/compare_x_ig.py` THRESHOLDS and functions at 72bb4d7, imported unchanged by `two_scenes.py`.

- `00_PREREGISTRATION.md`: the split and the classes, written before the run.
- `result.md`, `result.json`: per-frame dHash distances (every 2 s) and the spoken-word comparison per scene.

| scene | Facebook span | pictures | words | class |
|---|---|---|---|---|
| 1 | 0-32.48 s | 15 of 17 frames IDENTICAL | 44-word identical run | IDENTICAL |
| 2 | 32.48-69.04 s | 0 of 18 frames match any Instagram frame | 0 shared 5-word shingles | NOTHING SHARED |

Scene 1 is the Instagram video; scene 2 is footage the Instagram post doesn't contain. Videos are not in the repo; sha256 of both files is in
`result.json`. Whole-pair frame check and page: https://antmerrill.github.io/backfire-tracking/ldc-basepoint.html
