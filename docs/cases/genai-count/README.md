# Trial: how many of @timballard89's 5 posts on Oct 7, 2026 are Gen-AI fakes?

**Status: OPEN.** The predictions are locked. The code and the decision rules below are published **before anything runs**,
and the commit time is the timestamp. Results will be added under "Results", and this pre-registration will stay unchanged.

![One day on Instagram](img/2026-10-07_one_day_on_insta_card.png)

## The 5 posts

| # | Posted (PT) | Post | Length |
|---|---|---|---|
| 1 | 16:59 | [DeNlpDSI691](https://www.instagram.com/p/DeNlpDSI691/) | 4:08 |
| 2 | 17:15 | [DeNnnzboyBs](https://www.instagram.com/p/DeNnnzboyBs/) | 1:42 |
| 3 | 20:51 | [DeOAfQwonHi](https://www.instagram.com/p/DeOAfQwonHi/) | 1:26 |
| 4 | 20:57 | [DeOBQw2oqTA](https://www.instagram.com/p/DeOBQw2oqTA/) | 5:29 |
| 5 | 21:23 | [DeOEQmtoQjd](https://www.instagram.com/p/DeOEQmtoQjd/) | 1:08 |

The sha256 of each of our downloads is in [`posts.tsv`](posts.tsv). The video files are not in this repo.

## Predictions (locked)

| Player | X | Call | Which |
|---|---|---|---|
| John | [@Jimzz1e](https://x.com/Jimzz1e/status/2109005757220061577) | **4/5** | — |
| Claude | @MerrillAnt50522 | **2/5** | #1 and #5 |
| Grok | [@grok](https://x.com/grok/status/2109005999893774839) | **2/5** | #1 and #5 ("first and last thumbnails") |

Grok's reply, 2026-10-10 19:39:48 UTC, verbatim:

> Yes, still in.
>
> Modern AI-generated images and videos can be virtually indistinguishable from authentic content, making definitive determination difficult or impossible from visual inspection alone.
>
> The first and last thumbnails show highly stylized, cinematic religious scenes consistent with Gen-AI output. The middle three look like conventional talking-head or posed videos of the person.
>
> My call: 2.

![Question card](img/2026-10-10_grok_genai_question_card.png)

## Rules

1. Predictions are locked. No changes after the opening post.
2. Existing tools first. Our downloads of the 5 posts, and the [Round 3 T5 checks](../ldsabuse-twins/round3/README.md):
   AI-image detector on frames vs a real-camera control, voice and spectrum checks. New code only where those fall short.
3. Code and decision rules are published before they run. The commit time is the timestamp.
4. Same scripts, same data for all three. Every input and output is hashed.

## The checks ([`genai_count.py`](genai_count.py))

The functions are imported unchanged from Round 3's [`t5_genai_check.py`](../ldsabuse-twins/round3/t5_genai_check.py).

**Control (known real camera):** [Da7-1LpIR89](https://www.instagram.com/p/Da7-1LpIR89/). It's a third party's
phone video (dr.venus_sh) of Tim speaking on stage after a screening, 3:00 long. A person picks, by ear, where Tim speaks;
those times are written here before the run.

**A, images.** The open detector `umm-maybe/AI-image-detector` scores 9 frames per post (10%, 20% … 90%) and 20 frames
of the control.
- A post is **flagged A** if its median frame score is above the control's 95th percentile.

**B, voice.** `resemblyzer` speaker embedding of each post vs Tim's voice in the control.
- cosine ≥ 0.75: "matches Tim". Stated limit: a good voice clone would also match.
- below 0.75: "does not match Tim". This includes music-only posts and other speakers.
- Too little audio: "no speech".

**C, spectrum.** The highest frequency with energy above −60 dB of the peak, per post vs the control.
- A cutoff at or below 12 kHz while the control goes higher is a TTS-style flag, not proof.

The count the script reports is the number of posts flagged A. B and C are reported next to it for every post.

## Run it

```
pip install transformers resemblyzer scipy matplotlib
python genai_count.py POSTS_DIR Da7-1LpIR89.mp4 OUT_DIR --tim <start-end ...>
```

## Results

Not run yet.
