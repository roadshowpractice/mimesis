# LDC car: Tim's reel is LDC's two reels joined in reverse order, from a fuller copy (2026-11-01)

**Claim, in short.** latterdaychad (LDC) posted two separate car reels: AT WORK on Oct 12, then TREES on Oct 13.
Tim Ballard's Oct 14 reel is the two joined in reverse order, TREES then AT WORK. His AT WORK part shows **more of the
picture** than LDC's own post, so it wasn't cut from LDC's upload.

**Corrects** our 2026-10-30 pages ([`../ldc-car-scene2-extra-footage/`](../ldc-car-scene2-extra-footage/),
[`../ldc-car-two-scenes/`](../ldc-car-two-scenes/)). Those treated Tim's extra 36.6 s as footage LDC never posted. It is LDC's
own earlier reel, AT WORK. Their frame results still hold: no TREES frame is reused in the extra footage.

## Posting order (UTC; times from our scrapes of each account; `posts.csv`)

| # | posted | account | post | length | content |
|---|---|---|---|---|---|
| 1 | 2026-10-12 19:55:18 | latterdaychad (IG) | DeaBysIPTSx | 35.50 s | AT WORK: "Okay, so here I am at work..." |
| 2 | 2026-10-13 18:24:29 | latterdaychad (IG) | Decca9IB4mM | 32.47 s | TREES: "Okay, so I was parked right here between these two trees..." |
| 3 | 2026-10-14 07:22:55 | timballard89 (IG) | Ded1YoqorXi | 69.03 s | TREES, then AT WORK |
| 4 | 2026-10-14 07:23:08 | Tim Ballard (FB) | 1653357746398669 | 69.03 s | TREES, then AT WORK, then a 2.28 s silent hold |

The gaps: 22 h 29 min from AT WORK to TREES, then 12 h 59 min from TREES to Tim's reel (35 h 28 min after AT WORK).
Both LDC reels appear in all four of our scrapes of latterdaychad's timeline (Oct 13, 15, 16, 28), with no collaborators.

## How Tim's FB reel is built (seconds in Tim's reel)

| Tim's reel | source | how we know |
|---|---|---|
| 0-32.43 s | LDC's TREES reel, frame for frame | 968 / 973 frames match (banded dHash; see `../ldc-car-scene2-extra-footage/`) |
| 32.43-66.75 s | LDC's AT WORK reel, without its first 1.1 s ("Okay,") | audio below; same shots in the same order at matched moments |
| 66.75-69.03 s | nothing from LDC: the last shot held near-still with digital silence | -91 dB (true zero); frame-to-frame change < 0.3 of 255 |

## The tests

**1. Same audio.** Voice fingerprints (resemblyzer 0.1.4; `voice_compare.py`, results in `voice_compare.json` and
`voice_test.json`), cosine similarity, 1.0 = identical:
- Tim's 32.43-69.03 s vs LDC's AT WORK reel: **0.990**, the same sound.
- Tim's first half vs second half: **0.945**, the same voice.
- Calibration on known speakers (reels picked by their transcripts, IDs in `voice_compare.py`), LDC's other monologues against Tim's own talks: same person 0.810-0.912, LDC vs Tim
  0.638-0.705, no overlap. The car voice vs Tim: 0.657-0.746, so it isn't Tim. The car voice vs LDC's monologues:
  0.788-0.822.

**2. Audio offset.** Loudness envelopes cross-correlated (`audio_lag.py`, `audio_lag.json`): LDC's AT WORK runs **1.09 s
ahead** of Tim's second half (r = 0.877). That 1.09 s is LDC's opening "Okay,", which Tim's version lacks. The speech ends
at the same word in both ("It's crazy, so yeah").

**3. Pictures at the same moment.** At audio-matched moments the two show the same shots in the same order, but LDC's own
post is **zoomed in** with a large caption over the top of the frame, and Tim's shows **a wider view** with no caption. At
the same instant, Tim's frame shows things outside LDC's frame: a person standing by a dark car, a row of parked cars. A copy
made from LDC's post can't contain picture that LDC's post doesn't have.

**4. Why the frame hashes say 0 here, and why that's expected.** `match_atwork.py` (the same banded dHash as the 10-30
case) finds 0 matches at every offset within ±5 s (`match_atwork_summary.json`). That's not evidence of different
footage. LDC's caption covers the top and middle thirds of every frame, and Tim's GoFundMe link covers the bottom third, so
no band is clean in both. Control: on TREES, where only Tim's link differs, the bottom third alone matches just 453 / 973
(`match_atwork_summary_bottom.json`). The known-answer retest on TREES passes: 968 / 973.

## What this does and doesn't show

- **Shows:** LDC published AT WORK first and TREES second. Tim published both as one reel, in the opposite order, about
  13 hours after TREES. Tim's AT WORK has more picture than LDC's own post, plus a 2.28 s silent tail that LDC's lacks.
- **Doesn't show:** where Tim's wider copy came from, or who joined the reels. The wider picture means a version of the
  recording other than LDC's posted one existed and reached whoever made Tim's reel.
- **What would settle it:** any earlier public post carrying the wider, caption-free AT WORK footage. That would be a
  source both could have drawn on. If there's none, the wider file was private before Oct 14.

## Reproduce

Inputs: the videos and two MP3 cuts listed in `INPUTS.sha256` (not in this repo). Download the public posts in
`posts.csv` and compare hashes; platform re-encodes can differ, so the scripts' numbers are the check.
`voice_compare.py` (default run, then `--test`), `audio_lag.py` and `match_atwork.py` run with numpy, Pillow, ffmpeg and
resemblyzer. File paths at the top of each script point to our local copies; change `V` to yours.
Each script was run twice on 2026-11-01 with byte-identical output.
