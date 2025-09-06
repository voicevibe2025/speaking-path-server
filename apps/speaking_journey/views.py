import re
import string
import tempfile
import os
import base64
import io
import wave
import uuid
import logging
import hashlib
import subprocess
import json
from difflib import SequenceMatcher
import whisper
from typing import Optional
import google.generativeai as genai
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
import requests
from .models import Topic, TopicProgress, UserProfile, PhraseProgress, UserPhraseRecording, VocabularyPracticeSession
from apps.gamification.models import UserLevel, PointsTransaction
from .serializers import (
    SpeakingTopicsResponseSerializer,
    SpeakingTopicDtoSerializer,
    CompleteTopicResponseSerializer,
    UserProfileSerializer,
    PhraseProgressSerializer,
    PhraseSubmissionResultSerializer,
    UserPhraseRecordingSerializer,
    UserPhraseRecordingsResponseSerializer,
    SubmitFluencyPromptRequestSerializer,
    SubmitFluencyPromptResponseSerializer,
    # Vocabulary practice
    StartVocabularyPracticeResponseSerializer,
    SubmitVocabularyAnswerRequestSerializer,
    SubmitVocabularyAnswerResponseSerializer,
    CompleteVocabularyPracticeRequestSerializer,
    CompleteVocabularyPracticeResponseSerializer,
)

logger = logging.getLogger(__name__)

# Simple in-process cache for word clues to speed up repeat sessions
DEF_STYLE_VERSION = "fun_v1"
_DEF_CACHE: dict[str, str] = {}

def _cache_get(word: str) -> Optional[str]:
    try:
        w = (word or '').strip()
        if not w:
            return None
        key = f"{DEF_STYLE_VERSION}|{w}"
        return _DEF_CACHE.get(key)
    except Exception:
        return None

def _cache_set(word: str, definition: str):
    try:
        w = (word or '').strip()
        if not w:
            return
        # Basic size guard to avoid unbounded growth
        if len(_DEF_CACHE) > 1000:
            _DEF_CACHE.clear()
        key = f"{DEF_STYLE_VERSION}|{w}"
        _DEF_CACHE[key] = (definition or '').strip()
    except Exception:
        pass

def _compute_unlocks(user):
    topics = list(Topic.objects.filter(is_active=True).order_by('sequence'))
    completed_sequences = set(
        TopicProgress.objects.filter(user=user, completed=True, topic__is_active=True)
        .values_list('topic__sequence', flat=True)
    )
    unlocked_sequences = set()
    if topics:
        unlocked_sequences.add(topics[0].sequence)
    for t in topics:
        if t.sequence in completed_sequences:
            unlocked_sequences.add(t.sequence)
        else:
            # Unlock if previous is completed
            prev_seq = t.sequence - 1
            if prev_seq in completed_sequences:
                unlocked_sequences.add(t.sequence)
    return topics, completed_sequences, unlocked_sequences


def _normalize_text(text):
    """Normalize text for comparison: lowercase, remove punctuation, extra spaces"""
    if not text:
        return ""
    # Convert to lowercase and remove punctuation
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Remove extra whitespaces and normalize
    text = ' '.join(text.split())
    return text


def _calculate_similarity(expected, actual):
    """Calculate text similarity percentage (0-100)"""
    expected_norm = _normalize_text(expected)
    actual_norm = _normalize_text(actual)

    if not expected_norm or not actual_norm:
        return 0.0

    # Use SequenceMatcher for similarity calculation
    similarity = SequenceMatcher(None, expected_norm, actual_norm).ratio()
    return similarity * 100


def _tokenize_words(text: str):
    try:
        return re.findall(r"[A-Za-z']+", (text or '').lower())
    except Exception:
        return []


def _word_diff_context(expected_phrase: str, transcribed_text: str):
    """Return a small context dict of word-level diffs for targeted feedback."""
    exp = _tokenize_words(expected_phrase)
    got = _tokenize_words(transcribed_text)
    s = SequenceMatcher(None, exp, got)
    good: list[str] = []
    weak: list[str] = []
    extra: list[str] = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            good.extend(exp[i1:i2])
        elif tag == 'replace':
            weak.extend(exp[i1:i2])
            extra.extend(got[j1:j2])
        elif tag == 'delete':
            weak.extend(exp[i1:i2])
        elif tag == 'insert':
            extra.extend(got[j1:j2])
    # Keep unique order while limiting size
    def _uniq(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
    return {
        'goodTokens': _uniq(good)[:6],
        'weakTokens': _uniq(weak)[:6],
        'extraTokens': _uniq(extra)[:6],
    }


def _get_gemini_feedback(expected_phrase: str, transcribed_text: str, accuracy: float) -> str:
    """Get pronunciation feedback using Gemini 2.5 (pro/flash), transcript-aware.

    The feedback references the exact transcript and highlights weak vs. good words,
    then provides 2–3 concise, actionable tips. Falls back gracefully if API/model
    are not available.
    """
    # Build diff context
    diffs = _word_diff_context(expected_phrase, transcribed_text)
    context = {
        'expected': expected_phrase,
        'transcript': transcribed_text,
        'accuracy': round(float(accuracy or 0.0), 1),
        'diffs': diffs,
    }

    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '') or os.environ.get('GOOGLE_API_KEY', '')
    if not api_key:
        # Heuristic fallback when no API key
        weak = diffs.get('weakTokens') or []
        good = diffs.get('goodTokens') or []
        if accuracy >= 80:
            base = "Great job! Your pronunciation was clear."
        elif accuracy >= 60:
            base = "Nice effort. You're close—focus on clarity."
        else:
            base = "Keep practicing. Aim for slower, clearer articulation."
        tips = []
        if weak:
            tips.append(f"Practice the words: {', '.join(weak[:3])} (enunciate each syllable).")
        if good:
            tips.append(f"Well done on: {', '.join(good[:3])}. Keep that consistency.")
        if not tips:
            tips = ["Speak slightly slower and emphasize vowel sounds.", "End each word crisply—avoid dropping final consonants."]
        return base + "\n- " + "\n- ".join(tips[:3])


def _get_gemini_definition(word: str) -> str:
    """Generate a concise learner-friendly definition for a word using Gemini.

    The definition should avoid repeating the word itself and be 5–18 words.
    Fallback returns a heuristic placeholder if API is unavailable.
    """
    safe_word = (word or '').strip()
    # Cache first
    cached = _cache_get(safe_word)
    if cached:
        return cached

    api_key = (
        getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '') or os.environ.get('GOOGLE_API_KEY', '')
    )
    if not api_key or not safe_word:
        # Heuristic fallback
        out = f"A definition describing '{safe_word}' in everyday English."
        _cache_set(safe_word, out)
        return out

    candidates = [
        getattr(settings, 'GEMINI_TEXT_MODEL', None) or os.environ.get('GEMINI_MODEL') or 'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
    ]
    prompt = (
        "You are an English tutor writing a playful single-line clue for a TARGET word.\n"
        "Use styles like: situational, personification, exaggeration/humor, or action/sound.\n"
        "Rules:\n"
        "- Exactly one sentence, 12–24 words.\n"
        "- Do NOT include or hint the word itself.\n"
        "- No quotes, no markdown, no lists, no colons.\n"
        f"TARGET: {safe_word}"
    )
    try:
        genai.configure(api_key=api_key)
    except Exception:
        return "A playful, single-line clue in plain English."
    for name in candidates:
        try:
            model = genai.GenerativeModel(name)
            resp = model.generate_content(prompt)
            txt = getattr(resp, 'text', None)
            if txt:
                out = txt.strip()
                # Guard: avoid echoing the word
                if safe_word.lower() in out.lower():
                    # try to mask
                    out = out.replace(safe_word, '▢▢▢')
                # Trim to a single sentence and length
                out = out.split('\n')[0].strip()
                _cache_set(safe_word, out)
                return out
        except Exception as e:
            logger.warning('Gemini definition via %s failed: %s', name, e)
            continue
    out = "A short learner-friendly definition."
    _cache_set(safe_word, out)
    return out


def _get_gemini_definitions_batch(words: list[str]) -> dict:
    """Generate concise definitions for a list of words in a single Gemini call.

    Returns a mapping {word: definition}. Falls back to empty dict on failure.
    """
    words = [w for w in (words or []) if isinstance(w, str) and w.strip()]
    if not words:
        return {}
    api_key = (
        getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '') or os.environ.get('GOOGLE_API_KEY', '')
    )
    if not api_key:
        # Fallback: no API key
        d = {w: f"A playful clue about '{w}' in plain English." for w in words}
        for w, v in d.items():
            _cache_set(w, v)
        return d

    # Prefer fast model first
    candidates = [
        getattr(settings, 'GEMINI_TEXT_MODEL', None) or os.environ.get('GEMINI_MODEL') or 'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
    ]
    # Build a strict JSON-only instruction for fun clues
    prompt = (
        "You are an English tutor. For each TARGET word, return a JSON object mapping the word\n"
        "to exactly one playful clue sentence.\n"
        "Styles: situational/roleplay, personification, exaggeration/humor, action/sound.\n"
        "Rules: one sentence only; 12–24 words; avoid the word itself; no quotes; no markdown.\n"
        "Output JSON only, keys must be the input words, values are the clue sentences.\n"
        "WORDS: " + json.dumps(words, ensure_ascii=False)
    )
    try:
        genai.configure(api_key=api_key)
    except Exception:
        d = {w: "A playful, single-line clue in plain English." for w in words}
        for w, v in d.items():
            _cache_set(w, v)
        return d

    for name in candidates:
        try:
            model = genai.GenerativeModel(name)
            resp = model.generate_content(prompt)
            txt = getattr(resp, 'text', None)
            if not txt:
                continue
            # Try to locate JSON in the response
            raw = txt.strip()
            # If the model adds markdown fences, strip them robustly
            if raw.startswith('```'):
                # remove opening fence and optional language hint
                first_nl = raw.find('\n')
                if first_nl != -1:
                    raw = raw[first_nl + 1:]
                # remove closing fence if present
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()
            # Attempt to parse JSON
            try:
                data = json.loads(raw)
                out = {}
                for w in words:
                    val = str(data.get(w, '')).strip()
                    if not val:
                        continue
                    # avoid echoing word
                    if w.lower() in val.lower():
                        val = val.replace(w, '▢▢▢')
                    # strip wrapping quotes if present
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1].strip()
                    # single line
                    val = val.split('\n')[0].strip()
                    out[w] = val
                if out:
                    for ww, dd in out.items():
                        _cache_set(ww, dd)
                    return out
            except Exception as e:
                logger.warning('Gemini batch JSON parse failed: %s', e)
                continue
        except Exception as e:
            logger.warning('Gemini batch via %s failed: %s', name, e)
            continue
    return {}

def _sample_vocabulary_questions(topic: Topic, n: int) -> list[dict]:
    """Build n questions from topic.vocabulary with AI definitions and 3 distractors each.
    Returns a list of dict questions with id, word, definition, options, answered, correct.
    """
    words = list((topic.vocabulary or [])[:])
    words = [w for w in words if isinstance(w, str) and w.strip()]
    if not words:
        return []
    import random
    random.shuffle(words)
    pick = words[: max(1, min(n, len(words)))]
    remaining_pool = [w for w in words if w not in pick]
    # Try to fetch definitions in a single batch to reduce latency
    # Resolve from cache first to minimize API calls
    cached_defs = {w: (_cache_get(w) or '') for w in pick}
    missing = [w for w in pick if not cached_defs.get(w)]
    defs_map = {}
    if missing:
        defs_map = _get_gemini_definitions_batch(missing)
    # merge cached + fetched
    defs_map = {**{w: v for w, v in cached_defs.items() if v}, **defs_map}
    qs: list[dict] = []
    for w in pick:
        # Build distractors from other words in topic (fallback duplicates if insufficient)
        pool = [x for x in words if x != w]
        random.shuffle(pool)
        distractors = pool[:3]
        while len(distractors) < 3:
            distractors.append(random.choice(words))
        options = distractors + [w]
        random.shuffle(options)
        definition = defs_map.get(w) or _get_gemini_definition(w)
        q = {
            'id': str(uuid.uuid4()),
            'word': w,
            'definition': definition,
            'options': options,
            'answered': False,
            'correct': None,
        }
        qs.append(q)
    return qs


def _transcribe_audio_with_whisper(audio_file):
    """Transcribe audio using OpenAI Whisper tiny.en model"""
    try:
        # Load Whisper model (tiny.en for faster processing on your MX350)
        model = whisper.load_model("tiny.en")

        # Create temporary file for audio processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            # Write uploaded audio to temporary file
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            # Transcribe audio
            result = model.transcribe(temp_file_path)
            transcription = result.get("text", "").strip()
            return transcription
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return ""


def _transcribe_audio_with_speechbrain(audio_file):
    """Transcribe audio using SpeechBrain ASR (if available). Returns empty string on failure.

    This function makes a temporary copy of the uploaded file, converts it to 16kHz mono WAV via ffmpeg,
    then performs ASR with a pre-trained SpeechBrain model.
    """
    # On Windows, SpeechBrain's fetching uses symlinks which require special privileges.
    # To avoid frequent failures like WinError 1314 (no symlink privilege), skip by default on Windows.
    # You can override by setting ENABLE_SPEECHBRAIN=1 in the environment.
    if os.name == 'nt' and not os.environ.get('ENABLE_SPEECHBRAIN'):
        logger.info('Skipping SpeechBrain ASR on Windows (set ENABLE_SPEECHBRAIN=1 to force enable).')
        return ""
    try:
        # Try to reset pointer in case it was read before
        if hasattr(audio_file, 'seek'):
            try:
                audio_file.seek(0)
            except Exception:
                pass

        # Persist chunks to a temp file using original extension when available
        try:
            orig_name = getattr(audio_file, 'name', '')
            ext = os.path.splitext(orig_name)[1] or '.m4a'
        except Exception:
            ext = '.m4a'

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as src:
            for chunk in audio_file.chunks():
                src.write(chunk)
            src_path = src.name

        # Convert to 16kHz mono WAV for ASR consumption
        conv_path = src_path + '.wav'
        try:
            subprocess.run(
                ['ffmpeg', '-y', '-i', src_path, '-ac', '1', '-ar', '16000', conv_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except Exception as e:
            logger.error('ffmpeg conversion failed for SpeechBrain ASR: %s', e)
            return ""

        # Lazy-load SpeechBrain ASR
        try:
            from speechbrain.pretrained import EncoderDecoderASR
        except Exception as e:
            logger.warning('SpeechBrain not installed or failed to import: %s', e)
            return ""

        try:
            if not hasattr(_transcribe_audio_with_speechbrain, '_asr_model'):
                _transcribe_audio_with_speechbrain._asr_model = EncoderDecoderASR.from_hparams(
                    source="speechbrain/asr-crdnn-rnnlm-librispeech",
                    run_opts={"device": "cpu"}
                )
            model = _transcribe_audio_with_speechbrain._asr_model
            text = model.transcribe_file(conv_path)
            return (text or "").strip()
        except Exception as e:
            msg = str(e)
            if 'WinError 1314' in msg or 'privilege' in msg.lower():
                logger.warning('SpeechBrain ASR skipped due to Windows symlink privilege error: %s', e)
            else:
                logger.error('SpeechBrain ASR transcription failed: %s', e)
            return ""
        finally:
            # Cleanup temp files
            try:
                if os.path.exists(conv_path):
                    os.unlink(conv_path)
            except Exception:
                pass
            try:
                if os.path.exists(src_path):
                    os.unlink(src_path)
            except Exception:
                pass
    except Exception as e:
        logger.error('SpeechBrain transcription error: %s', e)
        return ""


class SpeakingTopicsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        topics, completed_sequences, unlocked_sequences = _compute_unlocks(request.user)

        # Get or create user profile for welcome screen personalization
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'first_visit': True}
        )

        # Fetch all phrase progress for this user
        phrase_progress_dict = {}
        for topic in topics:
            phrase_progress, _ = PhraseProgress.objects.get_or_create(
                user=request.user,
                topic=topic,
                defaults={'current_phrase_index': 0, 'completed_phrases': []}
            )
            phrase_progress_dict[topic.id] = phrase_progress

        payload = []
        for t in topics:
            # Get phrase progress for this topic
            phrase_prog = phrase_progress_dict.get(t.id)
            phrase_progress_data = None
            if phrase_prog:
                phrase_progress_data = {
                    'currentPhraseIndex': phrase_prog.current_phrase_index,
                    'completedPhrases': phrase_prog.completed_phrases or [],
                    'totalPhrases': len(t.material_lines or []),
                    'isAllPhrasesCompleted': phrase_prog.is_all_phrases_completed,
                }

            # Build fluency progress view
            fprompts = t.fluency_practice_prompt or []
            tp, _ = TopicProgress.objects.get_or_create(user=request.user, topic=t)
            stored_scores = list(tp.fluency_prompt_scores or [])
            # Normalize to list of ints for existing entries
            prompt_scores = []
            for i in range(min(len(stored_scores), len(fprompts))):
                try:
                    val = int(stored_scores[i])
                    prompt_scores.append(val)
                except Exception:
                    # skip invalid entry
                    prompt_scores.append(None)
            # Determine next prompt index to unlock
            next_prompt_index = None
            for i in range(len(fprompts)):
                if i >= len(prompt_scores) or prompt_scores[i] is None:
                    next_prompt_index = i
                    break
            fluency_completed = (len(fprompts) > 0) and (next_prompt_index is None)
            fluency_total_score = int(tp.fluency_total_score or 0)

            payload.append({
                'id': str(t.id),
                'title': t.title,
                'description': t.description or "",
                'material': t.material_lines or [],
                'vocabulary': t.vocabulary or [],
                'conversation': t.conversation_example or [],
                'fluencyPracticePrompts': t.fluency_practice_prompt or [],
                'fluencyProgress': {
                    'promptsCount': len(fprompts),
                    'promptScores': [int(s) for s in prompt_scores if s is not None],
                    'totalScore': fluency_total_score,
                    'nextPromptIndex': next_prompt_index,
                    'completed': fluency_completed,
                },
                'phraseProgress': phrase_progress_data,
                'unlocked': t.sequence in unlocked_sequences,
                'completed': t.sequence in completed_sequences,
            })

        # Build user profile data
        user_profile_data = {
            'firstVisit': profile.first_visit,
            'lastVisitedTopicId': str(profile.last_visited_topic.id) if profile.last_visited_topic else None,
            'lastVisitedTopicTitle': profile.last_visited_topic.title if profile.last_visited_topic else "",
        }

        # Mark as not first visit after this request
        if profile.first_visit:
            profile.first_visit = False
            profile.save(update_fields=['first_visit'])

        response_data = {
            'topics': payload,
            'userProfile': user_profile_data
        }
        serializer = SpeakingTopicsResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Update last visited topic for welcome screen personalization"""
        topic_id = request.data.get('lastVisitedTopicId')
        if not topic_id:
            return Response({'detail': 'Missing lastVisitedTopicId'}, status=status.HTTP_400_BAD_REQUEST)

        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'first_visit': False}
        )
        profile.last_visited_topic = topic
        profile.save(update_fields=['last_visited_topic'])

        return Response({'success': True}, status=status.HTTP_200_OK)


class SubmitPhraseRecordingView(APIView):
    """Submit phrase recording for transcription and accuracy evaluation"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, topic_id):
        # Get topic and validate access
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)

        # Get required parameters
        phrase_index = request.data.get('phraseIndex')
        audio_file = request.data.get('audio')

        if phrase_index is None:
            return Response({'detail': 'Missing phraseIndex'}, status=status.HTTP_400_BAD_REQUEST)

        if not audio_file:
            return Response({'detail': 'Missing audio file'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phrase_index = int(phrase_index)
        except (ValueError, TypeError):
            return Response({'detail': 'Invalid phraseIndex'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate phrase index
        material_lines = topic.material_lines or []
        if phrase_index < 0 or phrase_index >= len(material_lines):
            return Response({'detail': 'Invalid phraseIndex for this topic'}, status=status.HTTP_400_BAD_REQUEST)

        expected_phrase = material_lines[phrase_index]

        # Get or create phrase progress
        phrase_progress, _ = PhraseProgress.objects.get_or_create(
            user=request.user,
            topic=topic,
            defaults={'current_phrase_index': 0, 'completed_phrases': []}
        )

        # Transcribe with Whisper (existing) and SpeechBrain (optional)
        whisper_transcription = _transcribe_audio_with_whisper(audio_file)
        # Reset pointer for a second read before SpeechBrain
        if hasattr(audio_file, 'seek'):
            try:
                audio_file.seek(0)
            except Exception:
                pass
        sb_transcription = _transcribe_audio_with_speechbrain(audio_file)

        # If both failed, return a graceful message
        if not whisper_transcription and not sb_transcription:
            return Response({
                'success': False,
                'accuracy': 0.0,
                'transcription': '',
                'feedback': 'Could not process audio. Please try recording again.',
            }, status=status.HTTP_200_OK)

        # Compute accuracies for available transcripts
        scores = []
        whisper_accuracy = None
        if whisper_transcription:
            whisper_accuracy = _calculate_similarity(expected_phrase, whisper_transcription)
            scores.append(whisper_accuracy)
        sb_accuracy = None
        if sb_transcription:
            sb_accuracy = _calculate_similarity(expected_phrase, sb_transcription)
            scores.append(sb_accuracy)

        # Combine scores (average) and choose best transcription for feedback
        combined_accuracy = sum(scores) / len(scores) if scores else 0.0
        best_transcription = whisper_transcription if (whisper_accuracy or 0.0) >= (sb_accuracy or 0.0) else sb_transcription

        # New rule: Any accuracy passes and auto-unlocks the next phrase
        passed = True
        next_phrase_index = None
        topic_completed = False
        xp_awarded = 0

        # Award XP only for good performance to preserve gamification balance
        if combined_accuracy >= 80.0:
            xp_to_award = 50
            user_level, _ = UserLevel.objects.get_or_create(user=request.user)
            user_level.experience_points += xp_to_award
            user_level.total_points_earned += xp_to_award
            user_level.save()
            try:
                PointsTransaction.objects.create(
                    user=request.user,
                    amount=xp_to_award,
                    source='pronunciation',
                    context={
                        'topicId': str(topic.id),
                        'phraseIndex': phrase_index,
                        'accuracy': round(combined_accuracy, 1),
                    }
                )
            except Exception:
                # Non-fatal if logging fails
                pass
            xp_awarded = xp_to_award

        # Mark phrase as completed and advance regardless of accuracy
        phrase_progress.mark_phrase_completed(phrase_index)
        next_phrase_index = phrase_progress.current_phrase_index

        # Check if all phrases completed
        if phrase_progress.is_all_phrases_completed:
            # Mark pronunciation mode complete and, for testing, auto-complete other modes
            topic_progress, _ = TopicProgress.objects.get_or_create(
                user=request.user,
                topic=topic
            )
            # Pronunciation mode done because all phrases are completed
            topic_progress.pronunciation_completed = True
            # TESTING TEMP: Only auto-mark modes that are not yet implemented (listening, grammar)
            # Fluency and Vocabulary now have dedicated practice flows.
            topic_progress.listening_completed = True
            topic_progress.grammar_completed = True

            # Compute per-topic total score as the sum of latest accuracies per phrase
            try:
                qs = UserPhraseRecording.objects.filter(user=request.user, topic=topic).order_by('phrase_index', '-created_at')
                latest_by_phrase = {}
                for r in qs:
                    if r.phrase_index not in latest_by_phrase:
                        latest_by_phrase[r.phrase_index] = r
                total_score = 0
                for r in latest_by_phrase.values():
                    try:
                        total_score += int(round(float(r.accuracy or 0.0)))
                    except Exception:
                        total_score += 0
                # Persist on TopicProgress
                if hasattr(topic_progress, 'pronunciation_total_score'):
                    topic_progress.pronunciation_total_score = total_score
            except Exception as e:
                logger.warning('Failed to compute total pronunciation score: %s', e)

            # Complete the topic only if all modes are completed
            if not topic_progress.completed and topic_progress.all_modes_completed:
                topic_progress.completed = True
                topic_progress.completed_at = timezone.now()
            topic_progress.save()
            topic_completed = topic_progress.completed

        # Get feedback from Gemini based on the best transcription and combined accuracy
        feedback = _get_gemini_feedback(expected_phrase, best_transcription, combined_accuracy)

        # Persist user recording with audio and metadata
        recording_id = None
        audio_url = ''
        try:
            # Reset file pointer if needed before saving
            if hasattr(audio_file, 'seek'):
                try:
                    audio_file.seek(0)
                except Exception:
                    pass

            upr = UserPhraseRecording(
                user=request.user,
                topic=topic,
                phrase_index=phrase_index,
                transcription=best_transcription,
                accuracy=round(combined_accuracy, 1),
                feedback=feedback,
            )
            # Save file to storage (uses upload_to path)
            try:
                filename = getattr(audio_file, 'name', 'recording.m4a')
                upr.audio_file.save(filename, audio_file, save=False)
            except Exception:
                # As a fallback, try reading content to a ContentFile
                try:
                    if hasattr(audio_file, 'seek'):
                        audio_file.seek(0)
                    content = audio_file.read()
                except Exception:
                    content = b''
                if content:
                    upr.audio_file.save('recording.m4a', ContentFile(content), save=False)
            upr.save()
            recording_id = str(upr.id)
            try:
                if upr.audio_file:
                    audio_url = request.build_absolute_uri(upr.audio_file.url)
            except Exception:
                audio_url = ''
        except Exception:
            # Do not fail the request if persistence fails; continue without recording info
            recording_id = None
            audio_url = ''

        # Build response
        result = {
            'success': passed,
            'accuracy': round(combined_accuracy, 1),
            'transcription': best_transcription,
            'feedback': feedback,
            'nextPhraseIndex': next_phrase_index,
            'topicCompleted': topic_completed,
            'xpAwarded': xp_awarded,
            'recordingId': recording_id,
            'audioUrl': audio_url,
        }

        serializer = PhraseSubmissionResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteTopicView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        progress, created = TopicProgress.objects.get_or_create(user=request.user, topic=topic)
        # Mark all modes completed when manually completing a topic (keeps behavior consistent during testing)
        progress.pronunciation_completed = True
        progress.fluency_completed = True
        progress.vocabulary_completed = True
        progress.listening_completed = True
        progress.grammar_completed = True
        message = 'Topic marked as completed'
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
        else:
            message = 'Topic already completed'
        progress.save()

        # Determine next topic to unlock
        next_topic = (
            Topic.objects.filter(is_active=True, sequence__gt=topic.sequence)
            .order_by('sequence')
            .first()
        )
        resp = {
            'success': True,
            'message': message,
            'completedTopicId': str(topic.id),
            'unlockedTopicId': str(next_topic.id) if next_topic else None,
        }
        serializer = CompleteTopicResponseSerializer(resp)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserPhraseRecordingsView(APIView):
    """List user's recordings for a topic, optionally filtered by phraseIndex"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        qs = UserPhraseRecording.objects.filter(user=request.user, topic=topic).order_by('-created_at')

        phrase_index = request.query_params.get('phraseIndex')
        if phrase_index is not None:
            try:
                idx = int(phrase_index)
                qs = qs.filter(phrase_index=idx)
            except (TypeError, ValueError):
                return Response({'detail': 'Invalid phraseIndex'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserPhraseRecordingSerializer(qs, many=True, context={'request': request})
        data = {'recordings': serializer.data}
        return Response(data, status=status.HTTP_200_OK)


class SubmitFluencyPromptView(APIView):
    """Submit a fluency prompt completion with a score, enforcing sequential unlocking.

    Request JSON body:
      { "promptIndex": 0, "score": 78, "sessionId": "optional" }
    Response JSON body:
      { "success": true, "nextPromptIndex": 1, "fluencyTotalScore": 78, "fluencyCompleted": false, "promptScores": [78] }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        prompts = topic.fluency_practice_prompt or []
        if not prompts:
            return Response({'detail': 'No fluency prompts configured for this topic'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate request body
        serializer = SubmitFluencyPromptRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        prompt_index: int = int(data.get('promptIndex'))
        score: int = int(data.get('score'))

        if prompt_index < 0 or prompt_index >= len(prompts):
            return Response({'detail': 'Invalid promptIndex'}, status=status.HTTP_400_BAD_REQUEST)

        # Load or init progress
        tp, _ = TopicProgress.objects.get_or_create(user=request.user, topic=topic)
        scores = list(tp.fluency_prompt_scores or [])

        # Determine next expected prompt index (sequential unlocking)
        completed_count = 0
        for i in range(len(prompts)):
            val = scores[i] if i < len(scores) else None
            if isinstance(val, int):
                completed_count += 1
            else:
                break
        next_expected = completed_count if completed_count < len(prompts) else None

        if next_expected is None:
            return Response({'detail': 'All prompts already completed'}, status=status.HTTP_400_BAD_REQUEST)
        if prompt_index != next_expected:
            return Response({'detail': 'Prompt is locked. Complete previous prompts first.'}, status=status.HTTP_400_BAD_REQUEST)

        # Persist new score at the prompt index (pad to required length)
        if len(scores) < len(prompts):
            scores.extend([None] * (len(prompts) - len(scores)))
        scores[prompt_index] = int(score)

        # Recompute totals and completion
        total = sum(int(s) for s in scores if isinstance(s, int))
        tp.fluency_prompt_scores = scores
        tp.fluency_total_score = int(total)
        tp.fluency_completed = all(isinstance(s, int) for s in scores[:len(prompts)])
        # If all modes completed, mark topic completed
        if tp.all_modes_completed and not tp.completed:
            tp.completed = True
            tp.completed_at = timezone.now()
        tp.save()

        # Compute next prompt index after update
        try:
            new_completed = 0
            for i in range(len(prompts)):
                if i < len(scores) and isinstance(scores[i], int):
                    new_completed += 1
                else:
                    break
            new_next = new_completed if new_completed < len(prompts) else None
        except Exception:
            new_next = None

        # XP awarding logic
        xp_awarded = 0
        try:
            # +50 for this prompt if score >= 80
            if score >= 80:
                xp_awarded += 50
                user_level, _ = UserLevel.objects.get_or_create(user=request.user)
                user_level.experience_points += 50
                user_level.total_points_earned += 50
                user_level.save()
                try:
                    PointsTransaction.objects.create(
                        user=request.user,
                        amount=50,
                        source='fluency',
                        context={
                            'topicId': str(topic.id),
                            'promptIndex': prompt_index,
                            'score': score,
                            'type': 'prompt'
                        }
                    )
                except Exception:
                    pass

            # Bonus +100 if all prompts are now completed
            if new_next is None:
                user_level, _ = UserLevel.objects.get_or_create(user=request.user)
                user_level.experience_points += 100
                user_level.total_points_earned += 100
                user_level.save()
                xp_awarded += 100
                try:
                    PointsTransaction.objects.create(
                        user=request.user,
                        amount=100,
                        source='fluency',
                        context={
                            'topicId': str(topic.id),
                            'bonus': 'complete_all_prompts',
                            'promptScores': [int(s) for s in scores if isinstance(s, int)]
                        }
                    )
                except Exception:
                    pass
        except Exception:
            # XP failures are non-fatal
            pass

        resp = {
            'success': True,
            'nextPromptIndex': new_next,
            'fluencyTotalScore': tp.fluency_total_score,
            'fluencyCompleted': tp.fluency_completed,
            'promptScores': [int(s) for s in scores if isinstance(s, int)],
            'xpAwarded': xp_awarded,
        }
        out = SubmitFluencyPromptResponseSerializer(resp)
        return Response(out.data, status=status.HTTP_200_OK)


class GenerateTTSView(APIView):
    """Generate TTS audio via Gemini and return a temporary WAV URL.

    Request JSON body:
      { "text": "Hello world", "voiceName": "Kore" }
    Response JSON body:
      { "audioUrl": "https://.../media/speaking_journey/tts/<id>.wav", "sampleRate": 24000, "voiceName": "Kore" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text')
        voice_name = request.data.get('voiceName') or 'Kore'

        if not text or not isinstance(text, str) or not text.strip():
            return Response({'detail': 'Missing or invalid "text"'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Deterministic cache key and path
            sample_rate = 24000
            model_name = 'gemini-2.5-flash-preview-tts'
            text_norm = ' '.join(text.split())
            key_str = f"{model_name}|voice={voice_name}|rate={sample_rate}|text={text_norm}"
            cache_hash = hashlib.sha256(key_str.encode('utf-8')).hexdigest()
            relative_path = f"speaking_journey/tts/{cache_hash[:2]}/{cache_hash}.wav"

            # If file already exists, return it immediately (no external API call)
            if default_storage.exists(relative_path):
                try:
                    file_url = request.build_absolute_uri(default_storage.url(relative_path))
                except Exception:
                    base_url = request.build_absolute_uri(getattr(settings, 'MEDIA_URL', '/media/'))
                    file_url = base_url.rstrip('/') + '/' + relative_path.lstrip('/')
                return Response(
                    {
                        'audioUrl': file_url,
                        'sampleRate': sample_rate,
                        'voiceName': voice_name,
                        'cached': True,
                    },
                    status=status.HTTP_200_OK
                )

            api_key = (
                getattr(settings, 'GEMINI_API_KEY', '') or
                getattr(settings, 'GOOGLE_API_KEY', '') or
                os.environ.get('GEMINI_API_KEY', '') or
                os.environ.get('GOOGLE_API_KEY', '')
            )
            if not api_key:
                logger.error('Server misconfiguration: GEMINI_API_KEY/GOOGLE_API_KEY not set')
                return Response({'detail': 'Server misconfiguration: GEMINI_API_KEY/GOOGLE_API_KEY not set'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            url = (
                'https://generativelanguage.googleapis.com/v1beta/models/'
                'gemini-2.5-flash-preview-tts:generateContent'
            )

            payload = {
                'model': 'gemini-2.5-flash-preview-tts',
                'contents': [{
                    'parts': [{ 'text': text.strip() }]
                }],
                'generationConfig': {
                    'responseModalities': ['AUDIO'],
                    'speechConfig': {
                        'voiceConfig': {
                            'prebuiltVoiceConfig': { 'voiceName': voice_name }
                        }
                    }
                }
            }
            headers = {
                'x-goog-api-key': api_key,
                'Content-Type': 'application/json'
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code != 200:
                detail = resp.text
                logger.error('Gemini TTS request failed', extra={'status_code': resp.status_code, 'body': detail[:1000]})
                return Response(
                    {'detail': 'Gemini TTS request failed', 'status': resp.status_code, 'body': detail[:800]},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            data = resp.json()
            try:
                b64 = (
                    data['candidates'][0]['content']['parts'][0]['inlineData']['data']
                )
            except Exception:
                return Response(
                    {'detail': 'Unexpected response format from Gemini', 'response': data},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            # Decode PCM (s16le, 24kHz, mono) to WAV
            pcm_bytes = base64.b64decode(b64)
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_bytes)
            wav_bytes = buf.getvalue()

            # Persist to media storage under deterministic cache path for HTTP streaming via GET
            saved_path = default_storage.save(relative_path, ContentFile(wav_bytes))
            try:
                file_url = request.build_absolute_uri(default_storage.url(saved_path))
            except Exception:
                # Fallback to constructing from MEDIA_URL
                base_url = request.build_absolute_uri(getattr(settings, 'MEDIA_URL', '/media/'))
                file_url = base_url.rstrip('/') + '/' + saved_path.lstrip('/')

            return Response(
                {
                    'audioUrl': file_url,
                    'sampleRate': sample_rate,
                    'voiceName': voice_name,
                    'cached': False,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception('TTS generation failed')
            return Response({'detail': 'TTS generation failed', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StartVocabularyPracticeView(APIView):
    """Start a vocabulary practice session for a topic.

    Computes ~60% of topic vocabulary as questions.
    Response: { sessionId, totalQuestions, questions: [{id, definition, options}] }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        vocab = topic.vocabulary or []
        total = len([w for w in vocab if isinstance(w, str) and w.strip()])
        if total < 1:
            return Response({'detail': 'No vocabulary available for this topic'}, status=status.HTTP_400_BAD_REQUEST)
        # 60% rule
        import math
        q_count = max(1, int(round(0.6 * total)))

        # Create session and generate questions
        questions = _sample_vocabulary_questions(topic, q_count)
        session = VocabularyPracticeSession.objects.create(
            user=request.user,
            topic=topic,
            questions=questions,
            total_questions=len(questions),
            current_index=0,
            correct_count=0,
            total_score=0,
            completed=False,
        )

        payload = {
            'sessionId': str(session.session_id),
            'totalQuestions': session.total_questions,
            'questions': [
                {
                    'id': q.get('id'),
                    'definition': q.get('definition') or '',
                    'options': q.get('options') or [],
                }
                for q in session.questions
            ],
        }
        out = StartVocabularyPracticeResponseSerializer(payload)
        return Response(out.data, status=status.HTTP_200_OK)


class SubmitVocabularyAnswerView(APIView):
    """Submit an answer for a vocabulary question.

    Request: { sessionId, questionId, selected }
    Response: { correct, xpAwarded, nextIndex, completed, totalScore }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        ser = SubmitVocabularyAnswerRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        data = ser.validated_data
        session_id = data.get('sessionId')
        question_id = data.get('questionId')
        selected = (data.get('selected') or '').strip()

        session = get_object_or_404(VocabularyPracticeSession, session_id=session_id, user=request.user, topic=topic)
        if session.completed:
            # Already done
            next_idx = None
            return Response({'correct': False, 'xpAwarded': 0, 'nextIndex': next_idx, 'completed': True, 'totalScore': session.total_score}, status=status.HTTP_200_OK)

        # Find question
        questions = list(session.questions or [])
        idx = next((i for i, q in enumerate(questions) if str(q.get('id')) == str(question_id)), None)
        if idx is None:
            return Response({'detail': 'Invalid questionId'}, status=status.HTTP_400_BAD_REQUEST)
        q = questions[idx]
        if q.get('answered'):
            # Idempotent: do not double-award
            # Move to next unanswered index
            next_index = None
            for j, item in enumerate(questions):
                if not item.get('answered'):
                    next_index = j
                    break
            return Response({'correct': bool(q.get('correct')), 'xpAwarded': 0, 'nextIndex': next_index, 'completed': next_index is None, 'totalScore': session.total_score}, status=status.HTTP_200_OK)

        correct_word = q.get('word')
        is_correct = (selected == correct_word)

        # Update question state
        q['answered'] = True
        q['correct'] = bool(is_correct)
        questions[idx] = q

        xp_awarded = 0
        if is_correct:
            session.correct_count = int(session.correct_count or 0) + 1
            session.total_score = int(session.total_score or 0) + 10
            # Award +20 XP for correct answer
            try:
                user_level, _ = UserLevel.objects.get_or_create(user=request.user)
                user_level.experience_points += 20
                user_level.total_points_earned += 20
                user_level.save()
                PointsTransaction.objects.create(
                    user=request.user,
                    amount=20,
                    source='vocabulary',
                    context={'topicId': str(topic.id), 'questionId': str(question_id), 'type': 'answer'}
                )
                xp_awarded = 20
            except Exception:
                pass

        # Update session
        session.questions = questions
        # Move to next unanswered question index
        next_index = None
        for j, item in enumerate(questions):
            if not item.get('answered'):
                next_index = j
                break
        session.current_index = next_index if next_index is not None else len(questions)
        # Mark completed if no more
        session.completed = next_index is None
        session.save(update_fields=['questions', 'correct_count', 'total_score', 'current_index', 'completed', 'updated_at'])

        resp = {
            'correct': is_correct,
            'xpAwarded': xp_awarded,
            'nextIndex': next_index,
            'completed': session.completed,
            'totalScore': int(session.total_score or 0),
        }
        out = SubmitVocabularyAnswerResponseSerializer(resp)
        return Response(out.data, status=status.HTTP_200_OK)


class CompleteVocabularyPracticeView(APIView):
    """Complete the vocabulary session, persist topic progress and award completion XP.

    Request: { sessionId }
    Response: totals and XP, plus whether the topic is now completed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id):
        topic = get_object_or_404(Topic, id=topic_id, is_active=True)
        ser = CompleteVocabularyPracticeRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        session_id = ser.validated_data.get('sessionId')
        session = get_object_or_404(VocabularyPracticeSession, session_id=session_id, user=request.user, topic=topic)

        # If some questions unanswered, mark as completed but do not award bonus XP (still persist score)
        all_answered = all(bool(q.get('answered')) for q in (session.questions or [])) if session.questions else True
        xp_awarded = 0
        # Persist to TopicProgress
        tp, _ = TopicProgress.objects.get_or_create(user=request.user, topic=topic)
        tp.vocabulary_total_score = int(session.total_score or 0)
        tp.vocabulary_completed = True
        # Mark topic completed if all modes completed
        if not tp.completed and tp.all_modes_completed:
            tp.completed = True
            tp.completed_at = timezone.now()
        tp.save()

        # Award +150 XP for completion of this practice
        try:
            user_level, _ = UserLevel.objects.get_or_create(user=request.user)
            user_level.experience_points += 150
            user_level.total_points_earned += 150
            user_level.save()
            PointsTransaction.objects.create(
                user=request.user,
                amount=150,
                source='vocabulary',
                context={'topicId': str(topic.id), 'type': 'complete', 'allAnswered': all_answered}
            )
            xp_awarded += 150
        except Exception:
            pass

        session.completed = True
        session.save(update_fields=['completed', 'updated_at'])

        payload = {
            'success': True,
            'totalQuestions': int(session.total_questions or 0),
            'correctCount': int(session.correct_count or 0),
            'totalScore': int(session.total_score or 0),
            'xpAwarded': xp_awarded,
            'vocabularyTotalScore': int(tp.vocabulary_total_score or 0),
            'topicCompleted': bool(tp.completed),
        }
        out = CompleteVocabularyPracticeResponseSerializer(payload)
        return Response(out.data, status=status.HTTP_200_OK)
