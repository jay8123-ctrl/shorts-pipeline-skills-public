#!/usr/bin/env python3
"""yt_analytics_auth.py: one-time login that grants READ-ONLY YouTube Analytics access.

Separate token (_internal/.youtube/token_analytics.json) so the upload token keeps its narrow scopes.
Scopes: yt-analytics.readonly (reports) + youtube.readonly (channel/video lookups). Nothing here can edit or delete."""
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parents[3]
TOKEN = ROOT / "_internal" / ".youtube" / "token_analytics.json"
SECRETS = Path(os.environ.get("YOUTUBE_CLIENT_SECRETS_FILE") or Path.home() / ".config" / "claude-toolkit" / "youtube_client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtube.readonly"]

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent", open_browser=True,
                                  authorization_prompt_message="Open this URL if no browser appears:\n\n{url}\n",
                                  success_message="Analytics access granted (read-only). You can close this tab.")
    TOKEN.parent.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    print("saved", TOKEN)
