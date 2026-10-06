---
name: 'YouTube Studio: schedule finished Shorts'
description: >-
  Use this when Clip Bot has finished a Short (or a batch) and Stills & Clips
  Desk has written its copy, and the Short needs uploading and scheduling on the
  user's YouTube channel in Studio. Covers picking the date, checking the files,
  the upload settings, Studio getting stuck, and reporting back.
---
# YouTube Studio: schedule finished Shorts

Takes over after Clip Bot has delivered the mp4(s) and Stills & Clips Desk has delivered the copy. The output is scheduled Shorts plus a link list for the user. Clip Bot and Stills never upload. This step is the only one that touches YouTube.

## 1. Wait for both handoffs
- Clip Bot hands over the mp4(s) in `/workspace/clips/<slug>/`, at 1080x1920, with zh-Hans karaoke unless the source already has Chinese subs.
- Stills hands over `youtube-shorts-descriptions.md` and `descriptions.json` in the same folder. These hold the title, description, tags, thumbnail, and publish_order for each clip.
- Don't upload until the copy exists. If Clip Bot pings first, stay quiet and wait for Stills.

## 2. Pick the date
- **One topic per calendar day (user's local time).** All clips cut from the same source count as one topic.
- Find the next free day by listing `/workspace/clips/*/schedule-*.json` and comparing it with your memory of the queue.
- The first clip goes at **06:00**, and each further clip from the same topic goes 10 minutes later (06:10, 06:20, and so on), in Stills' publish_order.
- If today's 06:00 hasn't passed and today is free, today is fine.
- Default is at most 5 clips per source. Uploading more than that in one go counts as an upload wave, so ask the user first.

## 3. Pre-flight checks
- Every mp4 must be **under 50 MB**, because the box browser can't upload larger files to Studio. If one is bigger, make a smaller copy with ffmpeg (H.264 2-pass) and upload that copy.
- The title and description come from Stills, word for word. Keep the source credit, disclaimers, and any hedging such as 网传, 据称 or 未经证实.
- If the same source video has been used before, warn the user before uploading it again.

## 4. Upload in Studio (run as a desktop task)
- Use **https://studio.youtube.com only**. Never browse the signed-in youtube.com site.
- Before each upload, check Content > Shorts so you don't create a duplicate.
- Settings for each video:
  - Title, description and tags (under Show more) from `descriptions.json`.
  - Custom thumbnail from Stills, if Studio allows it. If not, skip it without retrying.
  - Audience: **No, not made for kids.**
  - Altered content: **No** (real footage).
  - Age restriction: **18+ only** for graphic or gory clips, even when blurred. Otherwise none.
  - Visibility: **Schedule** for the date and time, timezone **GMT+08:00 Singapore**. There's no Kuala Lumpur entry, and Singapore is the same offset.
- **Stuck on "Processing will begin shortly", with Schedule greyed out:** wait 3 to 5 minutes, reload Content > Shorts, open the draft and schedule it from there. Only upload again if no draft exists. If it's still stuck after about 15 minutes, stop and report the exact state.
- **Daily upload limit shown:** stop immediately. Don't retry. Note which clips are done, then resume the rest 24 hours later.
- If a batch run stops partway without an error, resume it for the missing clips only, after checking for drafts first.
- Don't change any other videos or settings.

## 5. Record and report
- Write `/workspace/clips/<slug>/schedule-<date>.json`: one object, or an array for a batch, with `clip`, `videoId`, `url` (`https://youtube.com/shorts/<id>`), `scheduled_for` (ISO with +08:00), `title` and `status`.
- Save a one-line queue note in memory: the topic, the date, and the next free day.
- Tell the user in one short message: the date and time in their local time with a short zone label (such as MYT), the Short link(s) with titles for a batch, any 18+ or other notable setting, and the next free day.
- Ping Clip Bot or Stills only if they need to act. Plain acknowledgements aren't needed.

## Don't
- Upload before Stills' copy exists, or rewrite their copy.
- Put two topics on one day without the user's explicit OK.
- Upload duplicates, or retry in a loop after the daily limit.
- Use youtube.com (instead of Studio) or any public-web browser tool for this.
