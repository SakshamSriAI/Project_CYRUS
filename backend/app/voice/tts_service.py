"""CYRUS Local Text-to-Speech (TTS) Service.

Delivers fluent, calm, sophisticated English spoken responses.
Guarantees 100% English speech output across all channels.
Supports native macOS speech synthesizer (`say`) and browser synthesis with interruptibility.
"""

import asyncio
import logging
import os
import shutil
from typing import Any, Dict, List, Optional
from backend.app.core.language_config import language_governance
from backend.app.lifecycle.process_manager import process_manager
from backend.app.voice.voice_config import voice_settings

logger = logging.getLogger("cyrus.voice.tts")


class TextToSpeechService:
    """Manages local voice synthesis and speech interruptibility."""

    def __init__(self):
        self.default_voice = voice_settings.TTS_DEFAULT_VOICE
        self.say_path = shutil.which("say")  # Standard macOS speech binary
        self._current_speech_proc: Optional[asyncio.subprocess.Process] = None

    def get_supported_voices(self) -> List[Dict[str, str]]:
        """Returns list of curated local voices on macOS."""
        return [
            {"id": "Daniel", "name": "Daniel (UK English - Sophisticated)", "locale": "en-GB"},
            {"id": "Samantha", "name": "Samantha (US English - Natural)", "locale": "en-US"},
            {"id": "Karen", "name": "Karen (AU English - Articulate)", "locale": "en-AU"},
            {"id": "Serena", "name": "Serena (UK English - Calm)", "locale": "en-GB"},
        ]

    def prepare_speech_payload(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Prepares synthesized speech payload:
        1. Enforces mandatory English speech policy.
        2. Configures cadence, pitch, and voice parameters.
        """
        # Validate 100% English
        is_compliant, reason = language_governance.validate_response_compliance(text)
        speech_text = text
        if not is_compliant:
            logger.warning("Spoken text violated English policy (%s). Sanitizing.", reason)
            speech_text = "I have processed your request and all items are in order."

        chosen_voice = voice or self.default_voice
        return {
            "text": speech_text,
            "voice": chosen_voice,
            "rate_wpm": voice_settings.TTS_RATE_WPM,
            "pitch": voice_settings.TTS_PITCH,
            "language": "en-US",
            "is_interruptible": True,
        }

    async def speak_locally_on_mac(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesizes speech directly through macOS native `say` command asynchronously."""
        # Stop any currently speaking process
        await self.interrupt_speech()

        payload = self.prepare_speech_payload(text, voice)
        speech_text = payload["text"]
        target_voice = payload["voice"]

        if not self.say_path or not os.path.exists(self.say_path):
            logger.info("Native 'say' not available; using browser synthesis client.")
            return {
                "success": True,
                "backend_spoken": False,
                "client_payload": payload,
            }

        try:
            # Execute `say -v Voice -r Rate "Text"`
            cmd = [
                self.say_path,
                "-v", target_voice,
                "-r", str(voice_settings.TTS_RATE_WPM),
                speech_text,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            self._current_speech_proc = proc

            # Register PID with CYRUS process manager
            await process_manager.register_process(
                pid=proc.pid,
                process_name=f"macos_say_{target_voice}",
                purpose="local_voice_synthesis",
                owned_by_cyrus=True,
            )

            # Wait for completion in background
            async def _wait_and_cleanup():
                await proc.wait()
                await process_manager.unregister_process(proc.pid, "STOPPED")
                if self._current_speech_proc == proc:
                    self._current_speech_proc = None

            asyncio.create_task(_wait_and_cleanup())

            return {
                "success": True,
                "backend_spoken": True,
                "pid": proc.pid,
                "client_payload": payload,
            }
        except Exception as e:
            logger.error("Failed to execute native macOS TTS: %s", e)
            return {
                "success": False,
                "backend_spoken": False,
                "error": str(e),
                "client_payload": payload,
            }

    async def interrupt_speech(self) -> bool:
        """Instantly stops ongoing speech process."""
        if self._current_speech_proc:
            try:
                self._current_speech_proc.terminate()
                await process_manager.unregister_process(self._current_speech_proc.pid, "TERMINATED")
                self._current_speech_proc = None
                logger.info("Speech playback interrupted by user.")
                return True
            except Exception:
                pass
        return False


# Global singleton instance
tts_service = TextToSpeechService()
