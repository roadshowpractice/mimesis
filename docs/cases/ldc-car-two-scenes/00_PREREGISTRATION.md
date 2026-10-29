# Two scenes, mimesis rules — LDC basepoint b0 (claude, 2026-10-29T23:49:36Z, before running)

John: "just run our data in mimesis with 2 scenes...same test as before". John's prediction (X, 23:18 UTC): "match. But what did he add?"
Rules: mimesis bin/compare_x_ig.py THRESHOLDS at commit 72bb4d7, unchanged; its dhash(), hamming(), tokens(), shingles(), longest_run() imported, not copied.
Frames every 2.0 s (THRESHOLDS frame_every_s), whole frame, as compare_x_ig fingerprints video.

Scenes of the Facebook reel 1653357746398669 (69.04 s): S1 = 0 to 32.48 s (the Instagram video's length), S2 = 32.48 to 69.04 s.
Instagram Decca9IB4mM (32.55 s) is the reference.

| scene | images | spoken words |
|---|---|---|
| S1 | each FB frame vs the IG frame at the same time | FB words with start < 32.48 s (whisper.json) vs all IG words (.txt) |
| S2 | each FB frame vs its nearest IG frame at any time ("compare it to scene 1") | FB words with start >= 32.48 s vs all IG words |

Classes per pair (compare_x_ig): IDENTICAL image dHash <= 6, or text 5-word-shingle Jaccard >= 0.8; SAME MATERIAL image <= 12, or shared
run >= 8 words, or >= 2 shared 5-word shingles; otherwise NOTHING SHARED. A scene's class = the class most of its frames reach; all per-frame
distances are reported.
