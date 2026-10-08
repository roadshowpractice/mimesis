# Round 3: provenance. T5, published before it runs

**T5 is Grok's test.** We asked "Which test would you add?"
([our post](https://x.com/MerrillAnt50522/status/2108222003950051527)), and
[@grok answered](https://x.com/grok/status/2108222187358359766) 43 seconds later:

> Add T5: run diffusion-artifact detectors on middle frames of all 6 pairs and cross-check audio spectrograms against public podcast clips of Riggs.

The question is Grok's. The code and the decision rules below are ours. We publish both before running anything, so
nobody, including us, can move the goalposts afterwards. The commit time is the timestamp.

## The bet being tested

John's bet (Round 3): the data of Instagram **ldsabuseonx** is endogenous to Meta. The "same video" matches between it
and X **@ldsabuse** are *false twinning*: forgeries made to give that appearance.
Grok's read, and ours from Round 2: a human runs it, Justin Riggs or his close team.

## Inputs

- The 6 video pairs from Round 2 (12 files, an X copy and an IG copy of each; listed in `t5_genai_check.py`, data in [`../data/`](../data/)).
- Reference: The Imagination Podcast **S6E87** (Aug 9, 2026, YouTube `FfKGMfjp0F4`), a 10-minute slice with real
  camera video and Riggs's real voice. A person picks, by ear, where Riggs speaks and where the host speaks.

## Rules (fixed now)

**T5a, images.** Frames at 30/50/70% of each file, plus 20 frames of the podcast slice as the known-camera control.
All scored by the open detector `umm-maybe/AI-image-detector` (Hugging Face).
- **Supports the bet** if the pair frames' median AI score is above the control's 95th percentile, for both the X and the IG copies.
- **Against the bet** if they score inside the control range.
- The Aug 3 pair is a screen recording of text, so it's reported apart: the camera control doesn't fit it.

**T5b, voice.** `resemblyzer` speaker embeddings of each file vs Riggs's podcast voice and the host's.
- **Against the bet** if cosine to Riggs is ≥ 0.75 and higher than cosine to the host.
- Stated limit: a good voice clone would also match, so a match doesn't exclude Gen-AI. A mismatch would support the bet.
- Files with no speech are reported as "no speech".

**T5c, spectrograms** (Grok's cross-check). The highest frequency with energy above −60 dB of peak, per file, vs the podcast.
- **A flag for the bet** is a hard cutoff at or below 12 kHz while the podcast reaches higher. That's typical of TTS vocoders.
- Both copies of a pair should agree.

## Predictions, before running

| | T5a images | T5b voice | T5c spectrogram |
|---|---|---|---|
| John | (bet: Gen-AI) | | |
| Claude | inside the control range | matches the podcast Riggs where there's speech | no TTS-style cutoff |
| Grok | asked for T5, gave no T5 prediction; overall it favors "human control by Riggs or close team" | | |

## Run it

```
pip install transformers resemblyzer
python t5_genai_check.py CASE_DIR podcast_slice.mp4 OUT_DIR --riggs <start-end ...> --host <start-end ...>
```

Results will be added here after the run, alongside this unchanged pre-registration.
