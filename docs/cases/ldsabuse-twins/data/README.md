# Public data: X @ldsabuse vs Instagram ldsabuseonx (mimesis case, Oct 2026)

| File | What it is |
|---|---|
| `x_posts.tsv` | all 115 posts and replies by @ldsabuse on the 7 days (PDT), full text, link, number of attached media files |
| `ig_posts.tsv` | all 32 posts on the ldsabuseonx grid: time, who started it, co-authors, full caption, link |
| `video_matches.tsv` | every video comparison: the 6 matches, the 1 length coincidence, and the 3 posts with no same-day match, with frame fingerprint distances |
| `files_inventory.csv` | ffprobe/EXIF facts for every media file on both sides (hash, codec, size, duration, tags) |
| `custody_hashes.tsv` | sha256 of every file collected, with UTC time and step; anyone given an original can check it against this list |
| `ig_capture_manifest.public.json` | the Instagram capture's manifest (method, parameters, tool versions, output hashes) |

Redaction: the logged-in accounts used to collect the data, their user IDs, local machine paths and session cookies are not published. Account identifiers are replaced by keyed hashes like `[acct:1a2b3c…]` (HMAC-SHA256 with a private key), so the same account always gets the same tag. Original files' sha256 values are unchanged.

Media files (the videos and images themselves) are not redistributed here; every post links to its original. Method and code: `bin/compare_x_ig.py` in this repository.
