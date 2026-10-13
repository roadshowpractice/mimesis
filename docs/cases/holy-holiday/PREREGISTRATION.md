# Holy Holiday for Weirdos in Utah: pre-registration

**Status: NOT RUN.** This file and the input hashes are published before anything runs. The commit time is the
timestamp. Results go in their own file, and this one stays unchanged.

## The post

Instagram post [`DdWodVUBwWy`](https://www.instagram.com/p/DdWodVUBwWy/), Sep 16, 2026, 15:46 UTC, 1:37. Started by
**latterdaychad**, with **ldsabuseonx**, **theemmapreneurofficial** and **transcendental_mormon_mystic**. It is the only
one of the 32 posts in the [ldsabuse Twins](../ldsabuse-twins/) network with transcendental_mormon_mystic on it: the odd join.

It is a reaction video: latterdaychad speaks at the start (0:00–0:13.8) and the end (1:25.6–1:37), and in between is
**1:12 of Candace Owens**, cut from somewhere else. Her part has two different settings:

| Scene | Post time | Looks like |
|---|---|---|
| **A, close-up** | 0:13.8–0:25.8 and 0:46.6–1:25.6 | her face close, white wall, mic at the bottom |
| **B, studio desk** | 0:25.8–0:46.6 | wider shot at a desk, her name on the wall, a sheriff's office web page on screen beside her |

So the excerpt runs A, B, A. Scene times are from our scene split (`dl_wm` `scene_split.py`, threshold 50).

## Inputs (sha256 in [`inputs.SHA256SUMS`](inputs.SHA256SUMS); files not in this repo)

Our download of the post, its Whisper transcript (`.whisper.json`, `.srt`), and our cut of Candace's part (scenes 2–4).

## Predictions (John, locked 2026-10-12)

1. **Same show.** Scenes A and B both come from one Candace Owens episode, from Sep 16, 2026. John saw it.
2. **Bot detection.** The SRA accounts all treated that episode as total validation. Who re-posted it, when and how
   is how we detect the bots. *(Rules for this one are fixed in a separate pre-registration before it runs.)*

## Test of prediction 1 (run 1)

**Candidate source:** Candace Ep 388, Sep 16, 2026, "BIG NEWS! Erika To File A Wrongful Death Lawsuit. For Charlie Or
For PR?", 1:05:36, <https://youtu.be/aLJhpxrakCU>. It is the only Sep 16 Candace episode our YouTube searches found.
It is downloaded **after** this commit, through the usual pipeline (download, watermark, Whisper), and its hash goes in the result.

**Method:** `bin/compare_cut.py`, the tool that lined up THE CUT: `--full` = the episode's `.whisper.json`, `--cut` =
the post's `.whisper.json`. It finds the stretches of the episode that the post keeps, word for word, with their time
offset.

**Decision rule.** Map each kept stretch back to post time (episode time minus its offset). Then:

- Scene A is **found** if those stretches cover at least 80% of scene A's 51 s.
- Scene B is **found** if they cover at least 80% of scene B's 20.8 s.
- Prediction 1 **holds** if both are found in this one episode.
- If only one is found, it does not hold for this episode, and the result says which scene came from where.
- If neither is found, Ep 388 is not the source. The next candidate gets its own pre-registration before it runs.

Whisper spells some words differently in two recordings of the same speech (THE CUT: 245 of 249 matched), which is
why the bar is 80% and not 100%.

## Command (run after this is pushed, word for word)

```
python bin/compare_cut.py compare data/holy_holiday_run1 \
  --full ~/boner_vault/dl_wm_outputs/<download day>/youtube__aLJhpxrakCU/youtube__aLJhpxrakCU.whisper.json \
  --cut ~/boner_vault/dl_wm_outputs/2026-10-12/instagram__DdWodVUBwWy/instagram__DdWodVUBwWy.whisper.json
```

`<download day>` is the only free part: the folder the pipeline writes to on the day of the download.
