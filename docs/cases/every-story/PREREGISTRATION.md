# Pre-registration: the every-story, 2025 video vs three 2019 texts

**Status: NOT RUN.** This file, the script and the input hashes are published before the run. The commit time is the
timestamp. The result will go in its own file, and this one will stay unchanged.

## Why

This is the job mimesis was first written for. Its first script (`bin/compare_sources.py`, June 25, 2025) says:
"compares 4 versions of TB's 'every-story'… data/original is from 2025! as they rolled out the same script… 3 sources
from 2019". We are doing it again, with every input saved and hashed first.

## Inputs (sha256 in [`inputs.SHA256SUMS`](inputs.SHA256SUMS))

| Name | What | Where |
|---|---|---|
| video | The 2025 White House video of his border remarks, 2:53 (our copy, YouTube `i5ID7VTlLuw`) | not in this repo |
| deseret | Deseret News op-ed, Feb 4, 2019: "I've fought sex trafficking at the border. This is why we need a wall" | [deseret.com](https://www.deseret.com/2019/2/4/20664993/tim-ballard-i-ve-fought-sex-trafficking-at-the-border-this-is-why-we-need-a-wall/) |
| foxnews | Fox News op-ed: "I've fought sex trafficking as a DHS special agent. We need to build the wall for the children" | [foxnews.com](https://www.foxnews.com/opinion/ive-fought-sex-trafficking-as-a-dhs-special-agent-we-need-to-build-the-wall-for-the-children) |
| whitehouse | The 2019 White House meeting on human trafficking at the border, full transcript | [The American Presidency Project](https://www.presidency.ucsb.edu/documents/remarks-meeting-human-trafficking-the-mexico-united-states-border-and-exchange-with) |

The three pages were saved on 2026-10-12 and hashed without being read. Their text is the page's `<p>` paragraphs,
so site boilerplate comes along. Known about the video: our old watermark timer suggests about 16 s are missing
between 0:20 and 2:01 of our copy (THE CUT notes, 2026-10-10).

## Prediction (locked)

| Player | Call |
|---|---|
| John ([@Jimzz1e](https://x.com/Jimzz1e)) | **"100% match… wall and all"**, the way it came out the first time, in June 2025 |

## Tests and decision rules

The video is transcribed by openai-whisper **small** (English, temperature 0) inside the run.

**Test A, the elements of the story.** Each is searched (case-insensitive) in the video transcript and in each text:

| | Element | Searched as |
|---|---|---|
| E1 | girl kidnapped in Central America | `central america` |
| E2 | 11 years old | `(11\|eleven)[- ]years?[- ]old` |
| E3 | groomed for two years | `groom…` then `two/2 years` within 60 characters, same sentence |
| E4 | boy kidnapped in Mexicali | `mexicali` |
| E5 | a wall in the boy's story | `wall` within 400 characters after the first `mexicali` |
| E6 | Calexico port of entry | `calexico` |
| E7 | rescued in San Bernardino | `san bernardino` |
| E8 | the wall was the difference | `wall (was\|made) (all )?the difference` |

John's call holds on Test A if **all 8 elements are in all 4** (32 of 32).

**Test B, word for word.** The video's words (lower case, punctuation dropped, numbers 0–20 written as words) are
lined up against each text's words with Python `difflib`. Score = share of the video's words found in order.
**Match = 95% or more.** (Whisper misspellings cost a few words even on the same audio: on 10-10 the same method gave
245 of 249 for the re-post.) Every unmatched video word is listed, so a reader can see what the misses are.

John's call holds on Test B if **all three texts match**. Overall: **holds** if A and B both hold; otherwise it says
which part failed.

## Command (run after this is pushed, word for word)

```
source venv/bin/activate
python bin/every_story.py docs/cases/every-story \
  --video data/every_story/raw/youtube__i5ID7VTlLuw.mp4 \
  --text deseret=data/every_story/raw/deseret_2019-02-04.html \
  --text foxnews=data/every_story/raw/foxnews_op-ed.html \
  --text whitehouse=data/every_story/raw/ucsb_whitehouse_2019.html
```

The script stops if any input's sha256 differs from `inputs.SHA256SUMS`. Output: `docs/cases/every-story/out/`.
