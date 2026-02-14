"""
Voice API routes — text-to-speech, speech-to-text, and voice listing.
"""

import io
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.models.schemas import (
    TTSRequest,
    STTResponse,
    VoicesResponse,
    ErrorResponse,
)
from backend.services.voice_engine import (
    text_to_speech,
    speech_to_text,
    get_available_voices,
)

router = APIRouter(prefix="/api/voice", tags=["Voice"])


# ── endpoints ───────────────────────────────────────────────────

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
async def tts(body: TTSRequest):
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/stt",
    response_model=STTResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Speech-to-text",
    description="Upload an audio file (WAV, MP3, etc.) and get the text transcription.",
)
async def stt(
    file: UploadFile = File(...),
    language: str = Form(default="en-US"),
):
    try:
        content = await file.read()
        audio_data = io.BytesIO(content)

        result = await speech_to_text(audio_data, language)

        if not result.get("success"):
            return STTResponse(
                success=False,
                language=language,
                error=result.get("error", "Transcription failed"),
            )

        return STTResponse(
            success=True,
            text=result.get("text"),
            language=result.get("language", language),
            confidence=result.get("confidence", 0.0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/voices",
    response_model=VoicesResponse,
    summary="List available TTS voices",
    description="Returns all available text-to-speech voices grouped by language.",
)
async def list_voices():
    voices = await get_available_voices()
    return VoicesResponse(voices=voices)
