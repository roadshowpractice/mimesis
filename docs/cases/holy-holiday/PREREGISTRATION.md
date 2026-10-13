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

## Addendum, 2026-10-12, before anything ran: visual cross-check (Grok's suggestion)

Grok, on X ([reply](https://x.com/grok/status/2109816150884282448)): "a quick visual cross-check that the close-up and
desk settings both appear in that episode, to confirm the cut beyond audio alone". Added, as a **confirmation step**: it
does not change the 80% rule above.

- For each scene (A and B), take 3 moments the transcript line-up matched: the first, middle and last matched word of
  that scene's longest kept stretch.
- At each moment, grab one frame from the post and one from the episode (at the post time plus the stretch's offset) and
  set them side by side on one sheet, 6 pairs in all.
- Each pair is marked **same setting** or **not**, by eye (Claude, then John). The post is a vertical crop with
  captions on top, so the check is about the setting (room, wall, desk, mic, clothes), not a pixel-perfect match.
- Reported with the result: "visual check: A 3/3, B 3/3" (or what it is), with the sheet. If a scene's audio is found but
  its picture is not, the result says so plainly. That would mean the audio was laid over other footage.

## Addendum 2, 2026-10-12, before anything ran: scenes from the splitter, on both sides (John)

John, on X ([reply](https://x.com/Jimzz1e/status/2109817909321355714)): "we agree that we use the scenes that were
generated in splitter. Candace comprised 2 scenes." And: adjust one side or both, so it is apples to apples.

So both videos are cut by **the same splitter with the same settings** (`dl_wm` `bin/scene_split.py`, threshold 50,
5 frames a second), and the comparison is splitter scene to splitter scene:

- **Post side** (already split): Candace is splitter clips 2, 3 and 4. Clips 2 and 4 are one scene, A (the close-up),
  cut in two by clip 3, scene B (the studio desk). Two scenes, as John said.
- **Episode side**: Ep 388's watermarked video goes through the same splitter after it is downloaded, before the line-up.
- **The coverage rule now applies per splitter clip:** each of clips 2, 3 and 4 is **found** if the kept stretches cover at
  least 80% of that clip's time. This replaces the pooled "80% of scene A" and "80% of scene B" above, and is stricter.
- For each found clip, the result names the **episode splitter scene(s)** its words fall in.
- **Prediction 1 holds** if clips 2, 3 and 4 are all found in Ep 388, and clips 2 and 4 land in the episode's close-up
  setting and clip 3 in its desk setting. The setting is read off the splitter's own screenshots of those episode scenes,
  which also makes the visual check (addendum 1) scene to scene.

## Command (run after this is pushed, word for word)

```
# 1. split the episode, same splitter and settings as the post (addendum 2)
(cd ~/Documents/repos/dl_wm && python bin/scene_split.py ~/boner_vault/dl_wm_outputs/<download day>/youtube__aLJhpxrakCU/youtube__aLJhpxrakCU_watermarked.mp4 --threshold 50 --fps 5)
# 2. line up the words
python bin/compare_cut.py compare data/holy_holiday_run1 \
  --full ~/boner_vault/dl_wm_outputs/<download day>/youtube__aLJhpxrakCU/youtube__aLJhpxrakCU.whisper.json \
  --cut ~/boner_vault/dl_wm_outputs/2026-10-12/instagram__DdWodVUBwWy/instagram__DdWodVUBwWy.whisper.json
```

`<download day>` is the only free part: the folder the pipeline writes to on the day of the download.
