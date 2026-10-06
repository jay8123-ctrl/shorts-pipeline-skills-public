#!/usr/bin/env python3
"""detect_cuts.py SOURCE A B [--thresh 6] [--ignore-bottom 0.11] : hard-cut candidates between A and B seconds.

Per-frame mean absolute difference (MAD) on a 64x32 grey thumbnail. A peak counts as a cut when it is > thresh AND
> 4x the local median + 2. The bottom strip (tickers, crawls) is ignored. Prints `t  mad  local_median`. Confirm each
candidate on frames either side, or with:  ffmpeg -i SOURCE -vf "select='gt(scene,0.25)',showinfo" -f null -
Then copy the confirmed times into CUTS in the clip config."""
import argparse, json
import cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("a", type=float); ap.add_argument("b", type=float)
ap.add_argument("--thresh", type=float, default=6.0)
ap.add_argument("--ignore-bottom", type=float, default=0.11, help="fraction of frame height to ignore at the bottom")
ap.add_argument("--json", default=None, help="optional path to dump the raw per-frame MAD series")
args = ap.parse_args()

cap = cv2.VideoCapture(args.src); cap.set(cv2.CAP_PROP_POS_MSEC, args.a * 1000)
prev = None; R = []
while True:
    ok, f = cap.read()
    if not ok: break
    t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
    if t > args.b: break
    h = int(f.shape[0] * (1 - args.ignore_bottom))
    g = cv2.cvtColor(cv2.resize(f[:h], (64, 32), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    if prev is not None: R.append((round(t, 3), float(np.abs(g - prev).mean())))
    prev = g
v = np.array([r[1] for r in R]); cuts = []
for i, (t, d) in enumerate(R):
    loc = float(np.median(v[max(0, i - 15):i + 15]))
    if d > args.thresh and d > 4 * loc + 2:
        cuts.append(t); print(t, round(d, 1), round(loc, 2))
print("CUTS =", cuts)
if args.json: json.dump(R, open(args.json, "w"))
