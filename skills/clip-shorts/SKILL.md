---
name: clip-shorts
description: "Use when cutting vertical YouTube Shorts from a long video or X/YouTube link: picks, 9:16 reframe, zh-Hans karaoke, QA, handoff."
---

# Clip Shorts (竖屏短视频切条)

You turn one long video into at most 5 vertical YouTube Shorts. Each Short has a hook-first cut, a calm fixed 9:16 frame, burned-in Simplified Chinese (zh-Hans) karaoke subtitles, and a short title card. You do the work. The user approves the picks and owns the upload.

**Workflow checklist**
1. Check the source id against your used-ids list, then download and probe the source (≥1080p).
2. Transcribe with word timestamps and fix names and terms.
3. Propose ≤5 hook-first picks snapped to sentences, and get user approval.
4. Detect shots, choose one crop per shot, translate, and write the ASS and title cards.
5. Encode each master under 45 MB.
6. Run lean QA: ffprobe, one frame per clip, and a head/tail re-transcribe.
7. Deliver the files, README and youtube-shorts-descriptions.md.

## 1. Inputs
- **Source**: a local video file, or a YouTube or X URL. Download the best stream at 1080p or higher. If only a lower resolution exists, tell the user before you cut.
  ```bash
  yt-dlp -S "res,ext:mp4:m4a" -f "bv*+ba/b" --merge-output-format mp4 -o source.mp4 "$URL"
  ffprobe -v error -show_entries stream=width,height,r_frame_rate -of csv=p=0 source.mp4
  ```
- **Transcript with word timestamps**: use faster-whisper (medium or larger) or openai-whisper with `word_timestamps=True`. Long files time words better when you transcribe overlapping ~30 s windows, as `scripts/transcribe_words.py` does. Re-run doubtful spots with `initial_prompt` set to the names and terms.
  ```bash
  ffmpeg -i source.mp4 -vn -ac 1 -ar 16000 audio16k.wav
  ```
- **Already used?** Keep a list of source video ids you have already cut (the YouTube id or X status id). If this id is on it, warn the user and wait for confirmation before you make it again.

## 2. Picks (选段)
- Make **at most 5 clips per source**: the 5 most viral-worthy moments (爆点). The user or a researcher may supply the picks. For a source over 30 min, pick its 5 most important points (核心观点).
- If a source is under about 5 min and the user approves it as **"whole"**, it becomes one Short.
- Target 30-90 s per clip. Start and end every clip on a **sentence boundary**. Use word timestamps plus an audio RMS check (`scripts/rms.py`) so no word is clipped. Leave ~0.1 s of air at the head and ~0.3 s at the tail, with short audio fades.
- **Hook first (开头即爆点)**: open on the strongest line, the question that sets up the payoff, or a 0.5-1 s preview of the payoff that then cuts back. No slow lead-in, no greetings, no "so, um".
- Present the picks to the user as `NN | in → out | duration | one-line hook (zh)`, and get approval before you build.

## 3. Output spec
- 1080×1920, H.264 High (level 4.1, yuv420p), AAC-LC 128k 48 kHz stereo, 30 fps (29.97 if the source is 59.94/29.97), `+faststart`.
- Keep each **master under 45 MB**, because the YouTube Studio browser upload limit is 50 MB. Aim for ~40 MB with 2-pass bitrate (`video kbps ≈ 40.5 MB × 8 / duration − 140`, capped at 6000). Alternatively, use CRF 18-23 and raise the CRF until the file fits.

## 4. Framing (构图)
- **Default**: a fixed center crop (`crop=ih*9/16:ih`, then scale to 1080×1920).
- **Per shot**: find hard cuts (shot detection: frame-difference peaks, confirmed with `select=gt(scene,0.25)`). Give each shot **one fixed crop x**. Move it off center only when the speaker would leave the frame. In that case, center it on the span the face covers over the whole shot (p1-p99 of the face box). Switch the crop on the exact first frame of the new shot.
- **Panels / split screens / wide shots**: frame the **current speaker**. If question and answer both fit inside the window, frame both. Otherwise frame the main speaker and let the other voice play off-frame.
- **Never** use continuous tracking, easing, zoom drift or shake.
- **Portrait or 4:5 source**: scale it to 1080 px wide, center it, and fill above and below with a blurred, slightly darkened copy of the same video.
- Note burned-in banners, tickers and logos, and keep subtitles and the title card clear of them.

## 5. Subtitles (中文卡拉OK字幕)
- **Default: zh-Hans burned-in karaoke on every Short, whatever language is spoken.** Translate faithfully (忠实翻译): keep the meaning, smooth only false starts, and never add claims.
- Skip it **only** if the source already has Chinese hardsubs (中文硬字幕). If the source has subtitles in another language only, still add Chinese.
- Use an ASS file with character-level `\k` highlight. Upcoming text is white (SecondaryColour) and sung text turns gold (PrimaryColour).
- Keep lines to **≤ ~12 Chinese characters**. A Latin word counts as about len/2.5. Use one line on screen at a time. Bottom MarginV is ~370 on 1080×1920. Raise a line wherever a banner or logo would sit behind it.
- Timing: a line starts at its first word's start. It ends at its last word's end + 0.3 s, or at the next line's start when the gap is ≤ 0.6 s. Spread `\k` across the characters (a Latin word weighs len/2.5 characters).
- Fix ASR errors, especially names and terms: use standard Chinese names (马斯克, 黄仁勋) and keep product names in Latin (Claude, SpaceX). Mark genuinely unclear audio as **[听不清]**, never invented words. List doubtful words in the README.

## 6. Title card (标题卡)
- Show it for ~3-4 s from t=0, with a 0.8 s fade out. Use 3 lines: a kicker (topic), a 2-line neutral Chinese title, and a small source line (outlet · event · date).
- Place it **below the faces and never covering a face**, and above the subtitles. Check this on a frame.
- Use neutral wording that attributes claims to the speaker (`马斯克：…`). Hedge unverified claims with **网传 / 据称 / 未经证实**. No clickbait that the clip does not support.

## 7. Sensitive content
- Heavily pixelate or blur gore, injuries or bodies **for the whole time they are on screen**, with a generous margin. Then pull frames across that span and look at them to confirm nothing is visible. If you can't confirm it, drop the clip and tell the user.

## 8. ffmpeg recipes
Cut, center crop, subtitles and a single-pass CRF encode:
```bash
ffmpeg -y -ss 178.45 -t 66.00 -i source.mp4 \
  -vf "fps=30,crop='trunc(ih*9/16/2)*2':ih:(iw-ow)/2:0,scale=1080:1920:flags=lanczos,setsar=1,ass=01-slug.ass:fontsdir=fonts" \
  -af "aresample=48000,afade=t=in:d=0.12,afade=t=out:st=65.70:d=0.3" \
  -c:v libx264 -preset slow -crf 20 -profile:v high -level 4.1 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -ac 2 -movflags +faststart 01-slug.mp4
```
Fixed crop per shot (608×1080 window from 1080p; shot 2 starts at clip t=4.72 s):
```bash
-vf "fps=30,crop=608:1080:x='if(lt(t\,4.720)\,599\,628)':y=0,scale=1080:1920:flags=lanczos,setsar=1"
```
Title card overlay plus subtitles (card.png is ~920 px wide, RGBA):
```bash
ffmpeg -y -ss A -t D -i source.mp4 -loop 1 -framerate 30 -t 5 -i card.png -filter_complex \
 "[0:v]fps=30,crop=608:1080:x=656:y=0,scale=1080:1920:flags=lanczos,setsar=1[b];\
  [1:v]scale=920:-1,format=rgba,fade=t=out:st=3.2:d=0.8:alpha=1[c];\
  [b][c]overlay=(W-w)/2:1120:eof_action=pass,ass=01-slug.ass[v]" -map "[v]" -map 0:a ...
```
Portrait or 4:5 source with a blurred fill:
```bash
-filter_complex "[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.08[bg];\
 [b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
```
Pixelate a region (x,y,w,h) between 12.0 and 18.5 s:
```bash
-filter_complex "[0:v]crop=400:300:700:200,scale=iw/24:-1,scale=400:300:flags=neighbor[p];[0:v][p]overlay=700:200:enable='between(t,12.0,18.5)'[v]"
```
Size control with a 2-pass target (~40.5 MB):
```bash
D=66.0; VB=$(python3 -c "print(min(6000,int(40.5*8e6/$D/1000-140)))")
X="-c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*3/2))k -bufsize $((VB*2))k -profile:v high -level 4.1 -pix_fmt yuv420p -r 30"
ffmpeg -y -ss 178.45 -t $D -i source.mp4 -vf "$VF" $X -pass 1 -an -f mp4 /dev/null
ffmpeg -y -ss 178.45 -t $D -i source.mp4 -vf "$VF" $X -pass 2 -c:a aac -b:a 128k -ar 48000 -ac 2 -movflags +faststart 01-slug.mp4
```

## 9. Minimal ASS karaoke
```
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Noto Sans CJK SC,72,&H0000D7FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,0,2,48,48,370,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:43.87,0:00:46.67,Karaoke,,0,0,0,,{\k40}约{\k40}是{\k40}美{\k40}国{\k40}的{\k40}三{\k40}倍
Dialogue: 0,0:00:47.46,0:00:49.90,Karaoke,,0,0,500,,{\k41}用{\k41}上{\k81}Rubin{\k41}芯{\k40}片
```
Colours are &HAABBGGRR, so &H0000D7FF is gold. `\k` is in centiseconds, and the values on a line sum to its duration. A per-line MarginV (500 above) raises that line over a banner.

## 10. QA (lean, required)
1. Run `ffprobe` on every master: 1080×1920, h264 High, aac, 30 (or 29.97) fps, duration as planned, **size < 45 MB**.
2. Look at **one frame per clip** (the still, taken mid-clip with a subtitle). Check that the face is in frame, the card is not on a face, subtitles are clear of banners, and gore is covered.
3. Run a subtitle timing check: re-transcribe the **first and last 2-4 s** of each finished MP4 (`scripts/edge_check.py`) to catch clipped words. Spot-check that karaoke lines appear with their speech.
Fix and rebuild anything that fails. Report the remaining known flaws honestly.

## 11. Deliverables (per clip)
- `NN-slug.mp4` (master), `NN-slug.ass`, `NN-slug-still.jpg`. NN is the publish order, slug is short English kebab-case.
- One `README.md` per source: the source URL and title, then a table of clip, in → out (source timecode and seconds), duration and size. Add translation notes, doubtful words and known flaws.

## 12. Handoff
Write `youtube-shorts-descriptions.md` with one section per clip, in publish order:
```
## 1. `01-slug.mp4`
**标题：** 马斯克：中国发电量约是美国3倍，AI竞赛拼的是电      (≤ ~40 chars, neutral, attributed)
**描述：**
<2-3 sentence faithful zh summary of what is said>
📌 来源：<outlet/channel> · <event>, <date>
🔗 <full source URL>
⏱ 原片时间码：02:58–04:04
🈶 中文字幕：原片为英文、无字幕，中文卡拉OK字幕译自原话
⚠️ 讲述者观点摘录，未经核实；非投资/医疗建议；请以原片为准。
#人物 #话题 #AI #Shorts
```
- Schedule uploads at **one topic per calendar day (Asia/Kuala_Lumpur)**. Clips from one source share a topic and go out on the same day, and the next topic waits for the next day. Do not upload or schedule unless the user asks you to.
- Add the source video id to your used-ids list.

## Bundled scripts (`scripts/`)
`build_short.py` + `clips.py` (config) build the masters: fixed per-shot crop, karaoke ASS, title card, 2-pass size targeting, still and metadata. Helpers cover the steps around the build: word timing (`transcribe_words.py`), cut detection (`detect_cuts.py`, `cut_check.py`), face sampling (`faces_scan.py`), RMS (`rms.py`), QA (`qa_frames.py`, `edge_check.py`) and the README (`make_readme.py`). See `scripts/README.md`.
