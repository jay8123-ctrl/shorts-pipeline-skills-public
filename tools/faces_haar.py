#!/usr/bin/env python3
"""faces_haar.py: sample face boxes with OpenCV's bundled Haar cascade (no model download) -> face_samples.json
(same format as faces_scan.py, so build_short.py reads it).
  python faces_haar.py --src source.mp4 --range 760 830 --range 445 487 --out work/face_samples.json [--every 5]"""
import argparse, json
import cv2
ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True); ap.add_argument("--out", default="work/face_samples.json")
ap.add_argument("--range", nargs=2, type=float, action="append", required=True, metavar=("A", "B"))
ap.add_argument("--every", type=int, default=5)
a = ap.parse_args()
cap = cv2.VideoCapture(a.src); W = int(cap.get(3)); H = int(cap.get(4))
casc = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in ("haarcascade_frontalface_alt2.xml", "haarcascade_frontalface_default.xml")]
out = {"fps": cap.get(cv2.CAP_PROP_FPS), "width": W, "height": H}
for k, (s, e) in enumerate(a.range):
    cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000); S = []; i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if t > e: break
        if i % a.every == 0:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); fl = []
            for c in casc:
                r = c.detectMultiScale(g, 1.1, 6, minSize=(90, 90))
                if len(r):
                    fl = [[int(x + w / 2), int(y + h / 2), int(w), int(h), 1.0] for x, y, w, h in r]; break
            S.append([round(t, 3), fl])
        i += 1
    out[f"R{k}"] = {"range": [s, e], "samples": S, "histcorr": []}
    print(k, len(S), "samples,", sum(1 for _, fl in S if fl), "with face", flush=True)
json.dump(out, open(a.out, "w"))
