"""CYRUS Full Voice Interaction Pipeline.

Coordinates:
1. Speech-to-Text parsing (wake-word + language detection).
2. CYRUS CORE conversational intelligence.
3. Centralized English output verification.
4. Kokoro TTS neural synthesis with Puck (`am_puck`) as the default voice.
5. Exam Mode & Emergency Halt hardware protection.
"""

import logging
from typing import Any, Dict, Optional
from backend.app.core.orchestrator import cyrus_core
from backend.app.guardian.emergency_stop import emergency_controller
from backend.app.lifecycle.process_manager import LifecycleState, process_manager
from backend.app.voice.kokoro_service import kokoro_service
from backend.app.voice.stt_service import stt_service
from backend.app.voice.voice_preferences import voice_preferences

logger = logging.getLogger("cyrus.voice.pipeline")


class VoicePipeline:
    """End-to-end voice loop orchestrator with Kokoro Puck default voice."""

    async def execute_voice_turn(
        self,
        raw_transcript: str,
        session_id: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        speak_on_mac: bool = False,
    ) -> Dict[str, Any]:
        """Processes a full voice turn from spoken audio/transcript to synthesized English speech."""
        # 1. Privacy & Safety Guards: Exam Mode and Emergency Halt
        if emergency_controller.is_halted:
            return {
                "success": False,
                "error": "Voice disabled: CYRUS STOP is currently activated.",
                "response_text": "CYRUS STOP is active. Voice interaction is locked.",
                "voice_id": "am_puck",
            }

        if process_manager.current_state == LifecycleState.EXAM_MODE:
            return {
                "success": False,
                "error": "Voice disabled: Exam Mode is active (Microphone and audio are released).",
                "response_text": "Exam mode is active. Voice processing is disabled.",
                "voice_id": "am_puck",
            }

        # 2. Parse Speech Input (STT)
        stt_result = stt_service.parse_speech_transcript(raw_transcript)
        if not stt_result.get("success"):
            return {
                "success": False,
                "error": "No audible speech recognized.",
                "response_text": "I could not detect any audible speech. How can I help you?",
                "voice_id": "am_puck",
            }

        clean_text = stt_result["clean_text"]
        detected_lang = stt_result["detected_language"]
        wake_word_triggered = stt_result["wake_word_triggered"]

        # 3. Retrieve Persistent Voice Preferences
        prefs = await voice_preferences.get_preferences()
        chosen_voice = voice or prefs.voice_id  # am_puck by default
        chosen_speed = speed if speed is not None else prefs.speed

        # 4. Process through CYRUS CORE Intelligence
        core_result = await cyrus_core.process_message(
            user_message=clean_text,
            session_id=session_id,
        )

        response_text = core_result["response"]

        # 5. Synthesize Natural Spoken Speech via Kokoro (`am_puck`)
        synthesis_result = await kokoro_service.synthesize_speech(
            text=response_text,
            voice_id=chosen_voice,
            speed=chosen_speed,
        )

        return {
            "success": True,
            "session_id": core_result["session_id"],
            "raw_transcript": raw_transcript,
            "clean_text": clean_text,
            "detected_language": detected_lang,
            "wake_word_triggered": wake_word_triggered,
            "response_text": response_text,
            "response_language": "English",
            "model_used": core_result.get("model_used", "deterministic-core"),
            "speech_payload": {
                "text": response_text,
                "voice": synthesis_result["voice_id"],
                "audio_url": synthesis_result["audio_url"],
            },
            "voice": {
                "voice_id": synthesis_result["voice_id"],
                "voice_name": synthesis_result["voice_name"],
                "speed": synthesis_result["speed"],
                "audio_url": synthesis_result["audio_url"],
                "duration_seconds": synthesis_result["duration_seconds"],
                "engine": "Kokoro TTS",
            },
        }


# Global singleton instance
voice_pipeline = VoicePipeline()
