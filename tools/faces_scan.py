#!/usr/bin/env python3
"""faces_scan.py: sample YuNet face boxes across the source ranges that contain your clips -> face_samples.json.

  python3 faces_scan.py --src source.mp4 --model face_detection_yunet_2023mar.onnx --range 175 340 --range 1205 1475 \
      --out work/face_samples.json [--every 6]

Model (public, OpenCV Zoo): https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
Output: {"fps": f, "R0": {"samples": [[t, [[cx, cy, w, h, score], ...]], ...], "histcorr": [[t, corr], ...]}, "R1": ...}
histcorr (HSV histogram correlation between consecutive frames) < 0.75 is a second cut signal."""
import argparse, json
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--range", nargs=2, type=float, action="append", required=True, metavar=("A", "B"))
ap.add_argument("--out", default="face_samples.json")
ap.add_argument("--every", type=int, default=6, help="detect on every Nth frame (6 at 59.94p = 0.1 s)")
args = ap.parse_args()

cv2.setNumThreads(2)
cap = cv2.VideoCapture(args.src)
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
det = cv2.FaceDetectorYN.create(args.model, "", (W, H), 0.6, 0.3, 5000)
out = {"fps": cap.get(cv2.CAP_PROP_FPS), "width": W, "height": H}
for k, (a, b) in enumerate(args.range):
    cap.set(cv2.CAP_PROP_POS_MSEC, a * 1000)
    S, D, prev, i = [], [], None, 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if t > b: break
        hsv = cv2.cvtColor(cv2.resize(f, (160, 90)), cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256]); cv2.normalize(h, h)
        if prev is not None: D.append([round(t, 3), float(cv2.compareHist(prev, h, cv2.HISTCMP_CORREL))])
        prev = h
        if i % args.every == 0:
            _, faces = det.detect(f)
            fl = [] if faces is None else [[round(float(r[0] + r[2] / 2)), round(float(r[1] + r[3] / 2)), round(float(r[2])),
                                            round(float(r[3])), round(float(r[14]), 2)] for r in faces]
            S.append([round(t, 3), fl])
        i += 1
    out[f"R{k}"] = {"range": [a, b], "samples": S, "histcorr": D}
    print(f"R{k}", len(S), "samples; low-corr:", [(c[0], round(c[1], 2)) for c in D if c[1] < 0.75], flush=True)
json.dump(out, open(args.out, "w"))
