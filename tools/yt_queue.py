#!/usr/bin/env python3
"""yt_queue.py: list the channel's scheduled (private + publishAt) videos and the next free day (MYT, UTC+8).

  python yt_queue.py            # human readable
  python yt_queue.py --json     # machine readable
Uses the cached OAuth token from tools/youtube_upload.py (_internal/.youtube/token_default.json)."""
import argparse, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[3]            # toolkit root
TOKEN = ROOT / "_internal" / ".youtube" / "token_default.json"
MYT = timezone(timedelta(hours=8))


def service():
    c = Credentials.from_authorized_user_file(str(TOKEN))
    if not c.valid:
        c.refresh(Request())
        TOKEN.write_text(c.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=c)


def scheduled(yt):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok or len(ids) >= 150:
            break
    out = []
    for k in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,status", id=",".join(ids[k:k + 50])).execute()
        for v in r["items"]:
            pa = v["status"].get("publishAt")
            if pa:
                t = datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone(MYT)
                out.append({"id": v["id"], "title": v["snippet"]["title"], "publish_myt": t.isoformat(), "date": t.date().isoformat()})
    return sorted(out, key=lambda x: x["publish_myt"])


def next_free_day(items, today=None):
    used = {i["date"] for i in items}
    d = (today or datetime.now(MYT)).date()
    while d.isoformat() in used:
        d += timedelta(days=1)
    return d.isoformat()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    items = scheduled(service())
    nf = next_free_day(items)
    if a.json:
        print(json.dumps({"scheduled": items, "next_free_day": nf}, ensure_ascii=False))
    else:
        for i in items:
            print(i["publish_myt"][:16], i["id"], i["title"])
        print("next free day (MYT):", nf)
