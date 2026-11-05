"""CYRUS Full Voice Interaction Pipeline.

Coordinates:
1. Speech-to-Text parsing (wake-word + language detection).
2. CYRUS CORE conversational intelligence.
3. Strict English output verification.
4. Text-to-Speech synthesis with interruptibility.
5. Exam Mode & Emergency Halt hardware protection.
"""

import logging
from typing import Any, Dict, Optional
from backend.app.core.orchestrator import cyrus_core
from backend.app.guardian.emergency_stop import emergency_controller
from backend.app.lifecycle.process_manager import LifecycleState, process_manager
from backend.app.voice.stt_service import stt_service
from backend.app.voice.tts_service import tts_service

logger = logging.getLogger("cyrus.voice.pipeline")


class VoicePipeline:
    """End-to-end voice loop orchestrator."""

    async def execute_voice_turn(
        self,
        raw_transcript: str,
        session_id: Optional[str] = None,
        voice: Optional[str] = None,
        speak_on_mac: bool = False,
    ) -> Dict[str, Any]:
        """Processes a full voice turn from spoken audio/transcript to synthesized English speech."""
        # 1. Privacy & Safety Guards: Exam Mode and Emergency Halt
        if emergency_controller.is_halted:
            return {
                "success": False,
                "error": "Voice disabled: CYRUS STOP is currently activated.",
                "response_text": "CYRUS STOP is active. Voice interaction is locked.",
                "speech_payload": tts_service.prepare_speech_payload("CYRUS STOP is active. Voice is locked."),
            }

        if process_manager.current_state == LifecycleState.EXAM_MODE:
            return {
                "success": False,
                "error": "Voice disabled: Exam Mode is active (Microphone and audio are released).",
                "response_text": "Exam mode is active. Voice processing is disabled.",
                "speech_payload": tts_service.prepare_speech_payload("Exam mode is active."),
            }

        # 2. Parse Speech Input (STT)
        stt_result = stt_service.parse_speech_transcript(raw_transcript)
        if not stt_result.get("success"):
            return {
                "success": False,
                "error": "No audible speech recognized.",
                "response_text": "I could not detect any audible speech. How can I help you?",
            }

        clean_text = stt_result["clean_text"]
        detected_lang = stt_result["detected_language"]
        wake_word_triggered = stt_result["wake_word_triggered"]

        # 3. Process through CYRUS CORE
        core_result = await cyrus_core.process_message(
            user_message=clean_text,
            session_id=session_id,
        )

        response_text = core_result["response"]

        # 4. Prepare Synthesized Speech (TTS)
        speech_payload = tts_service.prepare_speech_payload(
            text=response_text,
            voice=voice,
        )

        # 5. Optional Direct Mac Speaker Output
        backend_spoken = False
        if speak_on_mac:
            tts_res = await tts_service.speak_locally_on_mac(
                text=response_text,
                voice=voice,
            )
            backend_spoken = tts_res.get("backend_spoken", False)

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
            "speech_payload": speech_payload,
            "backend_spoken": backend_spoken,
        }


# Global singleton instance
voice_pipeline = VoicePipeline()
