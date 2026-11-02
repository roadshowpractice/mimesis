#!/usr/bin/env python3
"""Same voice in both halves of Tim's FB copy of LDC's car reel? resemblyzer speaker embeddings (cosine similarity).
Controls: same speaker (each half split in two; LDC's IG reel vs FB half 1), and other reels' speakers (not identified by us).
claude, 2026-11-01. Run with the dl_wm env python."""
import subprocess, json, sys, numpy as np
from pathlib import Path
from resemblyzer import VoiceEncoder, preprocess_wav
V = Path.home() / "boner_vault/dl_wm_outputs"
FB = V / "2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"
IG = V / "2026-10-13/instagram__Decca9IB4mM/instagram__Decca9IB4mM.mp4"
def wav(src, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + ["-i", str(src)] + (["-t", str(t)] if t else []) + ["-ac", "1", "-ar", "16000", "-f", "f32le", "-"]
    a = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
    return preprocess_wav(a, source_sr=16000)
enc = VoiceEncoder("cpu")
emb = lambda w: enc.embed_utterance(w)
cos = lambda a, b: float(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b))
clips = {
    "fb_half1": wav(FB, 0, 32.433), "fb_half2": wav(FB, 32.433),
    "fb_half1_a": wav(FB, 0, 16.2), "fb_half1_b": wav(FB, 16.2, 16.233),
    "fb_half2_a": wav(FB, 32.433, 18.3), "fb_half2_b": wav(FB, 50.733),
    "ig_ldc": wav(IG),
}
if "--test" in sys.argv:   # known-speaker test (John: "the 2 different people are chad and tb"); default run unchanged
    T = {"chad:DdWodVUBwWy": ("2026-10-12/instagram__DdWodVUBwWy", 0, 15), "chad:DeDux6thmUm": ("2026-10-13/instagram__DeDux6thmUm", 0, 30),
         "tim:1020903481014768": ("2026-10-10/facebook__1020903481014768", 0, 40), "tim:1068335199370200": ("2026-10-16/facebook__1068335199370200", 0, 40),
         "tim:2162868474611710": ("2026-10-16/facebook__2162868474611710", 0, 40), "ldc_ig:DeaBysIPTSx": ("2026-10-13/instagram__DeaBysIPTSx", 0, None)}
    clips = {k: clips[k] for k in ("fb_half1", "fb_half2")}
    for k, (p, ss, t) in T.items(): clips[k] = wav(V / p / (p.split("/")[1] + ".mp4"), ss, t)
    E = {k: emb(w) for k, w in clips.items()}
    ks = list(E); rows = []
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            ga, gb = a.split(":")[0].split("_half")[0], b.split(":")[0].split("_half")[0]
            kind = "same person" if ga == gb and ga in ("chad", "tim") else "chad vs tim" if {ga, gb} == {"chad", "tim"} else f"{ga} vs {gb}"
            rows.append(dict(a=a, b=b, kind=kind, cos=round(cos(E[a], E[b]), 3)))
    for r in sorted(rows, key=lambda r: r["kind"]): print(f"{r['kind']:16s} {r['a']:22s} {r['b']:22s} {r['cos']:.3f}")
    json.dump(rows, open("voice_test.json", "w"), indent=1); sys.exit()
others = ["2026-10-21/instagram__DeVwi1QIjTD", "2026-10-21/instagram__DeZhinGIQJx", "2026-10-21/instagram__DeXxtYkhN_t",
          "2026-10-22/facebook__1558352752727165", "2026-10-22/facebook__1744079277721192", "2026-10-21/instagram__DedEVp6ow5y"]
for o in others:
    clips["other:" + o.split("__")[1]] = wav(next((V / o).glob("*[!d].mp4")), 0, 40)
E = {k: emb(w) for k, w in clips.items()}
pairs = [("fb_half1", "fb_half2", "QUESTION"),
         ("fb_half1_a", "fb_half1_b", "same speaker, same half"), ("fb_half2_a", "fb_half2_b", "same speaker, same half"),
         ("ig_ldc", "fb_half1", "same audio (known)")]
pairs += [(k, h, "other speaker") for k in E if k.startswith("other:") for h in ("fb_half1", "fb_half2")]
pairs += [(a, b, "other vs other") for i, a in enumerate([k for k in E if k.startswith("other:")]) for b in [k for k in E if k.startswith("other:")][i + 1:]]
rows = [dict(a=a, b=b, kind=k, cos=round(cos(E[a], E[b]), 3)) for a, b, k in pairs]
for r in rows: print(f"{r['kind']:26s} {r['a']:26s} {r['b']:26s} {r['cos']:.3f}")
print({k: round(len(w) / 16000, 1) for k, w in clips.items()})
json.dump(rows, open("voice_compare.json", "w"), indent=1)
