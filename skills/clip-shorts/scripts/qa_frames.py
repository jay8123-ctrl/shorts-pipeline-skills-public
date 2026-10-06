#!/usr/bin/env python3
"""qa_frames.py: lean QA for built masters. For each clip it ffprobes the file (resolution, codecs, fps, duration,
size < 45 MB) and writes a contact sheet to <work>/qa/: the card at 1.5 s, every ~8 s, just after each crop switch,
and 0.4 s before the end. Look at the sheet: face in frame, card off faces, subs clear of banners, sensitive content
covered.

  python3 qa_frames.py --out out/ --work work/ [--config clips.py] [--fonts-dir DIR] [CLIP_ID ...]"""
import argparse, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, probe, default_fonts_dir

ap = argparse.ArgumentParser()
ap.add_argument("clips", nargs="*"); ap.add_argument("--out", required=True); ap.add_argument("--work", required=True)
ap.add_argument("--config", default=None); ap.add_argument("--fonts-dir", default=None)
args = ap.parse_args()
cfg = load_config(args.config); OUT = Path(args.out); QA = Path(args.work) / "qa"; QA.mkdir(parents=True, exist_ok=True)
try:
    FNT = ImageFont.truetype(f"{args.fonts_dir or default_fonts_dir()}/NotoSansCJK-Bold.ttc", 30, index=2)
except OSError:
    FNT = ImageFont.load_default()

def grab(f, t, p):
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(f), "-frames:v", "1", "-q:v", "3", str(p)])
    return Image.open(p)

def sheet(ims, labels, path, w=270, h=480, cols=8):
    rows = (len(ims) + cols - 1) // cols; W = Image.new("RGB", (w * cols, h * rows))
    for i, (im, lb) in enumerate(zip(ims, labels)):
        im = im.convert("RGB").resize((w, h)); ImageDraw.Draw(im).text((6, 4), lb, font=FNT, fill=(255, 0, 0))
        W.paste(im, ((i % cols) * w, (i // cols) * h))
    W.save(path, quality=85)

bad = 0
for cid in (args.clips or list(cfg.CLIPS)):
    c = cfg.CLIPS[cid]; name = f"{cid}-{c['slug']}"; f = OUT / f"{name}.mp4"
    if not f.exists(): print(cid, "missing", f); bad += 1; continue
    m = json.load(open(OUT / f"{name}.json")); pr = probe(f)
    d = float(pr["format"]["duration"]); size = int(pr["format"]["size"])
    v = next(s for s in pr["streams"] if s["codec_type"] == "video"); au = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    ok = (v["width"], v["height"]) == (1080, 1920) and v["codec_name"] == "h264" and v.get("profile") == "High" \
         and au and au[0]["codec_name"] == "aac" and size < 45e6 and abs(d - (c["src_out"] - c["src_in"])) < 0.2
    bad += not ok
    ts = {1.5, round(d - 0.4, 2)}; t = 8.0
    while t < d - 2: ts.add(round(t, 2)); t += 8
    for sh in m["framing"]["shots"][1:]: ts.add(round(sh.get("switch_t", sh["t0"]) + 0.3, 2))
    ts = sorted(ts); sheet([grab(f, t, QA / f"{cid}_{t}.jpg") for t in ts], [f"{t:.1f}" for t in ts], QA / f"sheet_{cid}.jpg")
    print("OK " if ok else "FAIL", name, f"{v['width']}x{v['height']} {v['codec_name']} {v.get('profile')} {v['r_frame_rate']}",
          au[0]["codec_name"] if au else "no-audio", f"dur={d:.2f}", f"{size / 1e6:.2f} MB", "sheet:", QA / f"sheet_{cid}.jpg", flush=True)
sys.exit(1 if bad else 0)
