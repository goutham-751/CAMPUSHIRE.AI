"""
Voice API routes — text-to-speech, speech-to-text (with confidence metrics),
and voice listing.
"""

import io
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from backend.auth import get_current_user, rate_limit
from backend.config import settings
from backend.models.schemas import (
    TTSRequest,
    STTResponse,
    VoicesResponse,
    ConfidenceMetrics,
    ErrorResponse,
)
from backend.services.voice_engine import (
    text_to_speech,
    speech_to_text,
    get_available_voices,
)
from backend.services.tone_analyzer import analyze_tone
from backend.utils.errors import client_error_detail

logger = logging.getLogger("campushire.voice")

router = APIRouter(prefix="/api/voice", tags=["Voice"])

_LLM_USER = rate_limit(20)


@router.post(
    "/tts",
    responses={
        200: {"content": {"audio/mpeg": {}, "audio/wav": {}}},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Text-to-speech",
    description="Convert text to speech. Returns an audio file in MP3 or WAV format.",
)
async def tts(body: TTSRequest, user=Depends(_LLM_USER)):
    try:
        audio_data = await text_to_speech(
            text=body.text,
            language=body.language,
            voice_id=body.voice_id,
            output_format=body.output_format,
        )

        media_type = "audio/mpeg" if body.output_format == "mp3" else "audio/wav"
        audio_data.seek(0)

        return StreamingResponse(
            audio_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="speech.{body.output_format}"'
            },
        )
    except Exception as e:
        logger.exception("TTS failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Text-to-speech failed."),
        )


@router.post(
    "/stt",
    response_model=STTResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Speech-to-text with confidence analysis",
    description=(
        "Upload an audio file (WAV, MP3, WebM, etc.) and get the text transcription "
        "along with real-time confidence metrics (WPM, filler words, pause ratio)."
    ),
)
async def stt(
    file: UploadFile = File(...),
    language: str = Form(default="en-US", max_length=16),
    user=Depends(_LLM_USER),
):
    try:
        max_bytes = settings.MAX_AUDIO_UPLOAD_MB * 1024 * 1024
        chunks = []
        size = 0
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Audio exceeds {settings.MAX_AUDIO_UPLOAD_MB} MB limit.",
                )
            chunks.append(chunk)

        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio is empty.",
            )

        content = b"".join(chunks)
        audio_data = io.BytesIO(content)
        result = await speech_to_text(audio_data, language)

        if not result.get("success"):
            return STTResponse(
                success=False,
                language=language,
                error=result.get("error", "Transcription failed"),
            )

        transcript = result.get("text", "")

        audio_format = "webm"
        filename = (file.filename or "").lower()
        if filename.endswith(".wav"):
            audio_format = "wav"
        elif filename.endswith(".mp3"):
            audio_format = "mp3"
        elif filename.endswith(".ogg"):
            audio_format = "ogg"

        tone_result = analyze_tone(content, transcript, audio_format)

        confidence_metrics = None
        if tone_result.get("success"):
            confidence_metrics = ConfidenceMetrics(**tone_result)

        return STTResponse(
            success=True,
            text=transcript,
            language=result.get("language", language),
            confidence=result.get("confidence", 0.0),
            confidence_metrics=confidence_metrics,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("STT failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Speech-to-text failed."),
        )


@router.get(
    "/voices",
    response_model=VoicesResponse,
    summary="List available TTS voices",
    description="Returns all available text-to-speech voices grouped by language.",
)
async def list_voices(_user=Depends(get_current_user)):
    voices = await get_available_voices()
    return VoicesResponse(voices=voices)
