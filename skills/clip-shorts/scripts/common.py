"""common.py: shared helpers (config loading, ffprobe, output fps choice, font lookup)."""
import importlib.util, json, os, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_config(path=None):
    """Load a clip config module (default: clips.py next to this file)."""
    path = Path(path) if path else HERE / "clips.py"
    spec = importlib.util.spec_from_file_location("clip_config", str(path))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def probe(f):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "format=duration,size,bit_rate:stream=codec_type,codec_name,profile,level,width,height,pix_fmt,r_frame_rate,duration,bit_rate,sample_rate,channels",
        "-of", "json", str(f)]))


def video_stream(pr):
    return next(s for s in pr["streams"] if s["codec_type"] == "video")


def out_fps(src_rate, requested="auto"):
    """'auto': 29.97 for NTSC-rate sources (59.94/29.97), else 30. Otherwise pass through (e.g. '30', '30000/1001')."""
    if requested != "auto":
        return requested
    num, _, den = src_rate.partition("/")
    return "30000/1001" if den == "1001" else "30"


def fps_float(fps):
    num, _, den = str(fps).partition("/")
    return float(num) / float(den or 1)


def default_fonts_dir():
    """Directory holding NotoSansCJK-Bold.ttc / NotoSansCJK-Regular.ttc (index 2 = Simplified Chinese)."""
    for d in (os.environ.get("FONTS_DIR"), "~/.fonts", "~/.local/share/fonts", "/usr/share/fonts/opentype/noto"):
        if d and (Path(d).expanduser() / "NotoSansCJK-Bold.ttc").exists():
            return str(Path(d).expanduser())
    return str(Path("~/.fonts").expanduser())
