# LDC car: the extra 36.6 s in Tim Ballard's Facebook copy (2026-10-30)

> **Correction (2026-11-01).** The footage this page calls scene 2 / extra footage is not footage LDC never posted: it is LDC's own
> earlier reel **DeaBysIPTSx** ("here I am at work", 2026-10-12 19:55 UTC), posted the day before TREES. Tim's copy shows a wider
> picture than LDC's post. The frame results on this page still stand. See [`../ldc-car-two-reels/`](../ldc-car-two-reels/).

**Pair.** latterdaychad Instagram reel **Decca9IB4mM** (posted 2026-10-13 18:24:29 UTC, 974 frames at 30 fps = 32.47 s) and
officialtimballard Facebook reel **1653357746398669** (posted 2026-10-14 07:23:08 UTC, 12.98 h later; 2071 frames = 69.03 s).
Post times are as the platforms reported them to our scrapes. Video sha256s in `SHA256SUMS`; the videos themselves are not in this repo.

**Scene 1** = FB frames 0-972 (0-32.43 s) = LDC's reel plus Tim's added GoFundMe link and logo/handle moves; see the sibling case
[`../ldc-car-overlay-masks/`](../ldc-car-overlay-masks/) (973/973 frames within mean difference 20 outside the added pieces).
**Scene 2** = FB frames 973-2070 (1098 frames, 36.6 s), not in LDC's reel.

## Question
Does scene 2 reuse any frame of scene 1?

## Method (`compare_scenes.py`)
Every scene-2 frame against every scene-1 frame (1098 x 973 pairs), frames grey 180x320 from the un-watermarked FB download.
Fingerprint: 64-bit dHash of the whole frame and of the top, middle and bottom thirds (`bin/compare_x_ig.py` `band_hashes`, unchanged).
Match = 2 or 3 of 3 thirds within 6 bits. Known-answer check first: LDC's IG frame i vs FB frame i (same footage) must match.

## Result (`summary.json`, per frame `scene2_nearest_scene1.tsv`)
| | |
|---|---|
| known-answer check, IG vs FB scene 1 | 968 / 973 frames match |
| scene-2 frames matching any scene-1 frame | **0 / 1098** (none with 2 or 3 thirds) |
| closest whole-frame distance | 13 bits (median of each frame's best: 20); a match is 6 or less |

By eye (not measured): scene 2 shows the same silver car, damage and parking lot as scene 1. FB frame pairs used on the card:
smashed front 900 / 1980, hood stains 960 / 1500, side and wheel 660 / 1380, curb and lines 60 / 1860.
A police SUV is on screen at FB frame 1680 (56.0 s); scene 1, looked at once per second, has none (a white van passes at 3-4 s).

**Reading.** Same car, same place, different shots: scene 2 is more footage of the same scene, not a re-cut of LDC's reel.
LDC posted the short cut first; Tim's copy has the longer footage. Who had the full file first is not in this data.

## Reproduce
`python docs/cases/ldc-car-scene2-extra-footage/compare_scenes.py FB.mp4 IG.mp4` (numpy, Pillow, ffmpeg; about a minute), then compare
with `summary.json` and `scene2_nearest_scene1.tsv`. Re-run 2026-10-30 from this copy: byte-identical.
