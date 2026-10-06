#!/usr/bin/env python3
"""cut_check.py: for every cut inside a clip, find the first OUTPUT frame of the new shot (same -ss/fps chain as the
build) and write switch.json {clip_id: {cut_src_t: switch_t}}, where switch_t is halfway between the last old frame
and the first new frame (clip seconds). build_short.py reads it from --work so the crop moves on the exact frame.

  python3 cut_check.py --src source.mp4 --work work/ [--config clips.py] [--fps auto]"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, probe, video_stream, out_fps, fps_float

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True); ap.add_argument("--work", required=True)
ap.add_argument("--config", default=None); ap.add_argument("--fps", default="auto")
args = ap.parse_args()
cfg = load_config(args.config)
FPS = out_fps(video_stream(probe(args.src))["r_frame_rate"], args.fps); FR = fps_float(FPS)
out = {}
for cid, c in cfg.CLIPS.items():
    a, b = c["src_in"], c["src_out"]; cuts = [t for t in getattr(cfg, "CUTS", []) if a < t < b]
    if not cuts: continue
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", args.src, "-an",
                                   "-vf", f"fps={FPS},scale=64:36,format=gray", "-f", "rawvideo", "-"])
    F = np.frombuffer(raw, np.uint8).reshape(-1, 36, 64).astype(np.float32)
    d = np.abs(np.diff(F, axis=0)).mean(axis=(1, 2))          # d[i] = difference between frame i and i+1
    out[cid] = {}
    for ct in cuts:
        rel = ct - a; i0 = int(rel * FR)
        win = range(max(0, i0 - 6), min(len(d), i0 + 6))
        j = max(win, key=lambda k: d[k]); first_new = j + 1
        sw = round((first_new - 0.5) / FR, 3)
        out[cid][str(round(ct, 3))] = sw
        print(cid, ct, "rel", round(rel, 3), "first new frame", first_new, "peak", round(float(d[j]), 1), "switch", sw)
Path(args.work).mkdir(parents=True, exist_ok=True)
json.dump(out, open(Path(args.work) / "switch.json", "w"), indent=1)
