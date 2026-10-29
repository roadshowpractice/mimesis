# Two scenes, mimesis rules — result (claude, 2026-10-29)

Pre-registration 00_PREREGISTRATION.md (sha256 9769ab6956a1472b..., checked OK before the run). Code two_scenes.py (mimesis 72bb4d7 functions
and THRESHOLDS, imported unchanged). Raw: result.json. Frames every 2 s, whole frame, 64-bit dHash.

| scene | Facebook span | images | spoken words | class |
|---|---|---|---|---|
| S1 | 0 to 32.48 s | 15 of 17 frames IDENTICAL (dHash <= 6), 1 SAME MATERIAL (8), 1 NOTHING (30, at 32 s: the end of the Instagram video) | 44-word identical run, 52 shared 5-word shingles, Jaccard 0.55 | **IDENTICAL** (images); text SAME MATERIAL |
| S2 | 32.48 to 69.04 s | 18 of 18 frames NOTHING SHARED with any Instagram frame (nearest 20 to 29 bits) | 84 words, 0 shared shingles, longest run 2 | **NOTHING SHARED** |

What this says:
- **Scene 1 is latterdaychad's Instagram video**, frame for frame (John's prediction: match).
- **Scene 2 is not in that Instagram post.** Its pictures match no frame of it, and its words share nothing with it. It is more footage of the same
  wrecked car, with first-person narration ("I am at work. I was working door to door and they just called me back to the office ... it was
  like a hit and run"), and the GoFundMe link on screen. That is what Tim Ballard's Facebook added.
- Not tested: whether scene 2 was ever published anywhere else (e.g. latterdaychad's stories or another post); whether the voice in scene 2 is
  the same speaker as scene 1.
