#!/usr/bin/env python3
"""yt_watch.py: find new videos on watched channels.

  yt_watch.py baseline      mark every video currently on the watched channels as seen (run once when adding a channel)
  yt_watch.py check         print NEW videos as JSON lines (not seen, not in yt-cn-processed.json, not live/upcoming); does NOT mark them
  yt_watch.py mark ID...    mark ids as seen (the pipeline calls this when it has finished or deliberately skipped a video)

Config: projects/_shared/watch.json  {"channels":[{"name","url"}], "seen":[ids]}"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = HERE.parent / "watch.json"
LOG = HERE.parents[2] / "yt-cn-processed.json"
DEPTH = 40


def load():
    return json.loads(CFG.read_text(encoding="utf-8"))


def save(c):
    CFG.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")


def listing(url, n):
    r = subprocess.run(["uvx", "yt-dlp", "--no-warnings", "--flat-playlist", "--playlist-end", str(n), "--print",
                        "%(id)s|%(duration)s|%(live_status)s|%(title)s", url.rstrip("/") + "/videos"],
                       capture_output=True, text=True, encoding="utf-8")
    out = []
    for line in r.stdout.splitlines():
        p = line.split("|", 3)
        if len(p) == 4 and len(p[0]) == 11:
            out.append(dict(id=p[0], duration=p[1], live=p[2], title=p[3]))
    if not out:
        print(f"WARN: no videos listed for {url}: {r.stderr[-300:]}", file=sys.stderr)
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    c = load(); seen = set(c.get("seen", []))
    if cmd == "baseline":
        for ch in c["channels"]:
            seen |= {v["id"] for v in listing(ch["url"], DEPTH)}
        c["seen"] = sorted(seen); save(c); print(f"{len(seen)} ids marked seen")
    elif cmd == "mark":
        c["seen"] = sorted(seen | set(sys.argv[2:])); save(c)
    else:
        done = {e["id"] for e in json.loads(LOG.read_text(encoding="utf-8-sig"))} if LOG.exists() else set()
        for ch in c["channels"]:
            for v in listing(ch["url"], 15):
                if v["id"] in seen or v["id"] in done or v["live"] in ("is_live", "is_upcoming"):
                    continue
                print(json.dumps(dict(v, channel=ch["name"], url=f"https://www.youtube.com/watch?v={v['id']}"), ensure_ascii=False))


if __name__ == "__main__":
    main()
