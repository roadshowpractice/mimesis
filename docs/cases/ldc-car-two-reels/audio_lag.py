#!/usr/bin/env python3
"""Audio offset between LDC's at-work reel (DeaBysIPTSx) and FB 1653357746398669 from 32.433 s on: cross-correlation of
the 8 kHz mono envelopes (100 Hz frames), then frames from both at matched moments. claude, 2026-11-01."""
import subprocess, json
from pathlib import Path
import numpy as np
V = Path.home() / "boner_vault/dl_wm_outputs"
FB = V / "2026-10-16/facebook__1653357746398669/facebook__1653357746398669.mp4"
A = V / "2026-10-13/instagram__DeaBysIPTSx/instagram__DeaBysIPTSx.mp4"
def env(p, ss=0):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", str(p), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32)
    e = np.abs(a[: len(a) // 80 * 80]).reshape(-1, 80).mean(1); return (e - e.mean()) / e.std()
ea, ef = env(A), env(FB, 32.433)
best = (None, -9)
for lag in range(-600, 601):   # A time = FB-half-2 time + lag/100
    x, y = (ea[lag:], ef) if lag >= 0 else (ea, ef[-lag:])
    k = min(len(x), len(y)); r = float(np.corrcoef(x[:k], y[:k])[0, 1])
    if r > best[1]: best = (lag, r)
out = {"lag_s_A_minus_FBhalf2": best[0] / 100, "r": round(best[1], 3)}
json.dump(out, open("audio_lag.json", "w"), indent=1); print(out)
