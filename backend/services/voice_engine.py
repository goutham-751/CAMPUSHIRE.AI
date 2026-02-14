import os
import io
import tempfile
import asyncio
from typing import Optional, Dict, Any, BinaryIO, Tuple
import wave
import numpy as np
from pydub import AudioSegment
from pydub.playback import play
from gtts import gTTS
import speech_recognition as sr
from dotenv import load_dotenv
import edge_tts
import aiohttp
import json

load_dotenv()


class VoiceEngine:
    """Text-to-speech and speech-to-text engine using edge-tts and Google recognition."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True

        # Voice settings  (edge-tts expects strings for rate/pitch/volume)
        self.default_voice = "en-US-AriaNeural"
        self.voice_rate = "+0%"
        self.voice_pitch = "+0Hz"
        self.voice_volume = "+0%"

        # Audio settings
        self.sample_rate = 24000
        self.channels = 1
        self.sample_width = 2

    async def text_to_speech(
        self,
        text: str,
        language: str = "en",
        slow: bool = False,
        voice_id: Optional[str] = None,
        output_format: str = "mp3",
    ) -> BinaryIO:
        """Convert text to speech and return the audio data as a BytesIO object."""
        try:
            if voice_id is None:
                voice_id = self.default_voice

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as temp_file:
                temp_path = temp_file.name

            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=self.voice_rate,
                pitch=self.voice_pitch,
                volume=self.voice_volume,
            )

            await communicate.save(temp_path)

            with open(temp_path, "rb") as f:
                audio_data = io.BytesIO(f.read())

            os.unlink(temp_path)
            return audio_data

        except Exception as e:
            # Fallback to gTTS
            try:
                tts = gTTS(text=text, lang=language, slow=slow)
                audio_data = io.BytesIO()
                tts.write_to_fp(audio_data)
                audio_data.seek(0)
                return audio_data
            except Exception as e2:
                raise Exception(
                    f"TTS generation failed: {str(e)} (Fallback also failed: {str(e2)})"
                )

    async def speech_to_text(
        self,
        audio_data: BinaryIO,
        language: str = "en-US",
    ) -> Dict[str, Any]:
        """Convert speech to text using Google's speech recognition."""
        temp_path = None
        try:
            audio_segment = AudioSegment.from_file(audio_data)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                audio_segment.export(
                    temp_path,
                    format="wav",
                    parameters=["-ac", "1", "-ar", "16000"],
                )

            with sr.AudioFile(temp_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)

            try:
                text = self.recognizer.recognize_google(audio, language=language)
                return {
                    "success": True,
                    "text": text,
                    "language": language,
                    "confidence": 1.0,
                }
            except sr.UnknownValueError:
                return {
                    "success": False,
                    "error": "Could not understand audio",
                    "language": language,
                }
            except sr.RequestError as e:
                return {
                    "success": False,
                    "error": f"Could not request results; {str(e)}",
                    "language": language,
                }

        except Exception as e:
            return {"success": False, "error": str(e), "language": language}
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def get_available_voices(self) -> Dict[str, list]:
        """Get a list of available voices from edge-tts."""
        return {
            "English (US)": [
                "en-US-AriaNeural",
                "en-US-ChristopherNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
                "en-US-AmberNeural",
                "en-US-AnaNeural",
                "en-US-AshleyNeural",
                "en-US-BrandonNeural",
                "en-US-CoraNeural",
                "en-US-ElizabethNeural",
                "en-US-EricNeural",
                "en-US-JacobNeural",
                "en-US-JaneNeural",
                "en-US-JasonNeural",
                "en-US-MichelleNeural",
                "en-US-MonicaNeural",
                "en-US-NancyNeural",
                "en-US-RogerNeural",
                "en-US-SaraNeural",
                "en-US-SteffanNeural",
                "en-US-TonyNeural",
            ],
            "English (UK)": [
                "en-GB-LibbyNeural",
                "en-GB-MaisieNeural",
                "en-GB-RyanNeural",
                "en-GB-SoniaNeural",
                "en-GB-ThomasNeural",
            ],
            "Other Languages": [
                "es-ES-ElviraNeural",
                "fr-FR-DeniseNeural",
                "de-DE-KatjaNeural",
                "it-IT-ElsaNeural",
                "pt-BR-FranciscaNeural",
                "ja-JP-NanamiNeural",
                "ko-KR-SunHiNeural",
                "zh-CN-XiaoxiaoNeural",
                "hi-IN-SwaraNeural",
                "ru-RU-SvetlanaNeural",
                "ar-SA-ZariyahNeural",
            ],
        }

    async def play_audio(self, audio_data: BinaryIO) -> None:
        """Play audio data using pydub."""
        try:
            audio_data.seek(0)
            audio_segment = AudioSegment.from_file(audio_data)
            play(audio_segment)
        except Exception as e:
            raise Exception(f"Error playing audio: {str(e)}")

    async def text_to_speech_and_play(
        self,
        text: str,
        language: str = "en",
        voice_id: Optional[str] = None,
    ) -> None:
        """Convert text to speech and play it immediately."""
        audio_data = await self.text_to_speech(text, language, voice_id=voice_id)
        await self.play_audio(audio_data)


# -------------------------------------------------------------------
# Lazy singleton
# -------------------------------------------------------------------
_voice_engine: Optional[VoiceEngine] = None


def get_voice_engine() -> VoiceEngine:
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine()
    return _voice_engine


async def text_to_speech(
    text: str,
    language: str = "en",
    slow: bool = False,
    voice_id: Optional[str] = None,
    output_format: str = "mp3",
) -> BinaryIO:
    """Convert text to speech."""
    return await get_voice_engine().text_to_speech(text, language, slow, voice_id, output_format)


async def speech_to_text(
    audio_data: BinaryIO,
    language: str = "en-US",
) -> Dict[str, Any]:
    """Convert speech to text."""
    return await get_voice_engine().speech_to_text(audio_data, language)


async def get_available_voices() -> Dict[str, list]:
    """Get a list of available voices."""
    return get_voice_engine().get_available_voices()


async def play_audio(audio_data: BinaryIO) -> None:
    """Play audio data."""
    await get_voice_engine().play_audio(audio_data)


async def text_to_speech_and_play(
    text: str,
    language: str = "en",
    voice_id: Optional[str] = None,
) -> None:
    """Convert text to speech and play it immediately."""
    await get_voice_engine().text_to_speech_and_play(text, language, voice_id)