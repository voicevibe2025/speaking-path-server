import os
import math
import json
import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# --- Utility grading helpers ---

def _level_from_score(score: float) -> str:
    if score >= 85:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 60:
        return "FAIR"
    return "NEEDS_IMPROVEMENT"


def _safe_import(module: str):
    try:
        return __import__(module, fromlist=["*"])  # type: ignore
    except Exception:
        return None


def _env_flag(name: str, default: str = "0") -> bool:
    val = os.environ.get(name, default).strip().lower()
    return val in {"1", "true", "yes", "on"}


# --- Core analysis steps ---

def transcribe_with_whisperx(audio_path: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns transcript and word-level timestamps using WhisperX (if available).
    """
    # Disabled by default to avoid heavy dependencies on Windows; enable via ENABLE_WHISPERX=1
    if os.name == 'nt' or not _env_flag('ENABLE_WHISPERX'):
        return "", []
    whisperx = _safe_import("whisperx")
    torch = _safe_import("torch")
    if whisperx is None or torch is None:
        return "", []
    try:
        # Force CPU on Windows to avoid missing cuDNN DLLs
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
        device = "cpu"
        model_size = os.environ.get("WHISPER_MODEL_SIZE", "base")
        model = whisperx.load_model(model_size, device)
        result = model.transcribe(audio_path)
        language = result.get("language") or "en"
        # Align for word-level timestamps
        align_model, metadata = whisperx.load_align_model(language_code=language, device=device)
        aligned = whisperx.align(result["segments"], align_model, metadata, audio_path, device)
        words: List[Dict[str, Any]] = []
        transcript_parts: List[str] = []
        for seg in aligned.get("segments", []):
            seg_words = seg.get("words") or []
            for w in seg_words:
                words.append({
                    "word": w.get("word") or "",
                    "start": float(w.get("start") or 0.0),
                    "end": float(w.get("end") or 0.0),
                })
            if seg.get("text"):
                transcript_parts.append(seg["text"])
        transcript = " ".join(tp.strip() for tp in transcript_parts if tp)
        return transcript.strip(), words
    except Exception as e:
        logger.exception("whisperx transcription failed: %s", e)
        return "", []


def transcribe_with_faster_whisper(audio_path: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns transcript and word-level timestamps using faster-whisper when available.
    Fallback: empty transcript and no words.
    """
    # Ensure ctranslate2 uses CPU to avoid missing cuDNN DLL errors on Windows
    os.environ.setdefault("CT2_FORCE_CPU", "1")
    fw = _safe_import("faster_whisper")
    if fw is None:
        logger.warning("faster-whisper not installed; skipping transcription")
        return "", []

    try:
        WhisperModel = getattr(fw, "WhisperModel")
        model_size = os.environ.get("WHISPER_MODEL_SIZE", "base")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(audio_path, word_timestamps=True)
        words: List[Dict[str, Any]] = []
        transcript_parts: List[str] = []
        for seg in segments:
            # seg.words may be None depending on model/version
            seg_words = getattr(seg, "words", None) or []
            for w in seg_words:
                words.append({
                    "word": getattr(w, "word", ""),
                    "start": float(getattr(w, "start", 0.0) or 0.0),
                    "end": float(getattr(w, "end", 0.0) or 0.0),
                })
            transcript_parts.append(getattr(seg, "text", ""))
        transcript = " ".join(tp.strip() for tp in transcript_parts if tp)
        return transcript.strip(), words
    except Exception as e:
        logger.exception("faster-whisper transcription failed: %s", e)
        return "", []


def detect_pauses_from_words(words: List[Dict[str, Any]], min_gap: float = 0.35) -> List[float]:
    pauses: List[float] = []
    for i in range(1, len(words)):
        prev_end = float(words[i - 1].get("end", 0.0) or 0.0)
        cur_start = float(words[i].get("start", 0.0) or 0.0)
        gap = max(0.0, cur_start - prev_end)
        if gap >= min_gap:
            pauses.append(round(gap, 2))
    return pauses


def detect_pauses_with_pyannote(audio_path: str, threshold: float = 0.35) -> List[float]:
    """
    Use pyannote.audio VAD to estimate pauses (non-speech gaps) if available.
    Requires HUGGING_FACE_HUB_TOKEN in environment and pyannote.audio installed.
    """
    # Disabled by default; enable explicitly with ENABLE_PYANNOTE=1
    if not _env_flag('ENABLE_PYANNOTE'):
        return []
    pipeline_mod = _safe_import("pyannote.audio")
    if pipeline_mod is None:
        return []
    try:
        from pyannote.audio import Pipeline  # type: ignore
        hf_token = os.environ.get("HUGGING_FACE_HUB_TOKEN") or os.environ.get("HF_TOKEN")
        if not hf_token:
            return []
        pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection", use_auth_token=hf_token)
        vad = pipeline(audio_path)
        # vad is an Annotation of speech regions; derive non-speech gaps
        speech_segments = list(vad.get_timeline().support())
        pauses: List[float] = []
        for i in range(1, len(speech_segments)):
            prev_end = float(speech_segments[i - 1].end)
            cur_start = float(speech_segments[i].start)
            gap = max(0.0, cur_start - prev_end)
            if gap >= threshold:
                pauses.append(round(gap, 2))
        return pauses
    except Exception as e:
        logger.exception("pyannote VAD failed: %s", e)
        return []


def detect_stutters(words: List[Dict[str, Any]]) -> int:
    count = 0
    for i in range(1, len(words)):
        w0 = (words[i - 1].get("word") or "").strip(" .,!?\n\t").lower()
        w1 = (words[i].get("word") or "").strip(" .,!?\n\t").lower()
        if w0 and w1 and w0 == w1 and len(w1) <= 3:
            count += 1
    return count


def detect_mispronunciations_placeholder(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder mispronunciation detector until MFA is configured. Flags some
    commonly tricky words if they appear.
    """
    tricky = {
        "comfortable": "kumf-tuh-buhl",
        "vegetable": "vej-tuh-buhl",
        "certificate": "ser-ti-fi-kit",
    }
    results: List[Dict[str, Any]] = []
    for w in words:
        token = (w.get("word") or "").lower().strip()
        if token in tricky:
            results.append({
                "word": token,
                "expected": tricky[token],
                "actual": token,
                "timestamp": float(w.get("start") or 0.0),
            })
    return results


def generate_gemini_feedback(context: Dict[str, Any]) -> str:
    """
    Generates feedback using Gemini if API key is present.
    Fallback: simple heuristic feedback string.
    """
    api = _safe_import("google.generativeai")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api or not api_key:
        # Fallback – use transcript-aware heuristics
        pauses = context.get("pauses", []) or []
        stutters = int(context.get("stutters") or 0)
        mis = context.get("mispronunciations", []) or []
        transcript = (context.get("transcript") or "").strip()
        stats = context.get("stats") or {}
        wpm = stats.get("wpm")
        filler_total = stats.get("filler_total")
        longest_pause = stats.get("longest_pause")
        top_fillers = stats.get("top_fillers") or []
        quote = stats.get("quote")

        headline = "Nice effort." if transcript else "Recording received."
        details = []
        if stutters:
            details.append(f"noticed {stutters} repetition(s)")
        if len(pauses):
            details.append(f"{len(pauses)} pause(s)")
        if filler_total:
            common = ", ".join(f"{w}×{c}" for w, c in top_fillers[:2]) if top_fillers else str(filler_total)
            details.append(f"fillers ({common})")
        if wpm:
            details.append(f"pace ≈{wpm} WPM")
        if longest_pause:
            details.append(f"longest pause {longest_pause}s")
        stats_line = ("; ".join(details) + ".") if details else ""

        quote_line = f"Example: \"{quote}\"" if quote else ""
        closing = "Try to maintain steady phrasing and reduce fillers by pausing briefly instead."
        return " ".join(x for x in [headline, stats_line, quote_line, closing] if x)

    try:
        api.configure(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        model = api.GenerativeModel(model_name)
        prompt = (
            "You are a precise English speaking coach. Use the user's exact transcript and stats to give targeted feedback.\n"
            "Requirements:\n"
            "- Reference one short quote from the transcript if helpful (do not over-quote).\n"
            "- Comment on pace (WPM), pauses (mention the longest pause if notable), stutters/repetitions, filler words (name the common ones), and clarity/coherence.\n"
            "- Keep feedback to 3–5 sentences.\n"
            "- End with a short bulleted list of 2–3 actionable practice tips tailored to the issues observed.\n"
        )
        content = json.dumps(context, ensure_ascii=False)
        resp = model.generate_content(prompt + "\nJSON:\n" + content)
        txt = getattr(resp, "text", None)
        return txt or "Great job! Focus on reducing filler words and maintaining steady pace."
    except Exception:
        logger.exception("Gemini feedback generation failed")
        return "Great job! Focus on reducing filler words and maintaining steady pace."


def analyze_fluency(audio_path: str) -> Dict[str, Any]:
    """
    Full pipeline with graceful fallbacks.
    Returns a dict with keys: transcript, pauses, stutters, mispronunciations, feedback,
    and suggested numeric scores.
    """
    # Prefer WhisperX alignment if available; fallback to faster-whisper
    transcript, words = transcribe_with_whisperx(audio_path)
    if not words:
        transcript, words = transcribe_with_faster_whisper(audio_path)

    # If no words from transcription, attempt a lightweight fallback: keep transcript empty
    # Prefer pyannote VAD if configured; otherwise derive from word gaps
    pauses = detect_pauses_with_pyannote(audio_path) if audio_path else []
    if not pauses:
        pauses = detect_pauses_from_words(words) if words else []
    stutters = detect_stutters(words) if words else 0
    mis = detect_mispronunciations_placeholder(words) if words else []

    # Duration and pacing stats
    duration_sec = 0.0
    if words:
        try:
            start_t = float(words[0].get("start") or 0.0)
            end_t = float(words[-1].get("end") or 0.0)
            duration_sec = max(0.0, end_t - start_t)
        except Exception:
            duration_sec = 0.0
    token_list = re.findall(r"[A-Za-z']+", transcript.lower()) if transcript else []
    word_count = len(token_list)
    wpm = round(word_count / (duration_sec / 60.0), 1) if duration_sec > 0 and word_count > 0 else None
    # Filler words
    single_fillers = {"um","uh","erm","hmm","like","actually","basically","literally","so","well"}
    phrase_fillers = [("you","know"), ("i","mean"), ("sort","of"), ("kind","of")]
    filler_counts: Dict[str, int] = {}
    # Count single-token fillers
    for tok in token_list:
        if tok in single_fillers:
            filler_counts[tok] = filler_counts.get(tok, 0) + 1
    # Count bigram phrase fillers
    for i in range(len(token_list) - 1):
        pair = (token_list[i], token_list[i + 1])
        if pair in phrase_fillers:
            key = " ".join(pair)
            filler_counts[key] = filler_counts.get(key, 0) + 1
    filler_total = sum(filler_counts.values())
    # Pause stats
    longest_pause = max(pauses) if pauses else None
    avg_pause = round(sum(pauses)/len(pauses), 2) if pauses else None

    # Short quote excerpt for targeted feedback
    quote = None
    if transcript:
        # pick the longest short sentence-like chunk (<= 60 chars)
        chunks = re.split(r"[\.\?!,;]\s+", transcript)
        chunks = [c.strip() for c in chunks if c.strip()]
        if chunks:
            chunks_sorted = sorted(chunks, key=lambda c: len(c), reverse=True)
            for c in chunks_sorted:
                if len(c) <= 60:
                    quote = c
                    break
            if not quote:
                quote = chunks_sorted[0][:60]

    # Heuristic scoring
    base = 82.0
    penalty = 0.0
    penalty += min(10.0, len(pauses) * 0.8)
    penalty += min(8.0, stutters * 1.5)
    penalty += min(8.0, len(mis) * 1.5)
    overall = max(50.0, min(98.0, base - penalty))

    def score_tuple(score: float, fb: str) -> Dict[str, Any]:
        return {"score": round(score, 1), "level": _level_from_score(score), "feedback": fb}

    pronunciation = score_tuple(max(60.0, overall - len(mis) * 2), "Pronunciation is generally clear.")
    fluency = score_tuple(max(60.0, overall - len(pauses) * 1.2 - stutters), "Flow is mostly smooth with minor pauses.")
    vocabulary = score_tuple(max(60.0, overall - 2.0), "Vocabulary usage is appropriate.")
    grammar = score_tuple(max(60.0, overall - 3.0), "Grammar is acceptable with minor mistakes.")
    coherence = score_tuple(max(60.0, overall - 1.5), "Ideas are organized and coherent.")

    # Build adaptive suggestions
    sugs: List[str] = []
    if stutters:
        sugs.append("Before starting, take one calm breath and begin the first word smoothly instead of repeating it.")
    if filler_total:
        names = ", ".join(w for w, _ in (sorted(filler_counts.items(), key=lambda x: -x[1])[:3]))
        sugs.append(f"Record a 30s answer avoiding fillers like {names}; insert a short silent pause instead.")
    if longest_pause and longest_pause > 1.2:
        sugs.append("Use linking phrases (for example, 'and also', 'because', 'as a result') to avoid long gaps.")
    if wpm and wpm < 90:
        sugs.append("Increase pace toward ~120–140 WPM by speaking in full phrases (group 3–5 words per breath).")
    if wpm and wpm > 170:
        sugs.append("Slow to ~130–150 WPM and add short 0.3–0.6s pauses at commas.")
    if word_count < 20:
        sugs.append("Add one reason and one example to extend your answer by 1–2 sentences.")
    if not sugs:
        sugs = ["Practice linking words", "Vary your intonation"]
    sugs = sugs[:3]

    feedback_text = generate_gemini_feedback({
        "transcript": transcript,
        "pauses": pauses,
        "stutters": stutters,
        "mispronunciations": mis,
        "stats": {
            "duration_sec": round(duration_sec, 2) if duration_sec else None,
            "wpm": wpm,
            "word_count": word_count,
            "filler_total": filler_total,
            "top_fillers": sorted(filler_counts.items(), key=lambda x: -x[1])[:3],
            "avg_pause": avg_pause,
            "longest_pause": longest_pause,
            "quote": quote,
        }
    })

    return {
        "transcript": transcript,
        "pauses": pauses,
        "stutters": stutters,
        "mispronunciations": mis,
        "overall_score": round(overall, 1),
        "pronunciation": pronunciation,
        "fluency": fluency,
        "vocabulary": vocabulary,
        "grammar": grammar,
        "coherence": coherence,
        "feedback": feedback_text,
        "suggestions": sugs,
        "duration_sec": round(duration_sec, 2) if duration_sec else None,
        "wpm": wpm,
        "filler_counts": filler_counts,
    }
