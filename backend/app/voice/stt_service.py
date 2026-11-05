"""CYRUS Local Speech-to-Text (STT) Service.

Processes spoken user input in Hindi, Hinglish, or English.
Detects wake-words, extracts semantic intent, and interfaces with the Language Gate.
"""

import logging
import re
from typing import Any, Dict, Optional
from backend.app.core.language_config import language_governance
from backend.app.voice.voice_config import voice_settings

logger = logging.getLogger("cyrus.voice.stt")


class SpeechToTextService:
    """Manages audio transcription, language detection, and wake-word parsing."""

    def __init__(self):
        self.wake_words = [w.lower() for w in voice_settings.WAKE_WORDS]

    def parse_speech_transcript(
        self,
        raw_transcript: str,
        confidence: float = 1.0,
    ) -> Dict[str, Any]:
        """Parses speech text:
        1. Checks for wake-word activation ("Hey CYRUS", "CYRUS").
        2. Strips wake-word prefix to extract core command.
        3. Analyzes whether speech is English, Hindi, or Hinglish.
        """
        text = raw_transcript.strip()
        if not text:
            return {
                "success": False,
                "clean_text": "",
                "wake_word_triggered": False,
                "detected_language": "English",
                "confidence": confidence,
            }

        # Check wake-word
        lower_text = text.lower()
        wake_word_triggered = False
        clean_text = text

        for ww in self.wake_words:
            if lower_text.startswith(ww):
                wake_word_triggered = True
                # Remove wake-word prefix
                clean_text = re.sub(rf"^{re.escape(ww)}[\s,:\-]*", "", text, flags=re.IGNORECASE).strip()
                break
            elif ww in lower_text:
                wake_word_triggered = True

        # If only wake word was spoken, default greeting
        if not clean_text:
            clean_text = "Good morning, CYRUS."

        # Detect spoken language
        detected_language = language_governance.detect_input_language(clean_text)

        logger.info(
            "Parsed spoken transcript: '%s' -> '%s' (Lang: %s, WakeWord: %s)",
            text, clean_text, detected_language, wake_word_triggered
        )

        return {
            "success": True,
            "raw_transcript": text,
            "clean_text": clean_text,
            "wake_word_triggered": wake_word_triggered,
            "detected_language": detected_language,
            "confidence": confidence,
        }


# Global singleton instance
stt_service = SpeechToTextService()
