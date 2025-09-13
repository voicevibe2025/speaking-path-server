"""
WebSocket consumers for real-time audio streaming
"""
import json
import asyncio
import base64
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import PracticeSession, AudioRecording, RealTimeTranscript
import logging
import os
import importlib.metadata as metadata

try:
    from google.genai.client import Client as GenAIClient
    from google.genai import types
except Exception:  # pragma: no cover - optional import in dev
    GenAIClient = None
    types = None

logger = logging.getLogger(__name__)
User = get_user_model()


class AudioStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time audio streaming and transcription
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = None
        self.user = None
        self.audio_buffer = bytearray()
        self.chunk_index = 0
        self.transcription_task = None

    async def connect(self):
        """
        Handle WebSocket connection
        """
        # Get user from scope (authenticated via middleware)
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return

        # Get session_id from URL route
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')

        # Verify session exists and belongs to user
        self.session = await self.get_session()
        if not self.session:
            await self.close(code=4004)  # Session not found
            return

        # Accept connection
        await self.accept()

        # Update session status
        await self.update_session_status('in_progress')

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'session_id': str(self.session.session_id),
            'user_id': self.user.id,
            'timestamp': datetime.now().isoformat()
        }))

        logger.info(f"WebSocket connected for session {self.session_id}, user {self.user.email}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Cancel any ongoing transcription task
        if self.transcription_task:
            self.transcription_task.cancel()

        # Process any remaining audio in buffer
        if self.audio_buffer:
            await self.process_audio_chunk(self.audio_buffer, is_final=True)

        # Update session status if still in progress
        if self.session and self.session.session_status == 'in_progress':
            await self.update_session_status('completed')

        logger.info(f"WebSocket disconnected for session {self.session_id}, code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages
        """
        try:
            if bytes_data:
                # Handle binary audio data
                await self.handle_audio_data(bytes_data)
            elif text_data:
                # Handle JSON control messages
                data = json.loads(text_data)
                message_type = data.get('type')

                if message_type == 'audio_chunk':
                    # Handle base64 encoded audio
                    audio_data = base64.b64decode(data.get('audio', ''))
                    await self.handle_audio_data(audio_data)

                elif message_type == 'end_stream':
                    # Process final audio and complete session
                    await self.handle_end_stream()

                elif message_type == 'get_feedback':
                    # Request immediate feedback
                    await self.send_intermediate_feedback()

        except json.JSONDecodeError as e:
            await self.send_error(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(f"Processing error: {str(e)}")

    async def handle_audio_data(self, audio_data):
        """
        Handle incoming audio data chunks
        """
        # Add to buffer
        self.audio_buffer.extend(audio_data)

        # Process chunk if buffer is large enough (e.g., 1 second of audio)
        # Assuming 16kHz sample rate, 16-bit audio = 32KB per second
        if len(self.audio_buffer) >= 32000:
            chunk_to_process = bytes(self.audio_buffer[:32000])
            self.audio_buffer = self.audio_buffer[32000:]

            # Process asynchronously
            if not self.transcription_task or self.transcription_task.done():
                self.transcription_task = asyncio.create_task(
                    self.process_audio_chunk(chunk_to_process)
                )

    async def process_audio_chunk(self, audio_chunk, is_final=False):
        """
        Process audio chunk - simplified version without external services
        """
        try:
            self.chunk_index += 1

            # Create real-time transcript entry (placeholder for actual transcription)
            transcript = await self.create_realtime_transcript(
                chunk_text="[Audio chunk processed]",
                confidence=0.95,
                is_final=is_final
            )

            # Send transcription to client
            await self.send(text_data=json.dumps({
                'type': 'transcription',
                'chunk_index': self.chunk_index,
                'text': transcript.chunk_text,
                'is_final': is_final,
                'confidence': transcript.confidence,
                'timestamp': datetime.now().isoformat()
            }))

        except Exception as e:
            logger.error(f"Error processing audio chunk: {str(e)}")
            await self.send_error(f"Transcription error: {str(e)}")

    async def handle_end_stream(self):
        """
        Handle end of audio stream
        """
        # Process remaining buffer
        if self.audio_buffer:
            await self.process_audio_chunk(self.audio_buffer, is_final=True)

        # Update session status
        await self.update_session_status('completed')

        # Send completion message
        await self.send(text_data=json.dumps({
            'type': 'stream_completed',
            'session_id': str(self.session.session_id),
            'timestamp': datetime.now().isoformat()
        }))

    async def send_intermediate_feedback(self):
        """
        Send intermediate feedback based on current transcripts
        """
        feedback = await self.generate_feedback()

        await self.send(text_data=json.dumps({
            'type': 'intermediate_feedback',
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }))

    async def send_error(self, error_message):
        """
        Send error message to client
        """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }))

    # Database operations
    @database_sync_to_async
    def get_session(self):
        """
        Get practice session from database
        """
        try:
            return PracticeSession.objects.get(
                session_id=self.session_id,
                user=self.user
            )
        except PracticeSession.DoesNotExist:
            return None

    @database_sync_to_async
    def update_session_status(self, status):
        """
        Update session status
        """
        if self.session:
            self.session.session_status = status
            if status == 'completed':
                self.session.completed_at = datetime.now()
            self.session.save()

    @database_sync_to_async
    def create_realtime_transcript(self, chunk_text, confidence, is_final):
        """
        Create real-time transcript entry
        """
        return RealTimeTranscript.objects.create(
            session=self.session,
            chunk_index=self.chunk_index,
            chunk_text=chunk_text,
            is_final=is_final,
            start_time=self.chunk_index * 1.0,  # Placeholder timing
            end_time=(self.chunk_index + 1) * 1.0,
            confidence=confidence
        )

    @database_sync_to_async
    def generate_feedback(self):
        """
        Generate feedback based on current transcripts
        """
        # Placeholder for feedback generation
        return {
            'pronunciation': 'Good pronunciation so far',
            'fluency': 'Maintaining good pace',
            'suggestions': ['Keep speaking clearly']
        }


class GeminiLiveProxyConsumer(AsyncWebsocketConsumer):
    """
    Proxy WebSocket for Gemini Live API (bidirectional low-latency voice).

    Client <-> Django (WebSocket) <-> Gemini Live (WebSocket via SDK)

    Client protocol:
      - Binary frames: 16kHz PCM16 mono audio chunks from mic.
      - Text frames (JSON): control messages, e.g. {"type": "end_stream"}

    Server protocol to client:
      - Binary frames: PCM16 audio generated by Gemini.
      - Text frames (JSON): {"type":"text","text":"..."}, {"type":"info"}, {"type":"error"}
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.gemini_client = None
        self.gemini_session = None
        self._gemini_cm = None
        self.recv_task = None
        self.closed = False
        self.active_model = None
        # Fallback mode for SDKs without realtime_input: buffer mic until end_turn
        self._use_buffered_content = False
        self._audio_buf = bytearray()

    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.practice_session = await self._get_session()
        if not self.practice_session:
            await self.close(code=4004)
            return

        # Configure Gemini client
        if GenAIClient is None:
            await self.close(code=4500)
            return
        # Prefer GOOGLE_API_KEY; google-genai reads env automatically
        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            await self.close(code=4501)
            return
        try:
            self.gemini_client = GenAIClient()

            model = os.environ.get("GEMINI_LIVE_MODEL", "gemini-2.5-flash-preview-native-audio-dialog")
            try:
                gn_version = metadata.version("google-genai")
            except Exception:
                gn_version = "unknown"
            # Select modalities by model: native-audio models should prefer AUDIO
            modalities = ["AUDIO"] if "native-audio" in model else ["TEXT"]

            # Build a sequence of connection attempts from most to least featured.
            attempts: list[tuple[str, dict]] = []

            # Attempt 1: primary config (include speech_config only if AUDIO)
            cfg1 = {
                "response_modalities": modalities,
                "system_instruction": {
                    "role": "system",
                    "parts": [{
                        "text": (
                            "You are Vivi, a friendly English tutor from Batam. "
                            "Be warm, natural, youthfully energetic, and concise. "
                            "Keep turns short to minimize latency."
                        )
                    }],
                },
            }
            if "AUDIO" in modalities:
                cfg1["speech_config"] = {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": os.environ.get("GEMINI_LIVE_VOICE", "Leda")
                        }
                    }
                }
            attempts.append((model, cfg1))

            # Attempt 2: same model, minimal config (only response_modalities)
            attempts.append((model, {"response_modalities": modalities}))

            # Attempt 3: fallback to text-only live model, minimal
            fallback_model = os.environ.get("GEMINI_LIVE_FALLBACK_MODEL", "gemini-live-2.5-flash-preview")
            attempts.append((fallback_model, {"response_modalities": ["TEXT"]}))

            last_error: Exception | None = None
            for idx, (mdl, cfg) in enumerate(attempts, start=1):
                try:
                    logger.info("live: connect attempt %d -> model=%s cfg_keys=%s", idx, mdl, list(cfg.keys()))
                    cm = self.gemini_client.aio.live.connect(model=mdl, config=cfg)
                    sess = await cm.__aenter__()
                    self._gemini_cm = cm
                    self.gemini_session = sess
                    model = mdl  # track active
                    logger.info(
                        "Gemini Live connected (model=%s, google-genai=%s, has_send_realtime_input=%s)",
                        mdl, gn_version, hasattr(sess, "send_realtime_input")
                    )
                    self.active_model = mdl
                    break
                except Exception as exc:
                    last_error = exc
                    logger.warning("live: connect attempt %d failed: %s", idx, exc)
                    continue

            if not self.gemini_session:
                raise RuntimeError(f"All Live connect attempts failed: {last_error}")

            self._use_buffered_content = not hasattr(self.gemini_session, "send_realtime_input")
            logger.info("live: path selected = %s", "buffered_content" if self._use_buffered_content else "realtime_input")
            # Reconnect to a TEXT-only Live model if we're on a native-audio model without realtime input
            if self._use_buffered_content and "native-audio" in model:
                logger.info("live: reconnecting to fallback TEXT model because runtime lacks realtime_input for native-audio")
                try:
                    await self._gemini_cm.__aexit__(None, None, None)
                except Exception:
                    pass
                fallback_model = os.environ.get("GEMINI_LIVE_FALLBACK_MODEL", "gemini-live-2.5-flash-preview")
                fallback_cfg = {"response_modalities": ["TEXT"], "system_instruction": {
                    "role": "system",
                    "parts": [{"text": (
                        "You are Vivi, a friendly English tutor from Batam. "
                        "Be warm, natural, youthfully energetic, and concise. "
                        "Keep turns short to minimize latency."
                    )}]}}
                cm2 = self.gemini_client.aio.live.connect(model=fallback_model, config=fallback_cfg)
                self.gemini_session = await cm2.__aenter__()
                self._gemini_cm = cm2
                model = fallback_model
                self.active_model = fallback_model
                logger.info("live: reconnected with fallback model=%s (TEXT only)", fallback_model)
        except Exception as e:
            logging.exception("Failed to connect to Gemini Live API")
            await self.close(code=4502)
            return

        await self.accept()
        await self._send_json({
            "type": "live_connected",
            "session_id": str(self.practice_session.session_id),
            "timestamp": datetime.now().isoformat(),
        })
        # Start forwarding Gemini -> client
        self.recv_task = asyncio.create_task(self._gemini_to_client_loop())

        # Start forwarding Gemini -> client

    async def disconnect(self, close_code):
        self.closed = True
        try:
            if getattr(self, "recv_task", None):
                self.recv_task.cancel()
                try:
                    await self.recv_task
                except Exception:
                    pass
            if self.gemini_session:
                await self.gemini_session.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            if getattr(self, "_gemini_cm", None):
                await self._gemini_cm.__aexit__(None, None, None)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if bytes_data:
                # Forward audio chunk to Gemini Live (or buffer when in fallback mode)
                if self._use_buffered_content:
                    self._audio_buf.extend(bytes_data)
                else:
                    await self._send_audio_to_gemini(bytes_data)
            elif text_data:
                data = json.loads(text_data)
                msg_type = data.get("type")
                if msg_type == "end_stream":
                    # Prefer ending the realtime audio stream explicitly if supported.
                    try:
                        if not self._use_buffered_content and hasattr(self.gemini_session, "send_realtime_input"):
                            logger.debug("live: end_stream via realtime_input(audio_stream_end=True)")
                            await self.gemini_session.send_realtime_input(audio_stream_end=True)
                        else:
                            # Buffered fallback: send aggregated audio as one turn
                            if self._audio_buf:
                                logger.info("live: flushing buffered audio (%d bytes) with end_of_turn=True", len(self._audio_buf))
                                sent = False
                                # Append ~300ms of silence to help VAD / end-of-turn on some backends
                                payload = bytes(self._audio_buf) + (b"\x00" * int(0.3 * 16000 * 2))
                                try:
                                    if hasattr(self.gemini_session, "send_client_content"):
                                        logger.debug("live: flush via send_client_content(turns=[Content(inline_data=Blob)], turn_complete=True)")
                                        await self.gemini_session.send_client_content(
                                            turns=[
                                                types.Content(
                                                    role="user",
                                                    parts=[
                                                        types.Part(
                                                            inline_data=types.Blob(data=payload, mime_type="audio/pcm;rate=16000")
                                                        )
                                                    ],
                                                )
                                            ],
                                            turn_complete=True,
                                        )
                                        sent = True
                                except Exception as e:
                                    logger.warning("live: send_client_content flush failed: %s", e)
                                    sent = False
                                if not sent:
                                    logger.debug("live: flush via LiveClientContent(inline_data=Blob), end_of_turn=True")
                                    await self.gemini_session.send(
                                        input=types.LiveClientContent(
                                            turns=[
                                                types.Content(
                                                    role="user",
                                                    parts=[
                                                        types.Part(
                                                            inline_data=types.Blob(data=payload, mime_type="audio/pcm;rate=16000")
                                                        )
                                                    ],
                                                )
                                            ]
                                        ),
                                        end_of_turn=True,
                                    )
                                self._audio_buf.clear()
                            else:
                                # No audio buffered; still mark end_of_turn
                                logger.debug("live: end_stream with empty buffer -> send minimal turn_complete")
                                await self.gemini_session.send(
                                    input=types.LiveClientContent(
                                        turns=[types.Content(role="user", parts=[])]
                                    ),
                                    end_of_turn=True,
                                )
                    except Exception:
                        pass
                elif msg_type == "barge_in":
                    # For now, end the current turn to simulate interruption.
                    try:
                        if not self._use_buffered_content and hasattr(self.gemini_session, "send_realtime_input"):
                            logger.debug("live: barge_in via realtime_input(audio_stream_end=True)")
                            await self.gemini_session.send_realtime_input(audio_stream_end=True)
                        else:
                            logger.debug("live: barge_in via send(LiveClientContent, end_of_turn=True)")
                            if self._audio_buf:
                                logger.info("live: barge_in flush buffered audio (%d bytes)", len(self._audio_buf))
                                sent = False
                                payload = bytes(self._audio_buf) + (b"\x00" * int(0.3 * 16000 * 2))
                                try:
                                    if hasattr(self.gemini_session, "send_client_content"):
                                        logger.debug("live: barge_in flush via send_client_content(turns=[Content(inline_data=Blob)], turn_complete=True)")
                                        await self.gemini_session.send_client_content(
                                            turns=[
                                                types.Content(
                                                    role="user",
                                                    parts=[
                                                        types.Part(
                                                            inline_data=types.Blob(data=payload, mime_type="audio/pcm;rate=16000")
                                                        )
                                                    ],
                                                )
                                            ],
                                            turn_complete=True,
                                        )
                                        sent = True
                                except Exception as e:
                                    logger.warning("live: send_client_content barge flush failed: %s", e)
                                    sent = False
                                if not sent:
                                    logger.debug("live: barge_in flush via LiveClientContent(inline_data=Blob), end_of_turn=True")
                                    await self.gemini_session.send(
                                        input=types.LiveClientContent(
                                            turns=[
                                                types.Content(
                                                    role="user",
                                                    parts=[
                                                        types.Part(
                                                            inline_data=types.Blob(data=payload, mime_type="audio/pcm;rate=16000")
                                                        )
                                                    ],
                                                )
                                            ]
                                        ),
                                        end_of_turn=True,
                                    )
                                self._audio_buf.clear()
                            else:
                                await self.gemini_session.send(
                                    input=types.LiveClientContent(
                                        turns=[types.Content(role="user", parts=[])]
                                    ),
                                    end_of_turn=True,
                                )
                    except Exception:
                        pass
                # Add more control messages as needed
        except Exception as e:
            await self._send_json({"type": "error", "message": f"{e}"})

    async def _send_audio_to_gemini(self, audio_bytes: bytes):
        try:
            if hasattr(self.gemini_session, "send_realtime_input"):
                # Preferred API (newer SDKs). Use the generic 'media' parameter for compatibility.
                logger.debug("live: send chunk via send_realtime_input(media=Blob[pcm16k])")
                await self.gemini_session.send_realtime_input(
                    media=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
                )
            else:
                # Fallbacks when realtime_input API isn't available
                sent = False
                if hasattr(types, "LiveClientRealtimeInput"):
                    try:
                        logger.debug("live: send chunk via send(LiveClientRealtimeInput(media=Blob))")
                        await self.gemini_session.send(
                            input=types.LiveClientRealtimeInput(
                                media=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
                            ),
                            end_of_turn=False,
                        )
                        sent = True
                    except Exception:
                        sent = False
                if not sent:
                    # Ultimate fallback: send minimal Content with inline_data bytes part
                    logger.debug("live: send chunk via send(LiveClientContent(turns=[Content(parts=[inline_data=Blob])]))")
                    await self.gemini_session.send(
                        input=types.LiveClientContent(
                            turns=[
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part(
                                            inline_data=types.Blob(
                                                data=audio_bytes,
                                                mime_type="audio/pcm;rate=16000",
                                            )
                                        )
                                    ],
                                )
                            ]
                        ),
                        end_of_turn=False,
                    )
        except Exception as e:
            # Avoid dumping large base64 payloads in error text
            msg = str(e)
            if len(msg) > 240:
                msg = msg[:240] + "…"
            await self._send_json({"type": "error", "message": f"upstream audio error: {msg}"})

    async def _gemini_to_client_loop(self):
        try:
            async for response in self.gemini_session.receive():
                # 1) Direct audio bytes (common on native audio models)
                try:
                    data = getattr(response, "data", None)
                    if data:
                        logger.debug("live: recv audio bytes=%d", len(data))
                        await self.send(bytes_data=data)
                        continue
                except Exception:
                    pass

                # 2) Older SDKs: response.audio.data
                try:
                    audio = getattr(response, "audio", None)
                    adata = getattr(audio, "data", None) if audio else None
                    if adata:
                        logger.debug("live: recv legacy audio bytes=%d", len(adata))
                        await self.send(bytes_data=adata)
                        continue
                except Exception:
                    pass

                # 3) Text convenience property
                try:
                    text = getattr(response, "text", None)
                    if text:
                        logger.debug("live: recv text len=%d", len(text))
                        await self._send_json({"type": "text", "text": text})
                        continue
                except Exception:
                    pass

                # 4) Server content structure: model_turn.parts[*]
                try:
                    sc = getattr(response, "server_content", None)
                    mt = getattr(sc, "model_turn", None) if sc else None
                    parts = getattr(mt, "parts", None) if mt else None
                    if parts:
                        aggregated_text = []
                        for p in parts:
                            # text part
                            ptext = getattr(p, "text", None)
                            if ptext:
                                aggregated_text.append(ptext)
                            # inline_data bytes (audio)
                            inline = getattr(p, "inline_data", None)
                            idata = getattr(inline, "data", None) if inline else None
                            if idata:
                                logger.debug("live: recv inline_data audio bytes=%d", len(idata))
                                await self.send(bytes_data=idata)
                        if aggregated_text:
                            out = "".join(aggregated_text)
                            await self._send_json({"type": "text", "text": out})
                            continue
                except Exception:
                    pass

                # 5) Fallback: forward event metadata if available
                try:
                    raw = getattr(response, "to_dict", None)
                    if callable(raw):
                        await self._send_json({"type": "info", "event": raw()})
                except Exception:
                    pass
        except asyncio.CancelledError:
            return
        except Exception as e:
            if not self.closed:
                await self._send_json({"type": "error", "message": f"upstream receive error: {e}"})

    async def _send_json(self, payload: dict):
        try:
            await self.send(text_data=json.dumps(payload))
        except Exception:
            pass

    # Database helper
    @database_sync_to_async
    def _get_session(self):
        try:
            return PracticeSession.objects.get(
                session_id=self.session_id,
                user=self.user,
            )
        except PracticeSession.DoesNotExist:
            return None
