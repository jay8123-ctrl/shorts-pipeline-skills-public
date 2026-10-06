# clip-shorts scripts

These scripts build 9:16 YouTube Shorts from a landscape source: one fixed crop per shot, a zh-Hans `\k` karaoke ASS, a title card, and 2-pass x264 sized under 45 MB. `clips.py` is a **worked example config** from a real 5-clip batch. Copy it for each new source and edit it.

## Dependencies
- `ffmpeg` / `ffprobe` with libx264, libass and AAC (any recent build), plus `yt-dlp` for URLs
- `python3` ≥ 3.9 with `pip install numpy pillow opencv-python faster-whisper` (or `openai-whisper` instead of faster-whisper; `asr.py` uses whichever is installed)
- Fonts: `NotoSansCJK-Bold.ttc` and `NotoSansCJK-Regular.ttc` (Noto Sans CJK, ttc index 2 = SC) in `~/.fonts`, or pass `--fonts-dir` / set `FONTS_DIR`
- Face model, only if you use `faces_scan.py`: `face_detection_yunet_2023mar.onnx` from https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet

## Files
| File | Role |
|---|---|
| `build_short.py` | Main build. Per clip it writes `NN-slug.mp4`, `.ass`, `-still.jpg` and `.json` |
| `clips.py` | Config: SOURCE, SUB, CLIPS (in/out, title card, zh/en lines with anchors), MANUAL_X, CUTS, WORD_FIXES, LOGO, layout |
| `common.py`, `asr.py` | Shared helpers (config loader, ffprobe, fps, fonts; whisper wrapper) |
| `transcribe_words.py` | Word timestamps over overlapping 30 s windows → `words.json` |
| `rms.py` | 50 ms RMS strip, so you can put in/out points in pauses |
| `detect_cuts.py` | Hard-cut candidates (frame-difference peaks) → `CUTS` |
| `faces_scan.py` | YuNet face samples → `face_samples.json` (used for the fixed crop x in close-ups) |
| `cut_check.py` | Frame-exact crop switch times → `switch.json` |
| `qa_frames.py` | ffprobe checks (1080×1920, h264 High, aac, < 45 MB, duration) + contact sheets |
| `edge_check.py` | Re-transcribes the first and last 4 s of each master to catch clipped words |
| `make_readme.py` | Writes the deliverables README table from the per-clip JSON |

## Run
```bash
SRC=source.mp4; WORK=work; OUT=out; mkdir -p $WORK $OUT
yt-dlp -S "res,ext:mp4:m4a" -f "bv*+ba/b" --merge-output-format mp4 -o $SRC "$URL"     # if starting from a URL
ffmpeg -i $SRC -vn -ac 1 -ar 16000 $WORK/audio16k.wav

# 1. timings (ranges = the parts of the source your picks come from; --language = spoken language)
python3 transcribe_words.py --audio $WORK/audio16k.wav --range 170 345 --range 1200 1480 --out $WORK/words.json --language en
python3 rms.py $WORK/audio16k.wav 176 182                       # check a cut point sits in a pause

# 2. shots and faces
python3 detect_cuts.py $SRC 170 345                             # paste confirmed times into CUTS
python3 faces_scan.py --src $SRC --model face_detection_yunet_2023mar.onnx --range 170 345 --out $WORK/face_samples.json

# 3. edit clips.py (picks, zh lines ≤ 12 chars, title cards, MANUAL_X for wide/panel shots), then
python3 cut_check.py  --src $SRC --work $WORK --config clips.py
python3 build_short.py --src $SRC --work $WORK --out $OUT --config clips.py            # or list clip ids
python3 qa_frames.py  --out $OUT --work $WORK --config clips.py                         # look at $WORK/qa/sheet_*.jpg
python3 edge_check.py $OUT/*.mp4 --language en
python3 make_readme.py --out $OUT --title "<source> · N 条 Shorts"
```
Without `face_samples.json`, shots fall back to a **centre crop** unless `MANUAL_X` sets x. Without `switch.json`, the crop switches at the cut time. `--target-mb` (default 40.5) sets the 2-pass size target, and `--fps auto` gives 29.97 for 59.94/29.97 sources and 30 otherwise.

## Notes
- Landscape sources only. For portrait or 4:5 sources, use the blurred-fill ffmpeg recipe in `SKILL.md`. Pixelation of sensitive regions is also an ffmpeg recipe there and is not automated here.
- Whisper sometimes hallucinates on short windows (wrong-language gibberish). If a HEAD/TAIL or window looks wrong, re-run it, or pass `--vad` / `--prompt "names, terms"`.
- `build_short.py` asserts that no karaoke line is over ~12.5 characters and that lines don't overlap. Shorten or split the line in `clips.py` if an assert fires.
- No API keys are needed. Nothing here uploads anything.
