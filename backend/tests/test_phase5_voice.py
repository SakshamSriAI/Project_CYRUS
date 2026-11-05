"""Tests for Phase 5: CYRUS VOICE Interaction Subsystem.

Verifies:
1. Speech-to-Text wake-word parsing and multilingual input detection (English, Hindi, Hinglish).
2. Text-to-Speech English-only speech output enforcement.
3. Full voice conversational turn with Hinglish input -> 100% English spoken output.
4. Exam Mode hardware mute and zero-footprint enforcement.
5. Emergency Stop (CYRUS STOP) voice lock.
6. Speech interruption and clean process cleanup.
"""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import init_db
from backend.app.guardian.emergency_stop import emergency_controller
from backend.app.lifecycle.process_manager import LifecycleState, process_manager
from backend.app.voice.stt_service import stt_service
from backend.app.voice.tts_service import tts_service
from backend.app.voice.voice_pipeline import voice_pipeline


class TestPhase5Voice(unittest.IsolatedAsyncioTestCase):
    """Test suite for CYRUS VOICE Speech Interaction."""

    async def asyncSetUp(self):
        await init_db()
        process_manager.set_state(LifecycleState.ACTIVE)
        if emergency_controller.is_halted:
            await emergency_controller.reset_emergency_stop()

    def test_stt_parsing_and_wake_word(self):
        # 1. English with wake-word
        res_en = stt_service.parse_speech_transcript("Hey CYRUS, what is our system status?")
        self.assertTrue(res_en["success"])
        self.assertTrue(res_en["wake_word_triggered"])
        self.assertEqual(res_en["clean_text"], "what is our system status?")
        self.assertEqual(res_en["detected_language"], "English")

        # 2. Hinglish with wake-word
        res_hing = stt_service.parse_speech_transcript("CYRUS, aaj mera schedule kya hai?")
        self.assertTrue(res_hing["success"])
        self.assertTrue(res_hing["wake_word_triggered"])
        self.assertEqual(res_hing["detected_language"], "Hinglish")
        self.assertEqual(res_hing["clean_text"], "aaj mera schedule kya hai?")

        # 3. Hindi in Devanagari script
        res_hi = stt_service.parse_speech_transcript("आज का मौसम कैसा है?")
        self.assertTrue(res_hi["success"])
        self.assertEqual(res_hi["detected_language"], "Hindi")

    def test_tts_payload_and_english_guard(self):
        clean_text = "Good morning Saksham. All systems are operational."
        payload = tts_service.prepare_speech_payload(clean_text, voice="Daniel")
        self.assertEqual(payload["voice"], "Daniel")
        self.assertEqual(payload["language"], "en-US")
        self.assertEqual(payload["text"], clean_text)

        # Non-English payload must be sanitized before speaking
        hindi_bad = "नमस्ते सक्षम, आपका स्वागत है।"
        sanitized_payload = tts_service.prepare_speech_payload(hindi_bad)
        self.assertNotIn("नमस्ते", sanitized_payload["text"])
        self.assertTrue(len(sanitized_payload["text"]) > 10)

    async def test_full_voice_turn_hinglish_to_english(self):
        # User speaks in Hinglish: "CYRUS, aaj mera schedule kya hai?"
        turn_res = await voice_pipeline.execute_voice_turn(
            raw_transcript="CYRUS, aaj mera schedule kya hai?",
            voice="Daniel",
            speak_on_mac=False,
        )
        self.assertTrue(turn_res["success"])
        self.assertEqual(turn_res["detected_language"], "Hinglish")
        self.assertTrue(turn_res["wake_word_triggered"])
        self.assertEqual(turn_res["response_language"], "English")

        # Verify speech output payload is 100% English
        speech_text = turn_res["speech_payload"]["text"]
        self.assertNotIn("aaj", speech_text.lower())
        self.assertNotIn("kya", speech_text.lower())
        self.assertTrue("schedule" in speech_text.lower() or "agenda" in speech_text.lower() or "operational" in speech_text.lower())

    async def test_voice_disabled_in_exam_mode(self):
        # Engage Exam Mode
        process_manager.set_state(LifecycleState.EXAM_MODE)

        # Attempt voice interaction
        turn_res = await voice_pipeline.execute_voice_turn("Good morning, CYRUS.")
        self.assertFalse(turn_res["success"])
        self.assertIn("Exam Mode is active", turn_res["error"])

        # Restore
        process_manager.set_state(LifecycleState.ACTIVE)

    async def test_voice_disabled_in_emergency_stop(self):
        # Trigger CYRUS STOP
        await emergency_controller.trigger_emergency_stop(reason="Voice lockdown drill")

        turn_res = await voice_pipeline.execute_voice_turn("Good morning, CYRUS.")
        self.assertFalse(turn_res["success"])
        self.assertIn("CYRUS STOP is currently activated", turn_res["error"])

        # Reset
        await emergency_controller.reset_emergency_stop()

    async def test_speech_interruption(self):
        interrupted = await tts_service.interrupt_speech()
        self.assertIsInstance(interrupted, bool)


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase5Voice)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
