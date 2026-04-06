"""
Real-Time Confidence & Tone Analyzer

Analyzes the user's spoken audio to produce speech quality metrics:
  • Words Per Minute (WPM)
  • Filler word frequency
  • Pause / silence ratio
  • Overall Confidence Score (weighted composite)

Uses pydub (already installed) for audio processing — no new dependencies.
"""

import io
import logging
import tempfile
import os
from typing import Dict, Any, List, Optional

from pydub import AudioSegment
from pydub.silence import detect_silence

logger = logging.getLogger("campushire.tone")

# Common filler words to detect in transcript
FILLER_WORDS = [
    "um", "uh", "uhh", "umm", "hmm", "hm",
    "like", "you know", "basically", "actually",
    "sort of", "kind of", "i mean", "right",
    "so yeah", "literally", "honestly",
]

# Ideal WPM range
IDEAL_WPM_LOW = 120
IDEAL_WPM_HIGH = 160


class ToneAnalyzer:
    """Analyzes speech audio and transcript for confidence metrics."""

    def analyze(
        self,
        audio_bytes: bytes,
        transcript: str,
        audio_format: str = "webm",
    ) -> Dict[str, Any]:
        """
        Analyze audio and transcript to produce confidence metrics.

        Args:
            audio_bytes: Raw audio data bytes
            transcript: The transcribed text from STT
            audio_format: Format of the audio (webm, wav, mp3, etc.)

        Returns:
            Dictionary of confidence metrics
        """
        try:
            # Load audio
            audio_io = io.BytesIO(audio_bytes)
            audio_segment = AudioSegment.from_file(audio_io, format=audio_format)

            # Duration in seconds
            duration_sec = len(audio_segment) / 1000.0
            if duration_sec < 1:
                return self._empty_metrics("Audio too short for analysis")

            # Compute individual metrics
            wpm, wpm_score = self._compute_wpm(transcript, duration_sec)
            filler_count, filler_details, filler_score = self._count_fillers(transcript)
            pause_ratio, pause_score = self._analyze_pauses(audio_segment, duration_sec)
            word_count = len(transcript.split()) if transcript else 0

            # Composite confidence score
            confidence_score = self._compute_confidence_score(
                wpm_score, filler_score, pause_score
            )

            # Generate tips
            tips = self._generate_tips(wpm, filler_count, pause_ratio)

            return {
                "success": True,
                "confidence_score": round(confidence_score, 1),
                "duration_seconds": round(duration_sec, 1),
                "word_count": word_count,
                "wpm": round(wpm, 1),
                "wpm_score": round(wpm_score, 1),
                "wpm_assessment": self._wpm_assessment(wpm),
                "filler_count": filler_count,
                "filler_words": filler_details,
                "filler_score": round(filler_score, 1),
                "pause_ratio": round(pause_ratio, 2),
                "pause_score": round(pause_score, 1),
                "tips": tips,
            }

        except Exception as e:
            logger.warning("Tone analysis failed: %s", e)
            return self._empty_metrics(str(e))

    def _compute_wpm(self, transcript: str, duration_sec: float) -> tuple:
        """Compute words per minute and WPM score."""
        words = len(transcript.split()) if transcript else 0
        if duration_sec < 1:
            return 0, 0

        wpm = (words / duration_sec) * 60

        # Score: 100 in ideal range, drops off outside
        if IDEAL_WPM_LOW <= wpm <= IDEAL_WPM_HIGH:
            score = 100
        elif wpm < IDEAL_WPM_LOW:
            score = max(0, 100 - (IDEAL_WPM_LOW - wpm) * 1.5)
        else:
            score = max(0, 100 - (wpm - IDEAL_WPM_HIGH) * 1.2)

        return wpm, score

    def _count_fillers(self, transcript: str) -> tuple:
        """Count filler words in transcript."""
        if not transcript:
            return 0, [], 100

        text_lower = transcript.lower()
        total_words = len(text_lower.split())
        details = []
        total_fillers = 0

        for filler in FILLER_WORDS:
            count = text_lower.count(filler)
            if count > 0:
                details.append({"word": filler, "count": count})
                total_fillers += count

        # Score: fewer fillers = higher score
        # Penalize at roughly 1 filler per 20 words as baseline
        if total_words == 0:
            filler_ratio = 0
        else:
            filler_ratio = total_fillers / total_words

        score = max(0, 100 - filler_ratio * 500)

        # Sort by count descending
        details.sort(key=lambda x: x["count"], reverse=True)

        return total_fillers, details[:5], score

    def _analyze_pauses(self, audio_segment: AudioSegment, duration_sec: float) -> tuple:
        """Analyze silence/pause ratio in audio."""
        try:
            # Detect silence (threshold: -40dBFS, min length: 500ms)
            silences = detect_silence(
                audio_segment,
                min_silence_len=500,
                silence_thresh=audio_segment.dBFS - 16 if audio_segment.dBFS > -60 else -50,
            )

            total_silence_ms = sum(end - start for start, end in silences)
            total_ms = len(audio_segment)
            pause_ratio = total_silence_ms / total_ms if total_ms > 0 else 0

            # Score: some pauses are natural (0.1-0.3 ratio is ideal)
            if 0.1 <= pause_ratio <= 0.3:
                score = 100
            elif pause_ratio < 0.1:
                score = max(60, 100 - (0.1 - pause_ratio) * 400)
            else:
                score = max(0, 100 - (pause_ratio - 0.3) * 200)

            return pause_ratio, score

        except Exception as e:
            logger.warning("Pause analysis failed: %s", e)
            return 0.2, 70  # neutral fallback

    def _compute_confidence_score(
        self, wpm_score: float, filler_score: float, pause_score: float
    ) -> float:
        """Weighted composite confidence score."""
        return wpm_score * 0.35 + filler_score * 0.40 + pause_score * 0.25

    def _wpm_assessment(self, wpm: float) -> str:
        if wpm < 90:
            return "Very Slow — may indicate hesitation"
        elif wpm < IDEAL_WPM_LOW:
            return "Slightly Slow — try to maintain a steady pace"
        elif wpm <= IDEAL_WPM_HIGH:
            return "Ideal Pace — clear and confident"
        elif wpm <= 200:
            return "Slightly Fast — consider slowing down"
        else:
            return "Too Fast — may indicate nervousness"

    def _generate_tips(self, wpm: float, filler_count: int, pause_ratio: float) -> List[str]:
        """Generate actionable speaking tips based on metrics."""
        tips = []
        if wpm < IDEAL_WPM_LOW:
            tips.append("Try to speak at a slightly faster pace to sound more confident.")
        elif wpm > IDEAL_WPM_HIGH:
            tips.append("Slow down a bit — pausing between points shows confidence.")

        if filler_count > 3:
            tips.append(
                f"You used {filler_count} filler words. Practice replacing 'um' and 'like' "
                "with brief pauses instead."
            )
        elif filler_count > 0:
            tips.append("Minor filler word usage — practice will help eliminate them.")

        if pause_ratio > 0.4:
            tips.append("You had long pauses. Prepare key talking points to maintain flow.")
        elif pause_ratio < 0.1:
            tips.append(
                "Almost no pauses detected. Brief pauses between points help your "
                "listener absorb your answer."
            )

        if not tips:
            tips.append("Excellent delivery! You spoke clearly and confidently.")

        return tips

    @staticmethod
    def _empty_metrics(error_msg: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": error_msg,
            "confidence_score": 0,
            "duration_seconds": 0,
            "word_count": 0,
            "wpm": 0,
            "wpm_score": 0,
            "wpm_assessment": "",
            "filler_count": 0,
            "filler_words": [],
            "filler_score": 0,
            "pause_ratio": 0,
            "pause_score": 0,
            "tips": [],
        }


# ── Singleton ──────────────────────────────────────────────────────
_tone_analyzer: Optional[ToneAnalyzer] = None


def get_tone_analyzer() -> ToneAnalyzer:
    global _tone_analyzer
    if _tone_analyzer is None:
        _tone_analyzer = ToneAnalyzer()
    return _tone_analyzer


def analyze_tone(
    audio_bytes: bytes,
    transcript: str,
    audio_format: str = "webm",
) -> Dict[str, Any]:
    """Analyze audio for confidence metrics."""
    return get_tone_analyzer().analyze(audio_bytes, transcript, audio_format)
