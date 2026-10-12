# The every-story, run 1: result

Run on 2026-10-12 at 21:12:38 UTC, exactly as pre-registered in [PREREGISTRATION.md](PREREGISTRATION.md) (published at mimesis
`7d3efc6`, pushed before the run). The command was the published one, word for word. The script checked all 4 input hashes
against [`inputs.SHA256SUMS`](inputs.SHA256SUMS) and printed "inputs: all sha256 match the pre-registration".
Output: [`out/every_story.md`](out/every_story.md), [`out/every_story.json`](out/every_story.json), the video transcript
[`out/video.txt`](out/video.txt), and the console log [`out/run1.log`](out/run1.log).

## Result: John's call does not hold under the pre-registered rules

**Test A, elements: 18 of 32 found, not 32 of 32. Fails.**

| | video | deseret | foxnews | whitehouse |
|---|---|---|---|---|
| E1 girl kidnapped in Central America | yes | yes | yes | yes |
| E2 11 years old | yes | no | no | yes |
| E3 groomed for two years | yes | no | no | yes |
| E4 boy kidnapped in Mexicali | yes | yes | yes | no |
| E5 a wall in the boy's story | yes | no | yes | no |
| E6 Calexico port of entry | no | yes | yes | no |
| E7 rescued in San Bernardino | yes | no | no | no |
| E8 the wall was the difference | yes | no | no | yes |

**Test B, word for word (match = 95% or more of the video's 532 words, in order): no text matches. Fails.**

| Text | Video words found | Share |
|---|---|---|
| deseret | 133 / 532 | 25.0% |
| foxnews | 91 / 532 | 17.1% |
| whitehouse | 275 / 532 | 51.7% |

## Read after the run (not part of the scoring)

Everything below was looked at only after the result above was written. It does not change the verdict.

**1. The 2019 White House transcript leaves out the middle of his remarks.** The American Presidency Project prints
his opening, the girl story up to "the clientele that's the big money", then the bracketed line
**"[Mr. Ballard continued his remarks, concluding as follows.]"**, and picks up again at "The difference between those
two cases is two plus two equals four. The wall was the difference."

That gap is why the transcript has no Mexicali boy (E4–E7) and why Test B stops at 51.7%.

**2. Where the transcript does print his words, the video says them word for word.** We lined up the transcript's
printed Ballard text (195 words) against the video, with the same word rules as the script. **192 of 195 (98.5%)** are in
the video, in the same order. The three misses are "I"/"I've" and "Sánchez", which the word rules split into two pieces.

The video holds **254 words exactly where the transcript has the bracket**: "They brought this little girl through a
part of the southern border where there was no wall…", down to "…rescued 12 other children in San Bernardino,
California." Its ending ("We are having to do operations in Mexico… fly swatter, which is the wall… Thank you very
much. I appreciate it.") is also not printed.

**3. So our "2025 video" is footage of the Feb 1, 2019 meeting itself** (the transcript page's date). The opening
("Thank you so much, Mr. President…") is the same, and so is "Olga Sánchez, just last month". "2025" is when the
first mimesis script got its copy, or when it was going round again ("as they rolled out the same script"). It is not
when it was said. The Deseret op-ed (Feb 4, 2019) came three days after the meeting.

**4. The video's E6 "no" is a transcription miss.** This run's Whisper small heard "the Mexico port of entry". On
2026-10-10 the same model heard "Calexico Port of Entry" (THE CUT, `QUOTES_CHECKED.md`). Scored as pre-registered.

**5. The op-eds tell the same two cases in other words.** Fox has the Mexicali boy and the wall in his story (E4, E5).
Deseret has Mexicali and Calexico but not the wall within 400 characters (E5). Neither has "11 years old" or "groomed
for two years" in those words, and neither repeats the speech word for word (17–25%).

## How to check this yourself

1. Fetch the three pages from the links in the pre-registration. Pages change over time, so your hashes may differ
   from ours. Ours are in `inputs.SHA256SUMS`.
2. On the [transcript page](https://www.presidency.ucsb.edu/documents/remarks-meeting-human-trafficking-the-mexico-united-states-border-and-exchange-with),
   find "Mr. Ballard continued his remarks, concluding as follows."
3. Read [`out/video.txt`](out/video.txt) beside it. The words before and after the bracket are the same as the video's,
   and the Mexicali boy sits in the gap.
4. Re-run: the command in the pre-registration. It stops if your inputs are not byte for byte ours.

Hashes of the outputs, as written by the run:

```
3fddf8804b695f376a911399768ff6c512220f1552d397e6940bfbc291ddf17d  out/every_story.json
b4f451b86c9c07681651ec4580d590472919e22ffd38ef0e27c6521f10a070fe  out/every_story.md
34622a0d3639ecb0a2d950acd8ab479e72c8af068cff493e1232562667ed3ad5  out/video.txt
```
