# Holy Holiday, run 2: pre-registration (Ep 387)

**Status: NOT RUN.** Published before Ep 387 is downloaded. Run 1 ([result](RESULT_run1.md)) found Ep 388 is not the source.

## Candidate

**Candace Ep 387**, "A Tale Of Two Statements: Mikey McCoy's Interview. Macklemore's Mic Drop.", 1:05:27,
<https://youtu.be/kn1E0scy9Wc>. YouTube gives its upload date as **2026-09-15**, the day before the post (Sep 16, 15:46 UTC).

Why this one: a search of her own channel for "Leavitt" (2026-10-12) returned it, next to Ep 388. Ep 387 was not in our
earlier general YouTube searches.

**Note on the date:** John's prediction 1 says the episode is "from Sep 16". If Ep 387 is the source, the result reports
the date difference plainly (YouTube's date vs the US date it aired), and it doesn't hide it.

## Rules

Everything from [PREREGISTRATION.md](PREREGISTRATION.md) and its three addenda, unchanged, with Ep 387 in place of Ep 388:

1. Download through the usual pipeline (download, watermark, Whisper).
2. Split with `scene_split.py`, threshold 50, 5 frames a second.
3. Label each scene Candace on screen or not, from contact sheets, **before any words are lined up**; publish the labels.
4. Line up with `compare_cut.py` (`--full` = Ep 387's `.whisper.json`, `--cut` = the post's), on the Candace scenes and on
   the full episode as the check.
5. Each of the post's clips 2, 3 and 4 is found if the kept stretches cover at least 80% of its time. Prediction 1 holds
   for this episode if all three are found, clips 2 and 4 in its close-up scenes and clip 3 in its desk/split scenes.
6. Visual check on the matched moments, 6 pairs, as in addendum 1.

## Command

```
(cd ~/Documents/repos/dl_wm && python bin/scene_split.py ~/boner_vault/dl_wm_outputs/<download day>/youtube__kn1E0scy9Wc/youtube__kn1E0scy9Wc_watermarked.mp4 --threshold 50 --fps 5)
python bin/compare_cut.py compare data/holy_holiday_run2 \
  --full ~/boner_vault/dl_wm_outputs/<download day>/youtube__kn1E0scy9Wc/youtube__kn1E0scy9Wc.whisper.json \
  --cut ~/boner_vault/dl_wm_outputs/2026-10-12/instagram__DdWodVUBwWy/instagram__DdWodVUBwWy.whisper.json
```
