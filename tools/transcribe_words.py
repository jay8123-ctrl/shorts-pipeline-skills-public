#!/usr/bin/env python3
"""transcribe_words.py: word-level timestamps over overlapping windows (timings are steadier than one long pass).

  ffmpeg -i source.mp4 -vn -ac 1 -ar 16000 audio16k.wav
  python3 transcribe_words.py --audio audio16k.wav --range 170 345 --range 1200 1480 --out work/words.json \
      [--model medium] [--language en] [--window 30] [--step 22] [--prompt "Elon Musk, Jensen Huang, Claude"]

Writes words.json = [[start, end, word], ...] in source seconds. Each window keeps only the words whose start falls
in its own slice (overlap split at the midpoint), so there are no duplicates. The raw per-window output goes to
<out>_windows.json for hand checks. Re-run doubtful spots with a tighter --range, --vad and --prompt, and patch
words.json or the config's WORD_FIXES.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from asr import transcribe

ap = argparse.ArgumentParser()
ap.add_argument("--audio", required=True)
ap.add_argument("--range", nargs=2, type=float, action="append", required=True, metavar=("A", "B"))
ap.add_argument("--out", default="words.json")
ap.add_argument("--model", default="medium")
ap.add_argument("--language", default="en")
ap.add_argument("--window", type=float, default=30)
ap.add_argument("--step", type=float, default=22)
ap.add_argument("--prompt", default=None)
ap.add_argument("--vad", action="store_true")
args = ap.parse_args()

tmp = Path(tempfile.mkdtemp()) / "win.wav"
raw, words = [], []
for A, B in args.range:
    wins = []; t = A
    while t < B:
        wins.append((t, min(t + args.window, B)))
        if t + args.window >= B: break
        t += args.step
    for i, (a, b) in enumerate(wins):
        lo = a if i == 0 else (a + wins[i - 1][1]) / 2
        hi = b if i == len(wins) - 1 else (wins[i + 1][0] + b) / 2
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", args.audio, "-ac", "1", "-ar", "16000", str(tmp)], check=True)
        ws = [[round(s + a, 2), round(e + a, 2), w] for s, e, w in transcribe(tmp, args.language, args.model, args.prompt, args.vad)]
        raw.append({"win": [a, b], "words": ws})
        words += [w for w in ws if lo <= w[0] < hi]
        print(f"[{a:.0f}-{b:.0f}]", " ".join(f"{w[2]}({w[0]:.2f})" for w in ws), flush=True)
words.sort()
out = Path(args.out)
out.write_text(json.dumps(words))
out.with_name(out.stem + "_windows.json").write_text(json.dumps(raw, indent=1))
print(f"{len(words)} words -> {out}")
