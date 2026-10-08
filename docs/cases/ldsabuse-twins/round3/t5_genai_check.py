"""T5 (from Grok, rules in 01_FALSIFY_PLAN.md): Gen-AI checks on the 6 X<->IG video pairs vs a real podcast slice.

  T5a images : AI-image detector on frames at 30/50/70% of each file; control = 20 frames of the podcast slice
  T5b voice  : resemblyzer speaker embedding of each file vs Riggs / host reference segments of the podcast
  T5c spectro: highest frequency with energy above -60 dB of peak; spectrogram PNGs side by side

Usage:
  python t5_genai_check.py CASE_DIR PODCAST.mp4 OUT_DIR --riggs 120-140 300-330 --host 10-30 200-215
  (segment times are seconds INTO the podcast slice file; John picks them by ear)
Needs: pip install transformers resemblyzer   (model umm-maybe/AI-image-detector downloads on first run)
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np

PAIRS = [  # (label, X file, IG file) from out/files_report.md
    ("Jul31", "x/media/2083336195715543493_0.mp4", "ig/media/Dbed4OEN_9d/instagram__Dbed4OEN_9d.mp4"),
    ("Aug03_screenrec", "x/media/2084516126403199292_0.mp4", "ig/media/Dbm17ScJJmq/instagram__Dbm17ScJJmq.mp4"),
    ("Aug11", "x/media/2087299108016886089_0.mp4", "ig/media/Db6ohLRp-rK/instagram__Db6ohLRp-rK.mp4"),
    ("Aug12", "x/media/2087734401102741732_0.mp4", "ig/media/Db9uvtKNmYf/instagram__Db9uvtKNmYf.mp4"),
    ("Aug24a", "x/media/2092055879013072972_0.mp4", "ig/media/DccZ0o1NmEo/instagram__DccZ0o1NmEo.mp4"),
    ("Aug24b", "x/media/2092085370343108922_0.mp4", "ig/media/DcckYqIBFZ2/instagram__DcckYqIBFZ2.mp4"),
]
MODEL = "umm-maybe/AI-image-detector"


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def frame(p, t):
    from PIL import Image
    import io
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(p), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"])
    return Image.open(io.BytesIO(raw)).convert("RGB")


def wav(p, sr=16000, ss=None, to=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + (["-to", str(to)] if to is not None else [])
    cmd += ["-i", str(p), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.check_output(cmd), np.float32)


def ai_score(clf, img):
    out = clf(img)
    s = [o["score"] for o in out if any(k in o["label"].lower() for k in ("artificial", "fake", "ai"))]
    return float(s[0]) if s else float("nan")


def top_freq(p, out_png, title):
    """highest frequency with energy above -60 dB of the peak (44.1 kHz analysis), and a spectrogram PNG"""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.signal import spectrogram
    x = wav(p, sr=44100)
    if x.size < 44100:
        return float("nan")
    f, t, S = spectrogram(x, fs=44100, nperseg=4096, noverlap=2048)
    spec = 10 * np.log10(S.mean(axis=1) + 1e-20)
    above = f[spec > spec.max() - 60]
    plt.figure(figsize=(8, 3)); plt.pcolormesh(t, f / 1000, 10 * np.log10(S + 1e-20), shading="auto", vmin=spec.max() - 90)
    plt.ylabel("kHz"); plt.xlabel("s"); plt.title(title, fontsize=9); plt.colorbar(label="dB"); plt.tight_layout()
    plt.savefig(out_png, dpi=90); plt.close()
    return float(above.max()) if above.size else float("nan")


def segs(xs):
    return [tuple(float(v) for v in s.split("-")) for s in xs]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case"); ap.add_argument("podcast"); ap.add_argument("out")
    ap.add_argument("--riggs", nargs="+", required=True, help="start-end seconds where Riggs speaks")
    ap.add_argument("--host", nargs="+", required=True, help="start-end seconds where the host speaks")
    a = ap.parse_args()
    case, pod, out = Path(a.case), Path(a.podcast), Path(a.out)
    (out / "spectrograms").mkdir(parents=True, exist_ok=True)
    from transformers import pipeline
    from resemblyzer import VoiceEncoder
    clf = pipeline("image-classification", model=MODEL)
    enc = VoiceEncoder("cpu")
    res = {"model": MODEL, "pairs": [], "control": {}}

    # control: 20 frames spread over the podcast slice
    pd = dur(pod)
    ctrl = [ai_score(clf, frame(pod, pd * (i + 0.5) / 20)) for i in range(20)]
    res["control"] = {"ai_scores": ctrl, "p95": float(np.nanpercentile(ctrl, 95)), "median": float(np.nanmedian(ctrl))}
    riggs = enc.embed_speaker([wav(pod, ss=s, to=e) for s, e in segs(a.riggs)])
    host = enc.embed_speaker([wav(pod, ss=s, to=e) for s, e in segs(a.host)])
    res["control"]["top_freq_hz"] = top_freq(pod, out / "spectrograms" / "podcast_S6E87.png", "podcast S6E87 slice (reference)")
    print(f"control frames: median {res['control']['median']:.3f}  p95 {res['control']['p95']:.3f}  "
          f"podcast top freq {res['control']['top_freq_hz']:.0f} Hz")

    print("pair            side  AI(30/50/70%)          cos_riggs cos_host  top_freq_Hz")
    for label, xf, igf in PAIRS:
        for side, rel in (("X", xf), ("IG", igf)):
            p = case / rel
            d = dur(p)
            scores = [ai_score(clf, frame(p, d * f)) for f in (0.3, 0.5, 0.7)]
            audio = wav(p)
            if audio.size > 16000 * 3 and np.abs(audio).max() > 0.01:
                e = enc.embed_utterance(audio)
                cr, ch = float(np.dot(e, riggs)), float(np.dot(e, host))
            else:
                cr = ch = float("nan")
            tf = top_freq(p, out / "spectrograms" / f"{label}_{side}.png", f"{label} {side}: {rel}")
            row = dict(pair=label, side=side, file=rel, ai_scores=scores, cos_riggs=cr, cos_host=ch, top_freq_hz=tf)
            res["pairs"].append(row)
            print(f"{label:15s} {side:3s}  {' '.join(f'{s:.3f}' for s in scores)}   {cr:8.3f} {ch:8.3f}  {tf:9.0f}")

    cam = [r for r in res["pairs"] if "screenrec" not in r["pair"]]
    for side in ("X", "IG"):
        med = float(np.nanmedian([s for r in cam if r["side"] == side for s in r["ai_scores"]]))
        res[f"median_ai_{side}"] = med
        print(f"T5a {side}: median AI score of camera pairs {med:.3f} vs control p95 {res['control']['p95']:.3f} -> "
              f"{'ABOVE (supports bet)' if med > res['control']['p95'] else 'inside control range (against bet)'}")
    print("T5b rule: cos_riggs >= 0.75 and > cos_host = same voice as podcast Riggs (against bet; clones would also match)")
    print("T5c rule: top_freq <= 12000 Hz while the podcast goes higher = TTS-style cutoff (flag for bet)")
    (out / "t5_results.json").write_text(json.dumps(res, indent=1))
    print("wrote", out / "t5_results.json", "and", out / "spectrograms")


if __name__ == "__main__":
    main()
