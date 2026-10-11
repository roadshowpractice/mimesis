# Left or right: pre-registration (published before the run)

**Status: NOT RUN.** Everything below was fixed and published before the comparison was run. Nothing in the code, the
inputs or the rule will change between this file and the run. The result goes in a separate file.

## The question

The S6E89 thumbnail of *The Imagination Podcast* has two face photos:

- **left:** the guest, Justin Riggs (@ldsabuse on X, ldsabuseonx on Instagram);
- **right:** the host, Emma Katherine.

The same thumbnail is B7 of the ldsabuse twin structure. @ldsabuse posted it on X on **Aug 18, 2026, 16:44 PDT** ("Soon."), and ldsabuseonx posted it on Instagram on Aug 20. See [B7 and the Lettering of the Twin Structure](../b7.html).

**The test (John's final rule):** can we find these pieces anywhere in the Joder-verse, meaning our own data, *before* Aug 18, 2026, 16:44 PDT? We use pixels only, compared with mimesis.

## Predictions (locked 2026-10-11 20:16 UTC, before any search)

| Who | Pick | How |
|---|---|---|
| John | **Right** (host) first | prediction |
| Claude | **Right** (host) first, about 60% | prediction: the thumbnail is the host's production, and the guest posted the finished art two days before airing |
| Grok | **Left** (guest) first | reply [2109379402337251817](https://x.com/grok/status/2109379402337251817) to our game post [2109379042432745972](https://x.com/MerrillAnt50522/status/2109379042432745972). It cites a search of post times rather than a prediction. |

## How the rule got here (all before any comparison, times UTC, Oct 11)

| Time | Step |
|---|---|
| 20:16 | Game posed: who posted the image first, guest or host? Predictions locked |
| 20:38 | John: pixels only, no metadata. Compare the stills against frames |
| 20:40 | The two still boxes fixed (below) |
| 20:44 | Method checked: self-test and decoys (below) |
| 20:52 | John's final rule: find the pieces in the Joder-verse before the X post |
| 21:00 | First run defined: the three videos before the photo, B1–B3 |

## First run: exactly what will be done

**Inputs.** All are in [`inputs/`](inputs/), hashes in [`inputs/SHA256SUMS`](inputs/SHA256SUMS). These are the same bytes as our case files, which have been under custody since they were collected (Oct 7–8, 2026).

| File | What | sha256 |
|---|---|---|
| `thumbnail_DcR9bobtKcF.jpg` | the S6E89 thumbnail as ldsabuseonx posted it, 1080×608, unwatermarked | `614c537f…` |
| `still_left.png` | box (40, 0, 285, 608) of the thumbnail: the guest’s face | `505006c1…` |
| `still_right.png` | box (810, 0, 1075, 500): the host’s face | `3432b7eb…` |
| `B1_Dbed4OEN_9d.mp4` | B1, ldsabuseonx, Jul 31, 2026, 43.8 s, [post](https://www.instagram.com/reel/Dbed4OEN_9d/) | `3548830115…` |
| `B2_Dbm17ScJJmq.mp4` | B2, ldsabuseonx, Aug 3, 2026, 18.1 s, [post](https://www.instagram.com/reel/Dbm17ScJJmq/) | `a139d831…` |
| `B3_Db6ohLRp-rK.mp4` | B3, ldsabuseonx, Aug 11, 2026, 52.4 s, [post](https://www.instagram.com/reel/Db6ohLRp-rK/) | `84eca0d7…` |

The boxes leave out the overlay text, the torn edges and the S6E89 label.

**Method.** Each video is sliced at 5 frames a second and reduced to 320×180 grayscale. Each face is then compared with every part of every slice, at every position and size. A coarse pass uses 4-pixel and 5% size steps; a fine pass then uses 1-pixel and 1.25% steps around the 3 best spots.

The fingerprint is a 64-bit difference hash: the picture is reduced to 9×8 grey squares, and each square is compared with its right-hand neighbour. **A face is found if a slice region is within 5 bits of it** (Hamming distance ≤ 5). That is the threshold of the earlier T4 test.

**Command**, exactly as it will be typed: from the mimesis repo root, at commit `54a0978`, with `bin/still_in_video.py` sha256 `cc6e3779…`. The inputs are read from this folder. `data/x_ig_ldsabuse_2026-10` is our case folder: it receives the custody log and the report.

    venv/bin/python bin/still_in_video.py data/x_ig_ldsabuse_2026-10 \
      --video B1=docs/cases/ldsabuse-twins/left_right/inputs/B1_Dbed4OEN_9d.mp4 \
      --video B2=docs/cases/ldsabuse-twins/left_right/inputs/B2_Dbm17ScJJmq.mp4 \
      --video B3=docs/cases/ldsabuse-twins/left_right/inputs/B3_Db6ohLRp-rK.mp4 \
      --fps 5 --out left_right_B1_B3 \
      --thumb docs/cases/ldsabuse-twins/left_right/inputs/thumbnail_DcR9bobtKcF.jpg \
      --still left=40,0,285,608 --still right=810,0,1075,500

**Environment:** Python 3.8.20, numpy 1.24.4, Pillow 10.4.0, ffmpeg 8.0.1.

**What counts as the result.**

- For each face, in each video: the best distance and where it occurs, and whether there is a match at ≤ 5.
- **Any match is checked by eye** before it counts, because the same people can look alike across frames.
- **"No match" is a valid result.** It means these pieces are not in B1–B3. It does not mean they are nowhere in the Joder-verse. Later runs can add more of our data, each published like this one before it is run.

## The method was checked before this run

- **Self-test:** a 5-second video made of the thumbnail itself, so both faces are certainly in it. The search finds both faces at distance **0**. Comparing whole frames instead finds neither (31 and 31), which is why regions are searched.
- **Decoys:** videos made of two unrelated Instagram photos. The best distances are 19/14 and 9/14: **no match.**

To repeat the self-test:

    ffmpeg -loop 1 -i inputs/thumbnail_DcR9bobtKcF.jpg -t 5 -vf scale=1280:720,format=yuv420p selftest.mp4

then run the same command with `--video self=selftest.mp4` in place of the three `--video` lines.
