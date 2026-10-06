#!/usr/bin/env python3
"""yt_publish_batch.py: upload + schedule a batch of finished Shorts through the YouTube Data API.

  python yt_publish_batch.py --dir clips/<topic>-<id> --date 2026-10-06 [--start 06:00] [--step 10] [--dry-run]

Reads <dir>/descriptions.json (publish_order, file, title, description, tags). Each clip is uploaded private with
--publish-at (MYT = UTC+8 converted to UTC), 10 minutes after the previous one. Afterwards every video is read back
from the API to confirm status.publishAt, and <dir>/schedule-<date>.json is written. Nothing is deleted here."""
import argparse, json, subprocess, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from yt_queue import ROOT, service, MYT

UPLOADER = ROOT / "tools" / "youtube_upload.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True); ap.add_argument("--date", required=True)
    ap.add_argument("--start", default="06:00"); ap.add_argument("--step", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir); items = json.loads((d / "descriptions.json").read_text(encoding="utf-8"))
    items.sort(key=lambda x: x["publish_order"])
    if len(items) > 5:
        sys.exit("more than 5 clips: ask the user first")
    h, m = map(int, a.start.split(":"))
    t0 = datetime.fromisoformat(a.date).replace(hour=h, minute=m, tzinfo=MYT)
    results = []
    for n, it in enumerate(items):
        when = t0 + timedelta(minutes=a.step * n)
        utc = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        tags = ",".join(t.lstrip("#") for t in it.get("tags", []))
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(it["description"]); desc_file = f.name
        cmd = [sys.executable, str(UPLOADER), "--video", str(d / it["file"]), "--title", it["title"],
               "--description-file", desc_file, "--tags", tags, "--publish-at", utc, "--json-out"]
        if a.dry_run:
            cmd.append("--dry-run")
        print(f"[{n + 1}/{len(items)}] {it['file']} -> {when.isoformat()}", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        line = [l for l in r.stdout.splitlines() if l.startswith("{")]
        if r.returncode or not line:
            print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(f"upload failed for {it['file']}; stop, check Studio for drafts before retrying")
        j = json.loads(line[-1])
        results.append({"clip": it["clip"], "videoId": j.get("videoId"), "url": f"https://youtube.com/shorts/{j.get('videoId')}" if j.get("videoId") else None,
                        "scheduled_for": when.isoformat(), "title": it["title"]})
    if a.dry_run:
        print("dry run ok"); return
    yt = service()
    ids = ",".join(r["videoId"] for r in results)
    got = {v["id"]: v for v in yt.videos().list(part="status,snippet", id=ids).execute()["items"]}
    for r in results:
        v = got.get(r["videoId"])
        pa = v["status"].get("publishAt") if v else None
        r["status"] = f"scheduled ({v['status']['privacyStatus']} until {pa})" if pa else "NOT SCHEDULED - check"
        print(r["scheduled_for"][:16], r["videoId"], r["status"])
    (d / f"schedule-{a.date}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
