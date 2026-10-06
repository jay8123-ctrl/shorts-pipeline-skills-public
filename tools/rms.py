#!/usr/bin/env python3
"""rms.py AUDIO.wav A B : 50 ms RMS (dBFS) between A and B seconds, one character per 50 ms (20 per row = 1 s).
Use it to confirm a cut point falls in a pause (blank/'.' run) and not mid-word. AUDIO must be 16-bit PCM WAV."""
import sys, wave
import numpy as np

if len(sys.argv) != 4: raise SystemExit(__doc__)
path, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
w = wave.open(path); sr = w.getframerate(); ch = w.getnchannels(); w.setpos(int(a * sr))
x = np.frombuffer(w.readframes(int((b - a) * sr)), dtype=np.int16).astype(np.float32) / 32768
if ch > 1: x = x.reshape(-1, ch).mean(axis=1)
hop = int(0.05 * sr); line = ""
for k, i in enumerate(range(0, len(x) - hop, hop)):
    d = 20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9)
    if k % 20 == 0: line += f"\n{a + k * 0.05:8.2f} "
    line += " .:-=+*#%@"[min(9, max(0, int((d + 60) / 5)))]
print(line)
