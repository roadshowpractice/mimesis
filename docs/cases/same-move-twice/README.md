# Same move, twice: an ally's reel, Tim added, posted again (2026-11-01)

**Claim, in short.** Twice in two days, a reel posted by a Brazilian political ally was reposted by Tim Ballard's accounts
with Tim inserted into it. The ally's footage is kept intact and on its own clock; the only new material is short
pieces showing Tim with the ally or with Bolsonaro.

| # | ally's original | posted (UTC) | Tim's copy | posted (UTC) | gap | what was inserted |
|---|---|---|---|---|---|---|
| 1 | Instagram **De6mHwFRbAG**, @mariofriasoficial (Mário Frias) | 2026-10-25 11:26:35 | Facebook reel **1140352768334907**, Tim Ballard | 2026-10-26 (FB gives the date only) | under 2 days | 17.92-18.80 s: an image of Tim with Bolsonaro; 30.68-31.60 s: Tim at Christ the Redeemer; 47.6-51.6 s: end card "DOMINGO VOTE 22 @MARIOFRIASOFICIAL" |
| 2 | Instagram **De8MHpPRfC2**, @dep.nikolas.ferreira (Nikolas Ferreira) | 2026-10-26 02:17:38 | Instagram **De-hLujNZYP**, @timballard89 | 2026-10-27 00:00:25 | 21 h 43 min | 0-2.77 s: a still image of Tim with Nikolas; 160.1-166.7 s: a hallway clip of Tim with Nikolas |

The same table is in `instances.csv`. The card showing the frames is posted on X:
https://x.com/MerrillAnt50522/status/2117017059129426267 (sha256 of the card in `SHA256SUMS`).

## Instance 1: Mário Frias → Tim's Facebook reel

- Mário's reel: owner mariofriasoficial, no collaborators, posted the morning of the Brazilian runoff (08:26 Brasília time).
- Tim's Facebook reel is 51.6 s long. Its frames carry Instagram's own share stamp, "@MARIOFRIASOFICIAL", with the audio
  "SIL · Capitão Levanta-Te". So Tim's copy was taken from Mário's Instagram post, not from a separate original file.
- **Measured (2026-10-27):** frame difference at 25 fps over the whole reel, using the left two thirds of the frame so the
  share stamp is ignored. Tim's copy equals Mário's reel on the same clock except for three pieces with no Mário stamp:
  17.92-18.80 s (0.88 s), 30.68-31.60 s (0.92 s) and the end card 47.6-51.6 s (4.0 s).
- The two inserts are about 0.9 s each, short enough to miss at normal speed.

## Instance 2: Nikolas Ferreira → Tim's Instagram re-share

- Nikolas's reel: 4,721 frames, 157.37 s. Tim's: 5,002 frames, 166.73 s. Both are 720x1280 at 30 fps.
- **Frames.** Each frame is fingerprinted as grey 180x320, with one 64-bit dHash per horizontal third
  (`bin/compare_x_ig.py` `band_hashes`). A match means 2 or 3 of the 3 thirds are within 6 bits.
  - Comparing the same frame number in both files, only 1,066 / 4,721 frames match (22.6%).
  - Shifting by 83 frames (2.767 s), **4,678 / 4,721 match (99.09%)**, 3,233 of them on all three thirds.
  - The best shift is -83 frames in all ten ~500-frame windows, so there's no speed change and nothing cut from the middle.
- **Sound.** Tim's audio is Nikolas's, delayed 2.760 s (correlation r = 0.977). Transcribed words line up for 326 / 343
  words, at a median delay of 2.76 s.
- **Known-answer check first:** the same code gives 968 / 973 on a pair already known to be the same footage
  (LDC's car reel against Tim's FB copy; see `../ldc-car-scene2-extra-footage/`).
- Tim's copy is therefore Nikolas's recording, untouched, with 2.767 s of still image before it and 6.60 s of hallway clip after it.

## The pattern

| | instance 1 | instance 2 |
|---|---|---|
| ally footage kept | yes, same clock | yes, all of it, one constant shift |
| what Tim added | about 0.9 s inserts (2) plus an end card | a front still plus an end clip |
| the additions show | Tim with Bolsonaro; Tim at a Rio landmark | Tim with Nikolas (twice) |
| time from ally post to Tim post | under 2 days | 21 h 43 min |
| credit to the ally in Tim's copy | only Instagram's own share stamp on the frames | collaborators and credits both empty in our scrape (caption not captured) |

## What this does and doesn't show

- **Shows:** both of Tim's posts are the ally's video plus short pieces of Tim, added at the front, the end, or spliced
  into the middle. The ally posted first both times.
- **Doesn't show:** who made the edits, a person or an automated pipeline. The measurements are the same either way.
- **What would bear on that:** how many more instances there are, and how regular they are. That means the same kind of
  inserts, the same lag after the ally's post, and the same kind of Tim images, across more allies. One or two could be
  a person; a steady run at a fixed lag points to a process. Also: whether the Tim images were made before the ally posted,
  which would mean they were ready to drop in.

## Sources and reproduction

- Post times come from our own scrapes of each account (timeline JSONL; sha256s in `SHA256SUMS`). The Facebook reel has
  only a date (`video_date` 20261026).
- The videos and frames are not in this repo (text only). Their sha256s are in `SHA256SUMS`, so a copy downloaded from the
  public posts can be checked against ours.
- Instance 2: `../ldc-car-scene2-extra-footage/compare_scenes.py` uses the same fingerprints. The full run (offset
  scan, audio lag, word alignment) was done offline on the files above. Its report and per-frame tables are kept with
  the data, hash-listed (report sha256 2e99d8d35abf…).
- Instance 1: a one-off frame difference, done 2026-10-27. That script was not kept, so this measurement is described
  here but not packaged.
