"""Gen-AI count trial (2026-10-10): the same three checks as Round 3's T5, run on @timballard89's 5 Oct 7 posts.

Existing tools first: frame(), wav(), ai_score() and top_freq() are imported unchanged from
../ldsabuse-twins/round3/t5_genai_check.py. Only the inputs and the per-post report are new.

  A images : AI-image detector (umm-maybe/AI-image-detector) on 9 frames per post, at 10%..90%;
             control = 20 frames of a third-party phone video of Tim on stage (Da7-1LpIR89, dr.venus_sh)
  B voice  : resemblyzer speaker embedding of each post vs Tim's voice in the control video
  C spectrum: highest frequency with energy above -60 dB of peak, per post vs the control

Usage:
  python genai_count.py POSTS_DIR CONTROL.mp4 OUT_DIR --tim 30-60 95-120
    POSTS_DIR holds <shortcode>.mp4 for the 5 posts (our downloads, NOT the watermarked copies)
    --tim: start-end seconds INTO the control where Tim speaks (picked by ear, written down before running)
Needs: pip install transformers resemblyzer scipy matplotlib
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("t5", HERE.parent / "ldsabuse-twins" / "round3" / "t5_genai_check.py")
t5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t5)

POSTS = ["DeNlpDSI691", "DeNnnzboyBs", "DeOAfQwonHi", "DeOBQw2oqTA", "DeOEQmtoQjd"]  # posting order, Oct 7 PT
FRACTIONS = [i / 10 for i in range(1, 10)]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("posts_dir"); ap.add_argument("control"); ap.add_argument("out")
    ap.add_argument("--tim", nargs="+", required=True, help="start-end seconds in the control where Tim speaks")
    a = ap.parse_args()
    posts_dir, ctrl, out = Path(a.posts_dir), Path(a.control), Path(a.out)
    (out / "spectrograms").mkdir(parents=True, exist_ok=True)
    from transformers import pipeline
    from resemblyzer import VoiceEncoder
    clf = pipeline("image-classification", model=t5.MODEL)
    enc = VoiceEncoder("cpu")
    res = {"model": t5.MODEL, "inputs": {}, "control": {}, "posts": []}

    cd = t5.dur(ctrl)
    scores = [t5.ai_score(clf, t5.frame(ctrl, cd * (i + 0.5) / 20)) for i in range(20)]
    res["inputs"]["control"] = {"file": ctrl.name, "sha256": sha256(ctrl)}
    res["control"] = {"ai_scores": scores, "p95": float(np.nanpercentile(scores, 95)), "median": float(np.nanmedian(scores)),
                      "tim_segments": a.tim,
                      "top_freq_hz": t5.top_freq(ctrl, out / "spectrograms" / "control.png", "control: Da7-1LpIR89")}
    tim = enc.embed_speaker([t5.wav(ctrl, ss=s, to=e) for s, e in t5.segs(a.tim)])
    c = res["control"]
    print(f"control: AI median {c['median']:.3f}  p95 {c['p95']:.3f}  top freq {c['top_freq_hz']:.0f} Hz")

    print("n  post          AI median  A          cos_tim  top_freq_Hz  C")
    for n, code in enumerate(POSTS, 1):
        p = posts_dir / f"{code}.mp4"
        res["inputs"][code] = {"file": p.name, "sha256": sha256(p)}
        d = t5.dur(p)
        s = [t5.ai_score(clf, t5.frame(p, d * f)) for f in FRACTIONS]
        med = float(np.nanmedian(s))
        audio = t5.wav(p)
        cos = float(np.dot(enc.embed_utterance(audio), tim)) if audio.size > 16000 * 3 and np.abs(audio).max() > 0.01 else float("nan")
        tf = t5.top_freq(p, out / "spectrograms" / f"{n}_{code}.png", f"{n} {code}")
        row = {"n": n, "post": code, "ai_scores": s, "ai_median": med,
               "A_ai_imagery": bool(med > c["p95"]),
               "B_cos_tim": cos, "B_voice": ("no speech" if np.isnan(cos) else "matches Tim" if cos >= 0.75 else "does not match Tim"),
               "C_top_freq_hz": tf, "C_tts_cutoff": bool(tf <= 12000 and c["top_freq_hz"] > 12000) if not np.isnan(tf) else None}
        res["posts"].append(row)
        print(f"{n}  {code}  {med:9.3f}  {'AI' if row['A_ai_imagery'] else '-':9s}  {cos:7.3f}  {tf:11.0f}  "
              f"{'cutoff' if row['C_tts_cutoff'] else '-'}")

    res["count_A"] = sum(r["A_ai_imagery"] for r in res["posts"])
    print(f"\nCount by check A (frames above the control's p95): {res['count_A']} of 5")
    print("B: cos >= 0.75 = same voice as Tim in the control (a good clone would also match)")
    print("C: top freq <= 12 kHz while the control goes higher = TTS-style cutoff (a flag, not proof)")
    (out / "results.json").write_text(json.dumps(res, indent=1))
    print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
