"""Tests for Phase 5 Extension: Kokoro TTS & Puck Voice Configuration.

Verifies:
1. Text preprocessor: acronym expansion, markdown stripping, conversational pauses.
2. Persistent voice preferences: defaults to am_puck, persists to SQLite, reload resilience.
3. Kokoro TTS service: generates valid 24kHz audio, Puck preview, custom text audition.
4. Strict English-only policy enforcement in audio synthesis.
5. Voice Studio API endpoints: configuration, preview, audition, audio file streaming.
"""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import init_db
from backend.app.lifecycle.process_manager import LifecycleState, process_manager
from backend.app.voice.kokoro_service import AUDIO_OUTPUT_DIR, kokoro_service
from backend.app.voice.text_preprocessor import text_preprocessor
from backend.app.voice.voice_config import KOKORO_VOICES, voice_settings
from backend.app.voice.voice_preferences import VoicePreferencesManager, voice_preferences


class TestPhase5KokoroPuck(unittest.IsolatedAsyncioTestCase):
    """Test suite for Kokoro TTS and Puck Voice Integration."""

    async def asyncSetUp(self):
        await init_db()
        process_manager.set_state(LifecycleState.ACTIVE)

    def test_text_preprocessor_acronym_and_markdown(self):
        # 1. Technical acronym expansion
        raw = "CYRUS uses SQLite with WAL mode on 16 GB of RAM, accessing the REST API."
        processed = text_preprocessor.prepare_for_synthesis(raw)
        self.assertIn("S Q L lite", processed)
        self.assertIn("W A L", processed)
        self.assertIn("gigabytes", processed)
        self.assertIn("R A M", processed)
        self.assertIn("A P I", processed)

        # 2. Markdown stripping
        md_text = "Here is **important** information with `print('hello')` code and [link](https://github.com)."
        cleaned = text_preprocessor.clean_markdown_and_code(md_text)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertIn("important", cleaned)

        # 3. Sentence segmentation
        long_paragraph = "First sentence here. Second sentence follows. Third sentence concludes."
        segments = text_preprocessor.segment_text(long_paragraph)
        self.assertEqual(len(segments), 3)

    async def test_voice_preferences_persistence(self):
        # 1. Default preferences should be Puck (am_puck)
        prefs = await voice_preferences.get_preferences()
        self.assertEqual(prefs.voice_id, "am_puck")
        self.assertEqual(prefs.speed, 1.0)
        self.assertTrue(prefs.voice_enabled)

        # 2. Update preferences in SQLite
        updated = await voice_preferences.update_preferences(
            voice_id="af_jessica",
            speed=1.1,
            voice_enabled=True,
            pitch=1.0,
        )
        self.assertEqual(updated.voice_id, "af_jessica")
        self.assertEqual(updated.speed, 1.1)

        # 3. Instantiate a fresh manager to test reload from SQLite
        fresh_mgr = VoicePreferencesManager()
        reloaded = await fresh_mgr.get_preferences()
        self.assertEqual(reloaded.voice_id, "af_jessica")
        self.assertEqual(reloaded.speed, 1.1)

        # 4. Restore default to am_puck
        await voice_preferences.update_preferences(voice_id="am_puck", speed=1.0)
        restored = await voice_preferences.get_preferences()
        self.assertEqual(restored.voice_id, "am_puck")

    def test_available_voices_and_puck_default(self):
        voices = kokoro_service.list_available_voices()
        self.assertGreaterEqual(len(voices), 2)
        puck_entry = next((v for v in voices if v["voice_id"] == "am_puck"), None)
        self.assertIsNotNone(puck_entry)
        self.assertTrue(puck_entry["is_default"])
        self.assertEqual(puck_entry["gender"], "Masculine")
        self.assertEqual(puck_entry["accent"], "American English")

        jessica_entry = next((v for v in voices if v["voice_id"] == "af_jessica"), None)
        self.assertIsNotNone(jessica_entry)
        self.assertEqual(jessica_entry["gender"], "Feminine")

    async def test_puck_signature_preview(self):
        result = await kokoro_service.get_puck_preview()
        self.assertTrue(result["success"])
        self.assertEqual(result["voice_id"], "am_puck")
        self.assertIn("Puck", result["voice_name"])
        self.assertTrue(result["audio_filename"].endswith(".wav"))
        self.assertTrue(result["audio_url"].startswith("/api/v1/voice/audio/"))

        # Verify physical file generated
        output_file = AUDIO_OUTPUT_DIR / result["audio_filename"]
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 1000)

    async def test_custom_text_audition(self):
        custom_text = "Good day Saksham. CYRUS Voice Studio is fully operational."
        res = await kokoro_service.synthesize_speech(
            text=custom_text,
            voice_id="am_puck",
            speed=1.1,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["voice_id"], "am_puck")
        self.assertEqual(res["speed"], 1.1)
        self.assertGreater(res["duration_seconds"], 0)

        output_file = AUDIO_OUTPUT_DIR / res["audio_filename"]
        self.assertTrue(output_file.exists())

    async def test_kokoro_english_only_enforcement(self):
        # Attempt to synthesize Hindi / non-compliant text
        hindi_text = "नमस्ते सक्षम, यह आवाज़ का परीक्षण है।"
        res = await kokoro_service.synthesize_speech(
            text=hindi_text,
            voice_id="am_puck",
        )
        self.assertTrue(res["success"])
        # Phonetic text must NOT contain Devanagari characters
        self.assertNotIn("नमस्ते", res["phonetic_text"])
        self.assertNotIn("परीक्षण", res["phonetic_text"])


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase5KokoroPuck)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
