---
name: shorts-titles-and-descriptions
description: Use when a finished YouTube Short (or a batch) needs a Chinese title, description, tags and thumbnail text, or when picking the best 5 moments from a numbered, timed summary of a video.
---

# YouTube Shorts: picks, titles and descriptions

Job: turn finished vertical clips into publish-ready copy (title, description, tags, thumbnail text), and pick the strongest moments from a numbered 重点 list when asked. Don't upload or publish. Don't invent facts or quotes.

## 1. Picking the 5 best moments (sources of 30 min or less)
Input: a numbered, timed Chinese summary (重点 list) plus a transcript with timestamps.
- Choose the 5 most likely to pull viewers: counter-intuitive claims, conflict, shocking numbers, famous names, a strong first line.
- Mix speakers and topics. Don't take 5 points that all make the same argument.
- Keep each clip under about 90 s. If a point runs long, tighten it using the transcript timestamps. Start on a hook line (a question, "Say something controversial", a number) and end on a complete sentence.
- Output per pick: number, time range (mm:ss–mm:ss, plus seconds if tightened), and a one-line reason. Add 2 backups.
- Suggest a publish order with the strongest hook first.

## 2. Before writing, read
- The clip folder README: source, exact source timecodes, subtitle notes, known flaws, and any UNVERIFIED flags.
- Each clip's JSON or .ass: the actual English and Chinese lines. Titles may only quote or paraphrase lines that are really there.

## 3. Titles
- Hook in the first ~15 characters. Lead with the famous name plus the surprise.
- Open a curiosity gap: state the surprise without giving away the answer. Use counter-intuitive, denial or "impossible" framing, or quote the most shocking real line.
- Concrete numbers and sharp stakes work best (3倍, 100亿小时, 8小时→3分钟).
- Where it helps, give 2 options and mark the pick.
- Truthful only: no invented claims, no fake quotes, no strengthening of hedged claims.
- For unverified claims, use 网传 / 据称 / 未经证实 in the title itself.

## 4. Thumbnail
- Text of 3 characters or fewer, or none (e.g. 未证实).
- Choose a frame with a strong expression or gesture, or a clear before/after contrast. Never show gore.

## 5. Description template
```
<Line 1 repeats the hook>

<2–3 sentences: who said what, attributed. Speaker's claims are framed as claims.>

📌 来源：<channel / account, event, date>
🔗 <full source URL>
⏱ 原片时间码：<mm:ss–mm:ss>  (or 整段 0:00–m:ss)
🈶 中文字幕：<source subtitle status, e.g. "原片为英文、无字幕，中文卡拉OK字幕译自英文原话" / "原片已有中英硬字幕">

⚠️ <disclaimer>

#tag #tag ... #Shorts
```

Disclaimers:
- Political speech: 讲述者主张／非新闻核实；非法律或投资意见；内容为演讲口述剪辑，请以原片为准。
- Business, tech or health: 讲述者主张／座谈观点摘录；非新闻核实；非投资或医疗建议；请以原片为准。
- Unverified viral clip: 网传视频／说法仅来自发帖者，未经证实；非新闻核实；含已模糊处理的画面；请以官方通报为准。

Tags: 5–8, made of names, topic and place, ending with #Shorts. Avoid inflammatory or nationality tags on sensitive stories.

## 6. Subtitle status (always state it)
- Source already has Chinese hardsubs: no karaoke added, so say so.
- Source has other-language subs or none: zh-Hans karaoke was burned in, so say what it was translated from.
- Low-confidence audio: say the translation is approximate (大意翻译).

## 7. Output files (in the clip folder)
- `youtube-shorts-descriptions.md`: header (source, subtitle status, publish order), then per clip: title (plus alternative), description.
- `descriptions.json`: a list of objects with publish_order, clip, file, thumbnail, thumbnail_text, title, title_alt, description, tags, source_url, credit, timecode, source_subs, karaoke, and claim_status when relevant.

## 8. Publishing rules to respect (for whoever uploads)
- One topic or batch per calendar day.
- Don't re-publish a source video that was already used without warning.
- For graphic content, suggest marking it mature or age-restricted.

## Quality check before handing off
- [ ] Every title line is backed by a real transcript line
- [ ] Credit, full URL, exact timecodes and disclaimer are present
- [ ] Subtitle status is stated
- [ ] Unverified claims are hedged in the title AND the description
- [ ] The first line of the description repeats the hook
