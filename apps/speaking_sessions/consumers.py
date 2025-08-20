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
