"""
AI Evaluation app configuration
"""
from django.apps import AppConfig
import os
import threading
import time
import logging
import tempfile
import wave
import struct



class AiEvaluationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_evaluation'
    verbose_name = 'AI Evaluation'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed for AI evaluation events
        logger = logging.getLogger(__name__)

        # Allow disabling warmup explicitly
        if str(os.environ.get('DISABLE_ASR_WARMUP', '')).strip().lower() in {"1", "true", "yes"}:
            logger.info("ASR warmup disabled by DISABLE_ASR_WARMUP env var")
            return

        def _create_silence_wav(duration_s: float = 0.2, sr: int = 16000) -> str:
            """Create a small temporary silent WAV and return its path."""
            # 16-bit PCM mono
            n_samples = int(sr * duration_s)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                with wave.open(tmp, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sr)
                    silence = struct.pack('<' + 'h' * n_samples, *([0] * n_samples))
                    wf.writeframes(silence)
                return tmp.name

        def _warm_asr_models():
            sample_path = None
            try:
                # Small delay to let the app finish booting and health checks pass quickly
                time.sleep(2.0)

                # Ensure CT2 uses CPU by default on typical hosts
                os.environ.setdefault("CT2_FORCE_CPU", "1")

                # Prepare a tiny sample file for a one-shot warm transcription
                sample_path = _create_silence_wav()

                # 1) Warm faster-whisper (ctranslate2)
                try:
                    from faster_whisper import WhisperModel as FWModel  # type: ignore
                    model_size = os.environ.get("WHISPER_MODEL_SIZE", "tiny.en")
                    fw_model = FWModel(model_size, device="cpu", compute_type="int8")
                    try:
                        # One-shot decode to prime kernels
                        fw_model.transcribe(sample_path, language="en", beam_size=1, best_of=1, vad_filter=False)
                    except Exception:
                        # Even if the first decode fails, the weights are still loaded
                        pass

                    # Share with services.WhisperService via class attribute
                    try:
                        from .services import WhisperService
                        WhisperService._fw_model = fw_model  # type: ignore[attr-defined]
                    except Exception:
                        logger.debug("Could not attach fw_model to WhisperService class; will lazy-load per request")

                    # Also share with speaking_journey helper if present
                    try:
                        from apps.speaking_journey import views as sj_views
                        setattr(sj_views._transcribe_audio_with_faster_whisper, '_model', fw_model)
                    except Exception:
                        logger.debug("Could not attach fw_model to speaking_journey view helper")

                    logger.info("faster-whisper model preloaded for warm start (%s)", model_size)
                except Exception as e:
                    logger.warning("ASR warmup: faster-whisper preload failed: %s", e)

                # 2) Warm openai-whisper unless explicitly disabled
                if str(os.environ.get('DISABLE_WHISPER', '')).strip().lower() not in {"1", "true", "yes"}:
                    try:
                        import whisper as openai_whisper  # type: ignore
                        ow_model = openai_whisper.load_model("tiny.en")
                        try:
                            ow_model.transcribe(sample_path, language="en")
                        except Exception:
                            pass

                        # Share with WhisperService class and speaking_journey helper
                        try:
                            from .services import WhisperService
                            WhisperService._model = ow_model  # type: ignore[attr-defined]
                        except Exception:
                            logger.debug("Could not attach whisper model to WhisperService class")
                        try:
                            from apps.speaking_journey import views as sj_views
                            setattr(sj_views._transcribe_audio_with_whisper, '_model', ow_model)
                        except Exception:
                            logger.debug("Could not attach whisper model to speaking_journey view helper")

                        logger.info("openai-whisper model preloaded for warm start (tiny.en)")
                    except Exception as e:
                        logger.warning("ASR warmup: openai-whisper preload failed: %s", e)

            except Exception as e:
                logger.warning("ASR warmup encountered an error: %s", e)
            finally:
                try:
                    if sample_path and os.path.exists(sample_path):
                        os.unlink(sample_path)
                except Exception:
                    pass

        # Launch background warmup without blocking the Django startup
        try:
            threading.Thread(target=_warm_asr_models, daemon=True).start()
        except Exception as e:
            logger.debug("Failed to start ASR warmup thread: %s", e)
