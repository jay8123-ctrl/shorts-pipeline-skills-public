#!/usr/bin/env python3
"""make_readme.py: write <out>/README.md from the per-clip metadata JSON files that build_short.py leaves in --out.

  python3 make_readme.py --out out/ [--title "白宫超级智能座谈 · 5 条 Shorts"] [--notes notes.md]

The table has file, source in -> out (timecode and seconds), duration, size, karaoke line count and title card.
--notes appends your hand-written sections (translation notes / doubtful words / known flaws)."""
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--title", default="YouTube Shorts")
ap.add_argument("--notes", default=None)
args = ap.parse_args()
R = Path(args.out)
rows = [json.load(open(j)) for j in R.glob("*.json") if j.name != "descriptions.json"]
rows = sorted((m for m in rows if "cut_start_s" in m), key=lambda m: (m.get("publish_order") or 0, m["clip"]))
def tc(t): m_ = int(t // 60); return f"{m_:02d}:{t - 60 * m_:05.2f}"
L = [f"# {args.title}\n"]
if rows:
    m0 = rows[0]
    L.append(f"**Source:** {m0['source_channel']} · *{m0['source_title']}* · {m0['source_url']} "
             f"({m0['source_resolution']}, {m0['source_fps']} fps, {m0['source_duration'] / 60:.1f} min)\n")
L += ["| Order | File | Source in → out | Duration | Size | Karaoke lines | Title card |", "|---|---|---|---|---|---|---|"]
for m in rows:
    c = m["title_card"]
    L.append(f"| {m.get('publish_order', '')} | `{m['path']}` | {tc(m['cut_start_s'])} → {tc(m['cut_end_s'])} "
             f"({m['cut_start_s']:.2f}–{m['cut_end_s']:.2f}s) | {m['duration']:.2f}s | {m['file_size_bytes'] / 1e6:.2f} MB | "
             f"{m['karaoke_lines']} | {c['line1']} / {c['line2']} |")
L.append("\nPer clip: `NN-slug.mp4` (master, 1080×1920 H.264 High + AAC, < 45 MB), `.ass` (zh-Hans karaoke), "
         "`-still.jpg` (mid-clip frame with a subtitle), `.json` (metadata, shots, EN+ZH lines).\n")
if args.notes: L.append(Path(args.notes).read_text(encoding="utf-8"))
L.append(f"\n**Schedule:** {rows[0].get('schedule_note', '') if rows else ''}\n")
(R / "README.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
