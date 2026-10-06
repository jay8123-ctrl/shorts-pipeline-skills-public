#!/usr/bin/env python3
"""edge_check.py: re-transcribe the first and last N seconds of finished masters to catch clipped words.

  python3 edge_check.py out/*.mp4 [--seconds 4] [--language en] [--model medium]

Read the HEAD/TAIL lines: the first word should be the planned opening word, and the last should be a complete
sentence end. A cut-off word at either edge means the in/out point must move to the pause (check with rms.py)."""
import argparse, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from asr import transcribe

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+"); ap.add_argument("--seconds", type=float, default=4.0)
ap.add_argument("--language", default="en"); ap.add_argument("--model", default="medium")
args = ap.parse_args()
tmp = Path(tempfile.mkdtemp()) / "edge.wav"
for f in sorted(args.files):
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
    res = []
    for a, b in [(0, args.seconds), (max(0, d - args.seconds), d)]:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", f, "-vn", "-ar", "16000", "-ac", "1", str(tmp)], check=True)
        res.append(" ".join(f"{w}({s + a:.2f}-{e + a:.2f})" for s, e, w in transcribe(tmp, args.language, args.model)))
    print(Path(f).name, f"dur={d:.2f}\n  HEAD: {res[0]}\n  TAIL: {res[1]}", flush=True)
