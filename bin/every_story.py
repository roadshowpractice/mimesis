#!/usr/bin/env python3
"""Line up the 2025 White House video of Tim Ballard's "every-story" against three 2019 texts.

This is the job mimesis was first written for (bin/compare_sources.py, June 2025), redone with the inputs saved
and hashed first. Pre-registration: docs/cases/every-story/PREREGISTRATION.md. Run it only after that is pushed.

  python bin/every_story.py CASE_DIR --video VIDEO.mp4 --text NAME=PAGE.html [--text ...] [--model small]

Steps:
  1. sha256 of every input, checked against CASE_DIR/inputs.SHA256SUMS (stops on any mismatch).
  2. Transcribe the video with openai-whisper (--model, default small), English, temperature 0.
  3. Text of each page = its <p> paragraphs (lib/mimesis/article.py).
  4. Test A, elements: each regex in ELEMENTS searched in the video transcript and in each text.
  5. Test B, word for word: the video's words lined up (difflib) against each text; share of the video's words
     found in order. Every unmatched video word is listed.
Writes CASE_DIR/out/every_story.json, every_story.md and the transcript (video.txt). Nothing is fetched.
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from mimesis.article import extract_article_text  # noqa: E402

# Test A. Fixed before the run; see the pre-registration for why each one.
ELEMENTS = [
    ("E1", "girl kidnapped in Central America", r"central america"),
    ("E2", "11 years old", r"\b(11|eleven)[- ]years?[- ]old"),
    ("E3", "groomed for two years", r"groom\w*[^.]{0,60}\b(two|2) years"),
    ("E4", "boy kidnapped in Mexicali", r"mexicali"),
    ("E5", "a wall in the boy's story", None),  # "wall" within 400 characters after the first "Mexicali"
    ("E6", "Calexico port of entry", r"calexico"),
    ("E7", "rescued in San Bernardino", r"san bernardino"),
    ("E8", "the wall was the difference", r"wall (was|made) (all )?the difference"),
]
B_THRESHOLD = 0.95  # Test B "match" = at least this share of the video's words, in order
NUMBERS = {str(i): w for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def words(text):
    out = []
    for w in re.findall(r"[a-z0-9']+", text.lower().replace("’", "'")):
        out.append(NUMBERS.get(w, w))
    return out


def element_hits(text):
    low = text.lower().replace("\n", " ")
    hits = {}
    for eid, _, rx in ELEMENTS:
        if rx is None:
            i = low.find("mexicali")
            hits[eid] = i >= 0 and re.search(r"\bwall", low[i:i + 400]) is not None
        else:
            hits[eid] = re.search(rx, low) is not None
    return hits


def line_up(video_words, text_words):
    sm = difflib.SequenceMatcher(None, video_words, text_words, autojunk=False)
    matched = [False] * len(video_words)
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            matched[b.a + k] = True
    missing = [(i, video_words[i]) for i, m in enumerate(matched) if not m]
    return sum(matched), missing


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case")
    ap.add_argument("--video", required=True)
    ap.add_argument("--text", action="append", required=True, help="NAME=page.html")
    ap.add_argument("--model", default="small")
    a = ap.parse_args()
    case = Path(a.case)
    texts = dict(t.split("=", 1) for t in a.text)

    # 1. inputs must be the hashed ones
    want = {}
    for line in (case / "inputs.SHA256SUMS").read_text().splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            want[name.strip()] = h
    for p in [a.video] + list(texts.values()):
        got, name = sha256(p), Path(p).name
        if want.get(name) != got:
            sys.exit(f"STOP: {name} sha256 {got} is not the pre-registered one ({want.get(name)})")
    print("inputs: all sha256 match the pre-registration")

    # 2. transcript
    import whisper
    model = whisper.load_model(a.model)
    tr = model.transcribe(a.video, language="en", temperature=0)
    video_text = tr["text"].strip()
    out = case / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "video.txt").write_text(video_text + "\n")

    # 3-5
    vw = words(video_text)
    res = {"run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "whisper_model": a.model,
           "video": Path(a.video).name, "video_words": len(vw), "sources": {}}
    res["sources"]["video"] = {"elements": element_hits(video_text)}
    for name, page in texts.items():
        t = extract_article_text(page)
        n, missing = line_up(vw, words(t))
        res["sources"][name] = {"elements": element_hits(t), "words_matched": n,
                                "share": round(n / len(vw), 4), "unmatched": missing}
    all_a = all(all(s["elements"].values()) for s in res["sources"].values())
    res["test_A_all_elements_everywhere"] = all_a
    (out / "every_story.json").write_text(json.dumps(res, indent=2) + "\n")

    names = list(res["sources"])
    md = [f"# every-story run ({res['run_utc']}, whisper {a.model})", "", "## Test A: elements", "",
          "| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for eid, label, _ in ELEMENTS:
        md.append(f"| {eid} {label} | " + " | ".join(
            "yes" if res["sources"][s]["elements"][eid] else "**no**" for s in names) + " |")
    md += ["", f"All elements in all four: **{'YES' if all_a else 'NO'}**", "",
           "## Test B: the video's words, in order, found in each text", ""]
    for name in texts:
        s = res["sources"][name]
        verdict = "match" if s["share"] >= B_THRESHOLD else "no match"
        md.append(f"- **{name}**: {s['words_matched']}/{len(vw)} = {s['share']:.1%} ({verdict})")
        md.append(f"  - unmatched: {' '.join(w for _, w in s['unmatched'][:120])}"
                  + (" …" if len(s["unmatched"]) > 120 else ""))
    (out / "every_story.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
