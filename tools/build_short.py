#!/usr/bin/env python3
"""build_short.py: build 9:16 YouTube Shorts masters from a landscape source.

Per clip id in the config (clips.py):
  word timings -> karaoke line ends -> ASS (\\k per character, zh-Hans) -> title-card PNG
  -> one fixed crop x per shot (manual, or from YuNet face samples, else centre) -> 2-pass x264 sized to TARGET_MB
  -> still JPG + metadata JSON.

Usage:
  python3 build_short.py --src source.mp4 --work work/ --out out/ [--config clips.py] [--fonts-dir DIR]
                         [--target-mb 40.5] [--fps auto] [CLIP_ID ...]          (no ids = all clips)

Inputs read from --work (all optional except words.json):
  words.json         [[start, end, word], ...] source seconds (transcribe_words.py)
  face_samples.json  YuNet samples (faces_scan.py). Missing -> centre crop unless MANUAL_X gives one
  switch.json        frame-exact crop switch times per cut (cut_check.py). Missing -> switch at the cut time
Outputs in --out: NN-slug.mp4, NN-slug.ass, NN-slug-still.jpg, NN-slug.json
Portrait/4:5 sources are not handled here; use the blurred-fill recipe in SKILL.md.
"""
import argparse, json, os, re, shutil, subprocess, sys, statistics as st
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, probe, video_stream, out_fps, default_fonts_dir

# ------------------------------------------------------------------ tunable constants (defaults; config may override some)
TARGET_MB = 40.5                 # 2-pass target per master (hard limit 45 MB; YouTube Studio browser upload limit 50 MB)
MAX_VKBPS = 6000                 # video bitrate cap
AUDIO_KBPS = 128
CARD_Y_DEFAULT = 1120            # title card top edge in the 1080x1920 output (keep below faces, above subs)
SUB_MARGIN_V_DEFAULT = 370       # karaoke bottom margin
SUB_MARGIN_V_LOGO_DEFAULT = 500  # margin for lines that would sit on a burned-in logo (config LOGO)
MAX_LINE_CHARS = 12.5            # Chinese chars per line (Latin word = len/2.5)
PUNCT = "，。！？、；：…“”《》·—%"

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("clips", nargs="*")
ap.add_argument("--src", required=True, help="source video (landscape)")
ap.add_argument("--work", required=True, help="work dir with words.json etc.; temp files go here")
ap.add_argument("--out", required=True, help="output dir for deliverables")
ap.add_argument("--config", default=None, help="clip config .py (default: clips.py next to this script)")
ap.add_argument("--fonts-dir", default=None, help="dir with NotoSansCJK-Bold.ttc / -Regular.ttc (default: auto)")
ap.add_argument("--target-mb", type=float, default=TARGET_MB)
ap.add_argument("--fps", default="auto", help="'auto' (29.97 for 59.94/29.97 sources, else 30) or e.g. 30")
ARGS = ap.parse_args()

CFG = load_config(ARGS.config)
SRC, WORK, OUT = Path(ARGS.src), Path(ARGS.work), Path(ARGS.out)
WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
FONTSDIR = ARGS.fonts_dir or default_fonts_dir()
CLIPS, SUB = CFG.CLIPS, CFG.SUB
SOURCE = getattr(CFG, "SOURCE", {})
MANUAL_X = getattr(CFG, "MANUAL_X", {})
CUTS = getattr(CFG, "CUTS", [])
LOGO = getattr(CFG, "LOGO", None)                       # (x0, x1) of a burned-in logo in source px, or None
CARD_Y = getattr(CFG, "CARD_Y", CARD_Y_DEFAULT)
SUB_MARGIN_V = getattr(CFG, "SUB_MARGIN_V", SUB_MARGIN_V_DEFAULT)
SUB_MARGIN_V_LOGO = getattr(CFG, "SUB_MARGIN_V_LOGO", SUB_MARGIN_V_LOGO_DEFAULT)
FRAMING = getattr(CFG, "FRAMING", "crop")                 # "crop" (centre/face crop) or "fit" (whole frame over blurred fill)
FIT_Y = getattr(CFG, "FIT_Y", 380)
NO_KARAOKE = getattr(CFG, "NO_KARAOKE", False)           # True when the source already carries Chinese hardsubs
SCHEDULE_NOTE = getattr(CFG, "SCHEDULE_NOTE", "Pending user review; not scheduled, not uploaded")

SRC_PR = probe(SRC); SRC_V = video_stream(SRC_PR)
SRC_W, SRC_H = int(SRC_V["width"]), int(SRC_V["height"])
assert SRC_W > SRC_H, "landscape source expected; for portrait/4:5 use the blurred-fill recipe"
CROP_W = int(round(SRC_H * 9 / 16 / 2)) * 2             # 1080p -> 608
FPS = out_fps(SRC_V["r_frame_rate"], ARGS.fps)

def _load(name, default):
    p = WORK / name
    return json.load(open(p)) if p.exists() else default

SWITCH = _load("switch.json", {})
WORDS = _load("words.json", None)
if WORDS is None: raise SystemExit(f"missing {WORK / 'words.json'} (run transcribe_words.py)")
WORDS = sorted(WORDS + [list(w) for w in getattr(CFG, "WORD_FIXES", [])])
FACES = _load("face_samples.json", {})
SAMPLES = sorted(s for v in FACES.values() if isinstance(v, dict) and "samples" in v for s in v["samples"])

# ------------------------------------------------------------------ line timing from word timestamps
def line_times(c):
    """lines = (zh, en, anchor). End = last word end + 0.3 s, or the next anchor when the gap is <= 0.6 s."""
    L = c["lines"]; out = []
    for i, (zh, en, a) in enumerate(L):
        nxt = L[i + 1][2] if i + 1 < len(L) else c["src_out"]
        ws = [w for w in WORDS if a - 0.35 <= w[0] < nxt - 0.05]
        e = max([min(w[1], w[0] + 1.2) for w in ws] + [a + 0.4])
        end = nxt if (i + 1 < len(L) and nxt - e <= 0.6) else min(e + 0.3, nxt)
        out.append((zh, a, round(end, 2), en))
    return out

# ------------------------------------------------------------------ karaoke ASS
RAISED = []

def ass_time(t):
    t = max(0.0, t); h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def tokens(text):
    """Split into karaoke syllables: one CJK char (+ trailing punctuation) or one Latin/number word."""
    toks = []
    for m in re.finditer(r"[A-Za-z0-9][A-Za-z0-9.]*[A-Za-z0-9]? ?|[\u4e00-\u9fff][%s]* ?|[%s]" % (PUNCT, PUNCT), text):
        tok = m.group(0)
        if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", tok) and toks:
            toks[-1] += tok; continue
        toks.append(tok)
    assert "".join(toks).replace(" ", "") == text.replace(" ", ""), (toks, text)
    return toks

def weight(tok):
    core = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", tok)
    return max(1.0, len(core) / 2.5) if re.match(r"[A-Za-z0-9]", core) else 1.0

def karaoke(text, t0, t1):
    toks = tokens(text); ws = [weight(t) for t in toks]; tot = sum(ws)
    total_cs = int(round((t1 - t0) * 100)); acc = 0; parts = []
    for i, (tok, w) in enumerate(zip(toks, ws)):
        cs = total_cs - acc if i == len(toks) - 1 else max(1, int(round(total_cs * w / tot)))
        acc += cs; parts.append(f"{{\\k{cs}}}{tok}")
    return "".join(parts)

def core_len(text):
    return len(re.sub(r"[^\u4e00-\u9fff]", "", text)) + sum(len(w) / 2.5 for w in re.findall(r"[A-Za-z0-9]+", text))

def text_w(text):
    return sum(40 if ord(ch) < 128 else 72 for ch in text) + 14

def logo_clash(text, a, b, shots):
    """True if, in any shot overlapping [a, b] (clip time), the burned-in logo lands under the centred subtitle."""
    if not LOGO: return False
    w = text_w(text); x0, x1 = 540 - w / 2 - 16, 540 + w / 2 + 16
    for sh in shots:
        s0, s1 = sh.get("switch_t", sh["t0"]), sh["t1"]
        if s1 <= a or s0 >= b: continue
        lx0, lx1 = (LOGO[0] - sh["fixed_x"]) * 1080 / CROP_W, (LOGO[1] - sh["fixed_x"]) * 1080 / CROP_W
        if lx1 > x0 and lx0 < x1: return True
    return False

def write_ass(path, title, lines, t_in, duration, shots=()):
    body = [
        "[Script Info]", f"Title: {title}", "ScriptType: v4.00+", "WrapStyle: 0",
        "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Karaoke,Microsoft YaHei,72,&H0000D7FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,0,2,48,48,{SUB_MARGIN_V},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for i, (text, a, b, _) in enumerate([] if NO_KARAOKE else lines):
        assert core_len(text) <= MAX_LINE_CHARS, f"line too long: {text}"
        assert b > a, text
        if i: assert a >= lines[i - 1][2] - 1e-6, f"overlap: {text}"
        a, b = a - t_in, min(b - t_in, duration - 0.05)
        mv = SUB_MARGIN_V_LOGO if logo_clash(text, a, b, shots) else 0
        if mv: RAISED.append((path.stem, text, round(a, 2)))
        body.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Karaoke,,0,0,{mv},,{karaoke(text, a, b)}")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ title card (kicker / line1 / line2 / source line)
def fit(d, text, path, size, maxw, index=0):
    while True:
        f = ImageFont.truetype(path, size, index=index)
        if d.textlength(text, font=f) <= maxw or size <= 30: return f
        size -= 2

def make_card(path, kicker, l1, l2):
    W, H = 980, 330
    im = Image.new("RGBA", (W, H), (10, 14, 24, 230)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 14, H], fill=(0, 215, 255, 255))
    B, R = "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"   # Windows port: Microsoft YaHei, ttc index 0
    d.text((40, 26), kicker, font=fit(d, kicker, B, 40, 900), fill=(0, 215, 255, 255))
    d.text((40, 94), l1, font=fit(d, l1, B, 56, 910), fill=(255, 255, 255, 255))
    d.text((40, 170), l2, font=fit(d, l2, B, 56, 910), fill=(255, 255, 255, 255))
    d.text((40, 264), SUB, font=fit(d, SUB, R, 30, 910), fill=(200, 210, 220, 255))
    im.save(path)

# ------------------------------------------------------------------ framing: one fixed crop x per shot, never tracking
def shots_for(cid, c):
    a, b = c["src_in"], c["src_out"]
    bounds = [a] + [t for t in CUTS if a < t < b] + [b]; shots = []
    centre = (SRC_W - CROP_W) // 2
    for i in range(len(bounds) - 1):
        t0, t1 = bounds[i], bounds[i + 1]
        sh = {"index": i, "src_t0": round(t0, 3), "src_t1": round(t1, 3), "t0": round(t0 - a, 3), "t1": round(t1 - a, 3),
              "crop_w": CROP_W, "crop_h": SRC_H}
        if i and str(round(t0, 3)) in SWITCH.get(cid, {}): sh["switch_t"] = SWITCH[cid][str(round(t0, 3))]
        key = (cid, round(t0, 3))
        samp = [max(fl, key=lambda f: f[2]) for t, fl in SAMPLES if t0 + 0.05 <= t < t1 - 0.05 and fl]
        # largest face per sample; drop small / low-score / lower-frame false positives
        big = [f for f in samp if f[2] >= 0.074 * SRC_H and f[4] >= 0.75 and f[1] < 0.65 * SRC_H]
        if key in MANUAL_X:
            sh.update(label="manual_speaker_x", fixed_x=MANUAL_X[key][0], note=MANUAL_X[key][1])
        elif len(big) < 3:
            sh.update(label="centre_default", fixed_x=centre, n_face=len(big))
        else:
            lefts = sorted(f[0] - f[2] / 2 for f in big); rights = sorted(f[0] + f[2] / 2 for f in big)
            lo, hi = lefts[int(0.01 * (len(lefts) - 1))], rights[int(round(0.99 * (len(rights) - 1)))]
            # centre on the span the face covers over the whole shot (p1-p99) so leaning stays in frame
            x = int(round(min(max((lo + hi) / 2 - CROP_W / 2, 0), SRC_W - CROP_W)))
            outside = sum(1 for f in big if f[0] - f[2] / 2 < x or f[0] + f[2] / 2 > x + CROP_W)
            sh.update(label="face_lock_fixed", fixed_x=x, face_span_x=[round(lo), round(hi)],
                      median_cx=round(st.median(f[0] for f in big), 1), median_face_w=round(st.median(f[2] for f in big), 1),
                      n_face=len(big), face_box_touching_edge=outside)
        shots.append(sh)
    return shots

def crop_expr(shots):
    expr = str(shots[-1]["fixed_x"])
    for sh, nx in reversed(list(zip(shots[:-1], shots[1:]))):
        sw = nx.get("switch_t", sh["t1"] - 0.017)
        expr = f"if(lt(t\\,{sw:.3f})\\,{sh['fixed_x']}\\,{expr})"
    return expr

# ------------------------------------------------------------------ build
def tc(t):
    m = int(t // 60); return f"{m:02d}:{t - 60 * m:06.3f}"

def build(cid):
    c = CLIPS[cid]; name = f"{cid}-{c['slug']}"; a, b = c["src_in"], c["src_out"]; dur = round(b - a, 3)
    lines = line_times(c); shots = shots_for(cid, c)
    ass_w = WORK / f"{name}.ass"; write_ass(ass_w, c["card"][1] + c["card"][2], lines, a, dur, shots)
    ass = OUT / ass_w.name; shutil.copyfile(ass_w, ass)
    card = WORK / f"card-{cid}.png"; make_card(card, *c["card"])
    vb = min(MAX_VKBPS, int(ARGS.target_mb * 1e6 * 8 / dur / 1000 - (AUDIO_KBPS + 12))); fo = c.get("fade_out", 0.3)
    base = (f"[0:v]fps={FPS},crop={CROP_W}:{SRC_H}:x='{crop_expr(shots)}':y=0,scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p[base];" if FRAMING == "crop" else
            f"[0:v]fps={FPS},split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.08,setsar=1[bg];"
            f"[b]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:{FIT_Y},setsar=1,format=yuv420p[base];")
    fc = (base +
          "[1:v]scale=920:-1,format=rgba,fade=t=out:st=3.2:d=0.8:alpha=1[card];"
          f"[base][card]overlay=x=(W-w)/2:y={CARD_Y}:eof_action=pass[vo];"
          f"[vo]ass={ass_w.name}:fontsdir=fonts[v];"
          f"[0:a]aresample=48000,afade=t=in:d=0.12,afade=t=out:st={dur - fo:.3f}:d={fo}[a]")
    out = OUT / f"{name}.mp4"
    common = ["ffmpeg", "-y", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", str(SRC.resolve()),
              "-loop", "1", "-framerate", FPS, "-t", "5", "-i", str(card.resolve()),
              "-filter_complex", fc, "-map", "[v]",
              "-c:v", "libx264", "-preset", "slow", "-b:v", f"{vb}k", "-maxrate", f"{int(vb * 1.5)}k", "-bufsize", f"{vb * 2}k",
              "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-r", FPS, "-g", "60",
              "-passlogfile", str((WORK / f"x264-{cid}").resolve())]
    for p, tail in ((1, ["-map", "[a]", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-f", "mp4", os.devnull]),
                    (2, ["-map", "[a]", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ac", "2", "-movflags", "+faststart",
                         "-t", f"{dur:.3f}", str(out.resolve())])):
        r = subprocess.run(common + ["-pass", str(p)] + tail, cwd=str(WORK), capture_output=True, text=True)
        if r.returncode: print(r.stderr[-5000:]); raise SystemExit(f"{cid}: ffmpeg pass {p} failed")
    mid = min(lines, key=lambda l: abs((l[1] + l[2]) / 2 - (a + b) / 2))
    st_t = c.get("still_t", round((mid[1] + mid[2]) / 2 - a, 2))     # mid-clip, on a subtitle
    still = OUT / f"{name}-still.jpg"
    subprocess.check_call(["ffmpeg", "-y", "-ss", str(st_t), "-i", str(out), "-frames:v", "1", "-q:v", "2", str(still)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pr = probe(out); v = video_stream(pr)
    odur = float(pr["format"]["duration"]); size = int(pr["format"]["size"])
    meta = {
        "clip": name, "publish_order": c.get("order"), "pick": c.get("pick"),
        "title_card": {"kicker": c["card"][0], "line1": c["card"][1], "line2": c["card"][2], "sub": SUB},
        "theme": c.get("theme", ""), "path": out.name, "still": still.name, "still_t": st_t, "ass": ass.name,
        "source_url": SOURCE.get("url", ""), "source_title": SOURCE.get("title", ""), "source_channel": SOURCE.get("channel", ""),
        "source_resolution": f"{SRC_W}x{SRC_H}", "source_fps": SRC_V["r_frame_rate"], "source_duration": float(SRC_PR["format"]["duration"]),
        "cut_start_s": a, "cut_end_s": b, "cut_start_tc": tc(a), "cut_end_tc": tc(b),
        "duration": round(odur, 3), "res": f"{v['width']}x{v['height']}",
        "encode": {"codec": "libx264", "preset": "slow", "mode": f"2-pass {vb}k (maxrate {int(vb * 1.5)}k)", "profile": v.get("profile"),
                   "level": "4.1", "pix_fmt": v.get("pix_fmt"), "fps": FPS, "faststart": True,
                   "audio": f"AAC-LC {AUDIO_KBPS}k 48 kHz stereo, 0.12 s fade-in / {fo} s fade-out"},
        "framing": {"strategy": "one fixed crop per shot (manual speaker x / YuNet face span / centre)", "continuous_track": False,
                    "crop": f"{CROP_W}x{SRC_H} -> 1080x1920 lanczos", "shots": shots},
        "karaoke": True, "karaoke_lang": "zh-Hans", "karaoke_lines": len(lines),
        "karaoke_raised_above_logo": [{"t": t, "zh": z} for n, z, t in RAISED if n == name],
        "transcript": [{"start": round(s - a, 2), "end": round(e - a, 2), "src_start": s, "src_end": e, "en": en, "zh": zh} for zh, s, e, en in lines],
        "file_size_bytes": size, "file_size_human": f"{size / 1048576:.2f} MiB ({size / 1e6:.2f} MB)",
        "under_45MB": size < 45e6, "published": False, "schedule_note": SCHEDULE_NOTE,
    }
    (OUT / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"clip": name, "dur": odur, "size": meta["file_size_human"], "vb": vb, "lines": len(lines),
                      "shots": [(s["t0"], s["fixed_x"], s["label"]) for s in shots]}, ensure_ascii=False), flush=True)
    if size >= 45e6: print(f"WARNING {name}: {size / 1e6:.2f} MB >= 45 MB; lower --target-mb", flush=True)

if __name__ == "__main__":
    for cid in (ARGS.clips or list(CLIPS)):
        build(cid)
