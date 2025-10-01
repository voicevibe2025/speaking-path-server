"""
AI Evaluation Services for VoiceVibe
Handles Whisper API transcription and LLM-based evaluation
"""
import os
import json
import asyncio
import aiohttp
import subprocess
from typing import Dict, List, Optional, Any
import base64
import tempfile
import time
try:
    import openai  # Optional dependency; only used if OPENAI_API_KEY is set
except Exception:  # pragma: no cover - optional dependency not installed
    openai = None
# Defer openai-whisper import to runtime to avoid import-time overhead and potential
# coverage/numba incompatibility (coverage.types.Tracer vs TTracer)
_openai_whisper = None
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class WhisperService:
    """
    Service for handling Whisper API transcription
    """

    def __init__(self):
        # Keep API key detection for potential future hosted use, but local model doesn't need it
        self.api_key = os.getenv('WHISPER_API_KEY', os.getenv('OPENAI_API_KEY'))
        # Lazy-load local whisper model name (match existing implementation)
        self.model_name = "tiny.en"

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API

        Args:
            audio_data: Audio file bytes
            language: Target language code

        Returns:
            Transcription result with text and metadata
        """
        try:
            # Accept base64 string or raw bytes
            if isinstance(audio_data, str):
                try:
                    audio_b64 = audio_data.split(",", 1)[-1]
                except Exception:
                    audio_b64 = audio_data
                audio_bytes = base64.b64decode(audio_b64)
            else:
                audio_bytes = audio_data

            # Persist to a temp file that Whisper (ffmpeg) can read
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                temp_path = tmp.name

            # Normalize to 16kHz mono WAV to avoid ASR shape errors on certain inputs
            input_path = temp_path
            conv_path = temp_path + ".wav"
            try:
                subprocess.run(
                    ['ffmpeg', '-y', '-i', temp_path, '-ac', '1', '-ar', '16000', conv_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                input_path = conv_path
            except Exception as e:
                logger.warning("ffmpeg conversion failed, using original: %s", e)

            # Choose engine preference via env flags
            # - ENABLE_FASTER_WHISPER or PREFER_FASTER_WHISPER: prefer faster-whisper first
            # - DISABLE_WHISPER: skip openai-whisper entirely (use faster-whisper only)
            prefer_fw = (
                os.environ.get("ENABLE_FASTER_WHISPER", "").strip().lower() in {"1", "true", "yes"}
                or os.environ.get("PREFER_FASTER_WHISPER", "").strip().lower() in {"1", "true", "yes"}
            )
            disable_whisper = (os.environ.get("DISABLE_WHISPER", "").strip().lower() in {"1", "true", "yes"})
            strict_dedup = (os.environ.get("WHISPER_STRICT_DEDUP", "").strip().lower() in {"1", "true", "yes"})
            disable_fw = (os.environ.get("DISABLE_FASTER_WHISPER", "").strip().lower() in {"1", "true", "yes"})
            # Prefer hosted OpenAI Whisper API when an API key is present, unless explicitly disabled
            prefer_api = (
                os.environ.get("DISABLE_OPENAI_WHISPER_API", "").strip().lower() not in {"1", "true", "yes"}
            ) and bool(self.api_key)

            def _transcribe_with_fw(path: str, lang: str) -> Optional[str]:
                """Best-effort faster-whisper transcription on CPU. Returns text or None on failure."""
                try:
                    # Ensure CPU to avoid missing GPU drivers on Railway
                    os.environ.setdefault("CT2_FORCE_CPU", "1")
                    import faster_whisper  # type: ignore
                except Exception:
                    return None
                try:
                    # Share a single model instance across calls
                    if not hasattr(self, "_fw_model") or self._fw_model is None:
                        model_size = os.environ.get("WHISPER_MODEL_SIZE", "tiny")
                        try:
                            self._fw_model = faster_whisper.WhisperModel(model_size, device="cpu", compute_type="int8")
                        except Exception:
                            # Fallback to tiny if tiny.en not found
                            self._fw_model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
                    segments, _info = self._fw_model.transcribe(
                        path,
                        language=lang or None,
                        word_timestamps=False,
                        vad_filter=False,
                        beam_size=1,
                        best_of=1,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        compression_ratio_threshold=2.4,
                        no_speech_threshold=0.6,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.05,
                        max_new_tokens=64,
                        log_prob_threshold=-1.0,
                        hallucination_silence_threshold=0.5,
                    )
                    parts: List[str] = []
                    for seg in segments:
                        parts.append(getattr(seg, "text", ""))
                    out = (" ".join(p.strip() for p in parts if p).strip()) or ""

                    # Collapse simple repeated phrase patterns for short utterances
                    def _collapse_repeats(s: str) -> str:
                        try:
                            import re as _re
                            # Compare using normalized tokens but preserve original spacing
                            words = (_re.sub(r"\s+", " ", s or "").strip()).split(" ")
                            norm = [
                                _re.sub(r"[^A-Za-z0-9']+", "", w.replace("’", "'").replace("`", "'"))
                                .lower()
                                for w in words
                            ]
                            n = len(words)
                            if n <= 3:
                                return " ".join(words)
                            i = 0
                            out_words: List[str] = []
                            while i < n:
                                max_w = min(5, n - i)
                                collapsed = False
                                for w in range(max_w, 1, -1):
                                    chunk_norm = norm[i:i+w]
                                    if any(t == "" for t in chunk_norm):
                                        continue
                                    repeats = 1
                                    while (
                                        i + (repeats * w) + w <= n
                                        and norm[i + repeats*w:i + (repeats+1)*w] == chunk_norm
                                    ):
                                        repeats += 1
                                    if repeats >= 2:
                                        # Keep only the first occurrence
                                        out_words.extend(words[i:i+w])
                                        i += repeats * w
                                        collapsed = True
                                        break
                                if not collapsed:
                                    out_words.append(words[i])
                                    i += 1
                            return " ".join(out_words)
                        except Exception:
                            return s

                    if strict_dedup or len(out.split()) <= 30:
                        out = _collapse_repeats(out)
                    return out
                except Exception as e:
                    logger.warning("faster-whisper transcription failed: %s", e)
                    return None

            def _transcribe_with_fw_vad(path: str, lang: str) -> Optional[str]:
                """Secondary pass with VAD enabled to curb repetitions in short utterances."""
                try:
                    os.environ.setdefault("CT2_FORCE_CPU", "1")
                    import faster_whisper  # type: ignore
                except Exception:
                    return None
                try:
                    if not hasattr(self, "_fw_model") or self._fw_model is None:
                        model_size = os.environ.get("WHISPER_MODEL_SIZE", "tiny")
                        try:
                            self._fw_model = faster_whisper.WhisperModel(model_size, device="cpu", compute_type="int8")
                        except Exception:
                            self._fw_model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
                    segments, _info = self._fw_model.transcribe(
                        path,
                        language=lang or None,
                        word_timestamps=False,
                        vad_filter=True,
                        beam_size=1,
                        best_of=1,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        compression_ratio_threshold=2.4,
                        no_speech_threshold=0.6,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.05,
                        max_new_tokens=64,
                        log_prob_threshold=-1.0,
                        hallucination_silence_threshold=0.5,
                    )
                    parts: List[str] = []
                    for seg in segments:
                        parts.append(getattr(seg, "text", ""))
                    out = (" ".join(p.strip() for p in parts if p).strip()) or ""
                    # Reuse collapser
                    def _collapse_repeats(s: str) -> str:
                        try:
                            import re as _re
                            words = (_re.sub(r"\s+", " ", s or "").strip()).split(" ")
                            norm = [
                                _re.sub(r"[^A-Za-z0-9']+", "", w.replace("’", "'").replace("`", "'"))
                                .lower()
                                for w in words
                            ]
                            n = len(words)
                            if n <= 3:
                                return " ".join(words)
                            i = 0
                            out_words: List[str] = []
                            while i < n:
                                max_w = min(5, n - i)
                                collapsed = False
                                for w in range(max_w, 1, -1):
                                    chunk_norm = norm[i:i+w]
                                    if any(t == "" for t in chunk_norm):
                                        continue
                                    repeats = 1
                                    while (
                                        i + (repeats * w) + w <= n
                                        and norm[i + repeats*w:i + (repeats+1)*w] == chunk_norm
                                    ):
                                        repeats += 1
                                    if repeats >= 2:
                                        out_words.extend(words[i:i+w])
                                        i += repeats * w
                                        collapsed = True
                                        break
                                if not collapsed:
                                    out_words.append(words[i])
                                    i += 1
                            return " ".join(out_words)
                        except Exception:
                            return s
                    if len(out.split()) <= 30:
                        out = _collapse_repeats(out)
                    return out
                except Exception as e:
                    logger.warning("faster-whisper (VAD) transcription failed: %s", e)
                    return None

            def _transcribe_with_openai_whisper(path: str, lang: str) -> Optional[str]:
                # Allow disabling to avoid PyTorch weight load and coverage/numba issues on CPU-only hosts
                if os.environ.get("DISABLE_WHISPER", "").strip().lower() in {"1", "true", "yes"}:
                    return None
                try:
                    global _openai_whisper
                    if _openai_whisper is None:
                        # Patch coverage.types to handle numba's coverage_support across versions
                        try:
                            import coverage.types as _cov_types  # type: ignore
                            # Map Tracer <-> TTracer
                            if not hasattr(_cov_types, 'Tracer') and hasattr(_cov_types, 'TTracer'):
                                setattr(_cov_types, 'Tracer', getattr(_cov_types, 'TTracer'))
                            if not hasattr(_cov_types, 'TTracer') and hasattr(_cov_types, 'Tracer'):
                                setattr(_cov_types, 'TTracer', getattr(_cov_types, 'Tracer'))
                            # Map ShouldTraceFn <-> TShouldTraceFn
                            if not hasattr(_cov_types, 'TShouldTraceFn') and hasattr(_cov_types, 'ShouldTraceFn'):
                                setattr(_cov_types, 'TShouldTraceFn', getattr(_cov_types, 'ShouldTraceFn'))
                            if not hasattr(_cov_types, 'ShouldTraceFn') and hasattr(_cov_types, 'TShouldTraceFn'):
                                setattr(_cov_types, 'ShouldTraceFn', getattr(_cov_types, 'TShouldTraceFn'))
                            # Define a minimal fallback when neither exists (older coverage.py versions)
                            if not hasattr(_cov_types, 'TShouldTraceFn') and not hasattr(_cov_types, 'ShouldTraceFn'):
                                try:
                                    _T = _cov_types.Callable[[str, _cov_types.FrameType], _cov_types.TFileDisposition]  # type: ignore[attr-defined]
                                except Exception:
                                    _T = object  # type: ignore
                                setattr(_cov_types, 'TShouldTraceFn', _T)
                                setattr(_cov_types, 'ShouldTraceFn', _T)
                            # Map ShouldStartContextFn <-> TShouldStartContextFn
                            if not hasattr(_cov_types, 'TShouldStartContextFn') and hasattr(_cov_types, 'ShouldStartContextFn'):
                                setattr(_cov_types, 'TShouldStartContextFn', getattr(_cov_types, 'ShouldStartContextFn'))
                            if not hasattr(_cov_types, 'ShouldStartContextFn') and hasattr(_cov_types, 'TShouldStartContextFn'):
                                setattr(_cov_types, 'ShouldStartContextFn', getattr(_cov_types, 'TShouldStartContextFn'))
                            # Fallback for ShouldStartContextFn when neither exists
                            if not hasattr(_cov_types, 'TShouldStartContextFn') and not hasattr(_cov_types, 'ShouldStartContextFn'):
                                try:
                                    _S = _cov_types.Callable[[_cov_types.FrameType], _cov_types.Optional[str]]  # type: ignore[attr-defined]
                                except Exception:
                                    _S = object  # type: ignore
                                setattr(_cov_types, 'TShouldStartContextFn', _S)
                                setattr(_cov_types, 'ShouldStartContextFn', _S)
                            # Ensure TCheckIncludeFn exists (Callable[[str, FrameType], bool])
                            if not hasattr(_cov_types, 'TCheckIncludeFn'):
                                try:
                                    _C = _cov_types.Callable[[str, _cov_types.FrameType], bool]  # type: ignore[attr-defined]
                                except Exception:
                                    _C = object  # type: ignore
                                setattr(_cov_types, 'TCheckIncludeFn', _C)
                        except Exception:
                            pass
                        import whisper as _w
                        _openai_whisper = _w
                    if not hasattr(self, "_model") or self._model is None:
                        self._model = _openai_whisper.load_model(self.model_name)
                    result = self._model.transcribe(path, language=lang)
                    return (result.get("text") or "").strip()
                except Exception as e:
                    logger.warning("openai-whisper transcription failed: %s", e)
                    return None

            started = time.perf_counter()
            text: Optional[str] = None
            engine_used = None

            try:
                # Try OpenAI Whisper API (hosted) first if available
                if prefer_api:
                    try:
                        import aiohttp as _aio
                        headers = {"Authorization": f"Bearer {self.api_key}"}
                        timeout = _aio.ClientTimeout(total=60)
                        async with _aio.ClientSession(headers=headers, timeout=timeout) as session:
                            with open(input_path, "rb") as f:
                                form = _aio.FormData()
                                form.add_field("file", f, filename=os.path.basename(input_path), content_type="audio/wav")
                                form.add_field("model", os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1"))
                                if language:
                                    form.add_field("language", language)
                                form.add_field("response_format", "json")
                                async with session.post("https://api.openai.com/v1/audio/transcriptions", data=form) as resp:
                                    if resp.status == 200:
                                        data = await resp.json()
                                        text = (data.get("text") or "").strip()
                                        if text:
                                            engine_used = "openai-api"
                                    else:
                                        body = await resp.text()
                                        logger.warning("OpenAI Whisper API error %s: %s", resp.status, body[:200])
                    except Exception as e:
                        logger.warning("OpenAI Whisper API call failed: %s", e)

                if (prefer_fw or disable_whisper) and not disable_fw:
                    if not text:
                        text = _transcribe_with_fw(input_path, language)
                    engine_used = engine_used or ("faster-whisper" if text is not None else None)
                    if not disable_whisper and (text is None or text == ""):
                        text = _transcribe_with_openai_whisper(input_path, language)
                        engine_used = engine_used or ("openai-whisper" if text is not None else None)
                else:
                    if not text:
                        text = _transcribe_with_openai_whisper(input_path, language)
                    engine_used = engine_used or ("openai-whisper" if text is not None else None)
                    if (text is None or text == "") and not disable_fw:
                        text = _transcribe_with_fw(input_path, language)
                        engine_used = engine_used or ("faster-whisper" if text is not None else None)

                duration = round(time.perf_counter() - started, 3)
                final_text = (text or "").strip()

                # Repetition detector (generic for short utterances)
                def _repetition_score(s: str) -> int:
                    try:
                        import re as _re
                        toks = [t for t in _re.findall(r"[A-Za-z0-9']+", (s or '').lower())]
                        n = len(toks)
                        if n < 4:
                            return 0
                        score = 0
                        i = 0
                        while i < n - 3:
                            matched = False
                            for w in range(min(5, (n - i) // 2), 1, -1):
                                a = toks[i:i+w]
                                b = toks[i+w:i+2*w]
                                if a and a == b:
                                    score += 1
                                    i += 2*w
                                    matched = True
                                    break
                            if not matched:
                                i += 1
                        return score
                    except Exception:
                        return 0

                def _collapse_repeats_text(s: str) -> str:
                    try:
                        import re as _re
                        words = (_re.sub(r"\s+", " ", s or "").strip()).split(" ")
                        norm = [
                            _re.sub(r"[^A-Za-z0-9']+", "", w.replace("’", "'").replace("`", "'"))
                            .lower()
                            for w in words
                        ]
                        n = len(words)
                        if n <= 3:
                            return " ".join(words)
                        i = 0
                        out_words: List[str] = []
                        while i < n:
                            max_w = min(5, n - i)
                            collapsed = False
                            for w in range(max_w, 1, -1):
                                chunk_norm = norm[i:i+w]
                                if any(t == "" for t in chunk_norm):
                                    continue
                                repeats = 1
                                while (
                                    i + (repeats * w) + w <= n
                                    and norm[i + repeats*w:i + (repeats+1)*w] == chunk_norm
                                ):
                                    repeats += 1
                                if repeats >= 2:
                                    out_words.extend(words[i:i+w])
                                    i += repeats * w
                                    collapsed = True
                                    break
                            if not collapsed:
                                out_words.append(words[i])
                                i += 1
                        return " ".join(out_words)
                    except Exception:
                        return s

                # If repetition seems present and we can try VAD, do a second pass
                try:
                    if _repetition_score(final_text) >= 1 and prefer_fw and not disable_fw:
                        alt = _transcribe_with_fw_vad(input_path, language)
                        if alt:
                            # Prefer the alternative if it reduces repetition noticeably
                            if _repetition_score(alt) < _repetition_score(final_text):
                                final_text = alt.strip()
                except Exception:
                    pass

                # Final sanitary collapse for short phrases
                try:
                    if final_text:
                        if strict_dedup or len(final_text.split()) <= 30:
                            final_text = _collapse_repeats_text(final_text)
                except Exception:
                    pass

                out = {
                    "text": final_text,
                    "language": language,
                    "duration": duration,
                    "segments": []
                }
                logger.info("Audio transcribed via %s in %.2fs (len=%d)", engine_used or "unknown", duration, len(final_text))
                return out
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception:
                    pass
                try:
                    if 'conv_path' in locals() and os.path.exists(conv_path):
                        os.unlink(conv_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            raise


class LLMEvaluationService:
    """
    Service for LLM-based language evaluation
    """

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = "gpt-4"

        if self.openai_api_key and openai is not None:
            openai.api_key = self.openai_api_key
        elif self.openai_api_key and openai is None:
            logger.info("OpenAI SDK not installed; skipping OpenAI init")

    async def evaluate_pronunciation(
        self,
        transcription: str,
        audio_features: Optional[Dict] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate pronunciation using LLM prompt engineering

        Args:
            transcription: Transcribed text
            audio_features: Optional audio analysis features
            user_level: User's proficiency level

        Returns:
            Pronunciation evaluation results
        """
        prompt = self._create_pronunciation_prompt(transcription, user_level)

        try:
            # Placeholder for LLM API call
            evaluation = {
                "score": 85,
                "issues": [],
                "suggestions": [
                    "Focus on vowel sounds in words like 'about'",
                    "Practice the 'th' sound in 'think' and 'that'"
                ],
                "phonetic_analysis": {
                    "stress_patterns": "Good",
                    "intonation": "Natural",
                    "rhythm": "Slightly rushed"
                }
            }

            return evaluation

        except Exception as e:
            logger.error(f"Pronunciation evaluation error: {str(e)}")
            raise

    async def evaluate_grammar(
        self,
        transcription: str,
        context: Optional[str] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate grammar using LLM analysis

        Args:
            transcription: Transcribed text
            context: Conversation context
            user_level: User's proficiency level

        Returns:
            Grammar evaluation results
        """
        prompt = self._create_grammar_prompt(transcription, context, user_level)

        try:
            # Placeholder for LLM API call
            evaluation = {
                "score": 78,
                "errors": [
                    {
                        "type": "verb_tense",
                        "text": "I go there yesterday",
                        "correction": "I went there yesterday",
                        "explanation": "Use past tense 'went' for past actions"
                    }
                ],
                "suggestions": [
                    "Review past tense verb forms",
                    "Practice subject-verb agreement"
                ],
                "complexity_level": "intermediate"
            }

            return evaluation

        except Exception as e:
            logger.error(f"Grammar evaluation error: {str(e)}")
            raise

    async def evaluate_fluency(
        self,
        transcription: str,
        duration: float,
        pauses: Optional[List[float]] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate speaking fluency

        Args:
            transcription: Transcribed text
            duration: Total speaking duration
            pauses: List of pause durations
            user_level: User's proficiency level

        Returns:
            Fluency evaluation results
        """
        words_per_minute = self._calculate_wpm(transcription, duration)

        try:
            evaluation = {
                "score": 82,
                "words_per_minute": words_per_minute,
                "pace": "good",
                "hesitations": "minimal",
                "filler_words": ["um", "uh"],
                "suggestions": [
                    "Try to reduce filler words",
                    "Maintain consistent speaking pace"
                ]
            }

            return evaluation

        except Exception as e:
            logger.error(f"Fluency evaluation error: {str(e)}")
            raise

    async def evaluate_vocabulary(
        self,
        transcription: str,
        topic: Optional[str] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Evaluate vocabulary usage

        Args:
            transcription: Transcribed text
            topic: Conversation topic
            user_level: User's proficiency level

        Returns:
            Vocabulary evaluation results
        """
        prompt = self._create_vocabulary_prompt(transcription, topic, user_level)

        try:
            evaluation = {
                "score": 75,
                "level": "B1",
                "word_variety": "moderate",
                "advanced_words": ["accomplish", "perspective"],
                "suggestions": [
                    "Use more varied adjectives",
                    "Try incorporating phrasal verbs"
                ],
                "topic_relevance": "good"
            }

            return evaluation

        except Exception as e:
            logger.error(f"Vocabulary evaluation error: {str(e)}")
            raise

    async def evaluate_cultural_appropriateness(
        self,
        transcription: str,
        scenario: str,
        cultural_context: str = "Indonesian"
    ) -> Dict[str, Any]:
        """
        Evaluate cultural appropriateness for Indonesian learners

        Args:
            transcription: Transcribed text
            scenario: Speaking scenario
            cultural_context: Cultural background

        Returns:
            Cultural appropriateness evaluation
        """
        prompt = self._create_cultural_prompt(transcription, scenario, cultural_context)

        try:
            evaluation = {
                "score": 88,
                "appropriateness": "good",
                "formality_level": "appropriate",
                "cultural_notes": [
                    "Good use of polite expressions",
                    "Consider adding more formal greetings in business contexts"
                ],
                "hofstede_alignment": {
                    "power_distance": "respected",
                    "collectivism": "demonstrated",
                    "uncertainty_avoidance": "acknowledged"
                }
            }

            return evaluation

        except Exception as e:
            logger.error(f"Cultural evaluation error: {str(e)}")
            raise

    async def generate_comprehensive_feedback(
        self,
        pronunciation: Dict,
        grammar: Dict,
        fluency: Dict,
        vocabulary: Dict,
        cultural: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback based on all evaluations

        Returns:
            Comprehensive feedback with scores and recommendations
        """
        # Calculate overall score
        scores = [
            pronunciation.get('score', 0),
            grammar.get('score', 0),
            fluency.get('score', 0),
            vocabulary.get('score', 0)
        ]
        if cultural:
            scores.append(cultural.get('score', 0))

        overall_score = sum(scores) / len(scores)

        # Compile feedback
        feedback = {
            "overall_score": round(overall_score, 1),
            "pronunciation_score": pronunciation.get('score', 0),
            "grammar_score": grammar.get('score', 0),
            "fluency_score": fluency.get('score', 0),
            "vocabulary_score": vocabulary.get('score', 0),
            "strengths": self._identify_strengths(scores),
            "areas_for_improvement": self._identify_improvements(
                pronunciation, grammar, fluency, vocabulary
            ),
            "personalized_recommendations": self._generate_recommendations(
                pronunciation, grammar, fluency, vocabulary, user_preferences
            ),
            "next_practice_focus": self._suggest_next_focus(scores),
            "motivational_message": self._generate_motivation(overall_score)
        }

        if cultural:
            feedback["cultural_score"] = cultural.get('score', 0)
            feedback["cultural_insights"] = cultural.get('cultural_notes', [])

        return feedback

    # Helper methods for prompt creation
    def _create_pronunciation_prompt(self, text: str, level: str) -> str:
        return f"""
        Analyze the pronunciation challenges in this transcribed speech from an {level} English learner:
        
        Text: {text}
        
        Identify:
        1. Likely pronunciation errors for Indonesian speakers
        2. Stress pattern issues
        3. Intonation problems
        4. Specific phonemes that need practice
        
        Provide constructive feedback suitable for {level} level.
        """

    def _create_grammar_prompt(self, text: str, context: Optional[str], level: str) -> str:
        return f"""
        Analyze the grammar in this transcribed speech from an {level} English learner:
        
        Text: {text}
        Context: {context or 'General conversation'}
        
        Identify:
        1. Grammar errors with corrections
        2. Sentence structure issues
        3. Tense consistency problems
        4. Subject-verb agreement errors
        
        Provide explanations suitable for {level} level Indonesian learners.
        """

    def _create_vocabulary_prompt(self, text: str, topic: Optional[str], level: str) -> str:
        return f"""
        Analyze the vocabulary usage in this transcribed speech from an {level} English learner:
        
        Text: {text}
        Topic: {topic or 'General'}
        
        Evaluate:
        1. Vocabulary range and variety
        2. Word choice appropriateness
        3. Use of collocations and phrases
        4. Academic or professional vocabulary if relevant
        
        Suggest improvements for {level} level.
        """

    def _create_cultural_prompt(self, text: str, scenario: str, cultural_context: str) -> str:
        return f"""
        Analyze the cultural appropriateness of this speech from an {cultural_context} speaker:
        
        Text: {text}
        Scenario: {scenario}
        
        Consider:
        1. Formality level appropriateness
        2. Politeness strategies
        3. Cultural sensitivity
        4. Hofstede's cultural dimensions for {cultural_context}
        
        Provide culturally-aware feedback.
        """

    def _calculate_wpm(self, text: str, duration: float) -> int:
        """Calculate words per minute"""
        if duration <= 0:
            return 0
        word_count = len(text.split())
        return int((word_count / duration) * 60)

    def _identify_strengths(self, scores: List[float]) -> List[str]:
        """Identify user's strengths based on scores"""
        strengths = []
        categories = ["Pronunciation", "Grammar", "Fluency", "Vocabulary"]

        for i, score in enumerate(scores[:4]):
            if score >= 80:
                strengths.append(f"Strong {categories[i].lower()}")

        return strengths if strengths else ["Consistent effort across all areas"]

    def _identify_improvements(self, *evaluations) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []

        for eval_data in evaluations:
            if eval_data.get('score', 100) < 70:
                if 'suggestions' in eval_data:
                    improvements.extend(eval_data['suggestions'][:1])

        return improvements[:3] if improvements else ["Continue practicing regularly"]

    def _generate_recommendations(self, *evaluations, user_preferences=None) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []

        # Add specific recommendations based on lowest scores
        for eval_data in evaluations:
            if eval_data and eval_data.get('suggestions'):
                recommendations.extend(eval_data['suggestions'][:1])

        # Add preference-based recommendations
        if user_preferences:
            if user_preferences.get('immediate_correction'):
                recommendations.append("Practice with immediate error correction exercises")
            if user_preferences.get('visual_learning'):
                recommendations.append("Use visual aids and diagrams for grammar patterns")

        return recommendations[:5]

    def _suggest_next_focus(self, scores: List[float]) -> str:
        """Suggest next area to focus on"""
        categories = ["pronunciation", "grammar", "fluency", "vocabulary"]
        min_score_idx = scores[:4].index(min(scores[:4]))
        return f"Focus on improving {categories[min_score_idx]} in your next session"

    def _generate_motivation(self, score: float) -> str:
        """Generate motivational message based on score"""
        if score >= 85:
            return "Excellent work! You're making great progress!"
        elif score >= 70:
            return "Good job! Keep practicing to reach the next level!"
        elif score >= 55:
            return "You're improving! Stay consistent with your practice."
        else:
            return "Keep going! Every practice session brings you closer to your goals."
