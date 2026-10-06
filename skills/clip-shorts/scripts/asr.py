"""asr.py: one tiny wrapper so every script can use faster-whisper (preferred) or openai-whisper.

transcribe(path, language="en", model="medium", prompt=None, vad=False) -> [[start, end, word], ...]
Times are relative to the start of `path`. Models are cached per process.
"""
_CACHE = {}


def _load(model):
    if model in _CACHE:
        return _CACHE[model]
    try:
        from faster_whisper import WhisperModel
        m = ("faster", WhisperModel(model, device="auto", compute_type="int8"))
    except ImportError:
        import whisper  # openai-whisper
        m = ("openai", whisper.load_model(model))
    _CACHE[model] = m
    return m


def transcribe(path, language="en", model="medium", prompt=None, vad=False):
    kind, m = _load(model)
    out = []
    if kind == "faster":
        kw = dict(language=language, word_timestamps=True, vad_filter=vad, condition_on_previous_text=False,
                  beam_size=5, initial_prompt=prompt)
        if vad:
            kw["vad_parameters"] = dict(min_silence_duration_ms=300)
        segs, _ = m.transcribe(str(path), **kw)
        for s in segs:
            for w in (s.words or []):
                out.append([round(w.start, 2), round(w.end, 2), w.word.strip()])
    else:
        r = m.transcribe(str(path), language=language, word_timestamps=True, initial_prompt=prompt,
                         condition_on_previous_text=False)
        for s in r["segments"]:
            for w in s.get("words", []):
                out.append([round(w["start"], 2), round(w["end"], 2), w["word"].strip()])
    return out
