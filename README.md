# Chinese Shorts pipeline for Claude Code

Paste a YouTube, X or Facebook video link into Claude Code. It writes a timed Chinese summary, cuts up to 5 vertical Shorts with Chinese karaoke subtitles, writes the titles and descriptions, uploads them to your YouTube channel and schedules them. One link in, scheduled Shorts out.

Built and tested on Windows 11 with Claude Code. Linux and macOS should work, but the font step needs a Chinese font path change.

## What is in this repo

| Folder | Contents |
|---|---|
| `skills/video-chinese-shorts` | Step 1: duplicate check, Chinese 重点 summary, picks (max 5) |
| `skills/clip-shorts` | Step 2: 9:16 clips, karaoke subtitles, title card, QA. Scripts are in `scripts/` |
| `skills/shorts-titles-and-descriptions` | Step 3: Chinese titles, descriptions, tags |
| `skills/youtube-studio-schedule-shorts` | Step 4: upload and schedule (browser route in YouTube Studio) |
| `tools/` | Helpers: upload and schedule through the YouTube API, queue check, analytics, channel watcher, patched clip scripts |

## Install in Claude Code (recommended)

Claude Code loads skills from a folder, so this is the only agent where everything works as designed.

1. Install [Claude Code](https://claude.com/claude-code).
2. Download this repo (green **Code** button, then **Download ZIP**, or `git clone`).
3. Copy every folder inside `skills/` into your skills folder, then restart Claude Code:
   - Windows: `C:\Users\<you>\.claude\skills\`
   - macOS / Linux: `~/.claude/skills/`
4. Check it worked: start Claude Code and type `/skills`. You should see `video-chinese-shorts`, `clip-shorts`, `shorts-titles-and-descriptions` and `youtube-studio-schedule-shorts`.
5. Continue with **Setup, step by step** below, then paste a video link.

## Install in Grok or another chat bot (limited, untested)

Grok and most chat bots have no skills folder, and I have not tested this repo with Grok. What can work:

- The four `SKILL.md` files are plain Markdown instructions. You can paste one into the bot's custom instructions, a project prompt, or the start of a chat, then paste the video link.
- That gives you the **writing steps** (summary, picks, titles and descriptions). The bot can only do them from a transcript you paste in.
- It cannot run the scripts: downloading the video, cutting clips, burning subtitles and uploading all need a computer where Python, ffmpeg and the files are available, which is what Claude Code provides.

If your bot can run code and use files (an agent with a terminal), follow the Claude Code steps and point the bot at the `skills/` folder.

## Setup, step by step

### 1. Install the programs
- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) on your PATH (check with `ffmpeg -version`)
- yt-dlp is run through `uvx yt-dlp`, so nothing extra to install

### 2. Get the toolkit this depends on
`tools/yt_publish_batch.py` and `tools/yt_queue.py` use `tools/youtube_upload.py` from the open-source toolkit:
```bash
git clone https://github.com/digitalsamba/claude-code-video-toolkit
cd claude-code-video-toolkit
```
Then copy this repo's `tools/` folder to `claude-code-video-toolkit/projects/_shared/tools/`.

### 3. Create the Python environment
From the toolkit folder:
```bash
uv venv projects/_shared/venv --python 3.12
uv pip install --python projects/_shared/venv numpy pillow opencv-python-headless==4.11.0.86 faster-whisper av==15.1.0 google-api-python-client google-auth-oauthlib google-auth-httplib2 python-dotenv httplib2
```
The two pinned versions matter: newer `av` or OpenCV break the face and video steps.

### 4. Add the subtitle font
The scripts use Microsoft YaHei (`msyh.ttc`, `msyhbd.ttc`). On Windows they are in `C:\Windows\Fonts`; copy them to `projects/_shared/fonts/`. On Linux or macOS, use any bold Chinese font and change the font name in `tools/build_short.py`.

### 5. Connect your YouTube channel (needed for automatic upload)
1. In [Google Cloud Console](https://console.cloud.google.com/), create a project and enable **YouTube Data API v3**.
2. Create an **OAuth client ID** of type **Desktop app** and download the JSON.
3. Put its path in the toolkit's `.env`: `YOUTUBE_CLIENT_SECRETS_FILE=<path>`.
4. Log in once (a browser opens, click Allow):
```bash
uv run tools/youtube_upload.py --auth
```
5. If the app stays in "Testing" mode, the login expires after about 7 days; run step 4 again.

Optional, for channel analytics: also enable **YouTube Analytics API**, then run `python tools/yt_analytics_auth.py` and `python tools/yt_analytics_report.py`.

## How to use it
1. Open Claude Code in the toolkit folder.
2. Paste a video link, for example `https://www.youtube.com/watch?v=...`
3. Claude runs the four skills in order and reports the Shorts, times and links.

Uploads default to private with a scheduled publish time (06:00, then +10 minutes per clip). YouTube's default quota allows about 6 uploads a day.

## Rules built into the skills
- Claims are attributed to the speaker, and nothing is added that the video does not say.
- A repeat video, graphic footage or an unverified claim stops the run and asks you first.
- Maximum 5 Shorts per source video; one topic per day.
- Sources that already carry Chinese hardsubs get no extra subtitles (`NO_KARAOKE = True`).

## Not included on purpose
OAuth secrets and tokens, `.env`, downloaded videos, and any processed-videos log. You use your own Google Cloud project.

## Watch channels for new videos (optional)
`tools/yt_watch.py baseline` marks a channel's current videos as seen; `tools/yt_watch.py check` lists new ones. Copy `tools/watch.example.json` to `projects/_shared/watch.json`, add your channels, and run `baseline` first so old videos are not processed.
