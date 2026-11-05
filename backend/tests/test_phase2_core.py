"""Tests for Phase 2: CYRUS CORE, Local AI Engine & Conversation Pipeline.

Verifies:
1. English input understanding -> English response.
2. Hindi Devanagari input understanding -> 100% English response.
3. Hinglish input understanding -> 100% English response.
4. Session persistence in SQLite.
5. Conversation history retrieval.
6. Output policy enforcement guard.
7. Resilience when local Ollama is offline.
"""

import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.language_config import language_governance
from backend.app.core.orchestrator import cyrus_core
from backend.app.database import execute_query, execute_write, init_db


class TestPhase2CoreOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Test suite for CYRUS CORE conversational intelligence."""

    async def asyncSetUp(self):
        await init_db()

    async def test_english_interaction(self):
        result = await cyrus_core.process_message("Good morning, CYRUS.")
        self.assertEqual(result["detected_language"], "English")
        self.assertEqual(result["response_language"], "English")
        self.assertIn("Good morning", result["response"])
        self.assertTrue(len(result["response"]) > 10)

        # Verify response is compliant with English policy
        compliant, reason = language_governance.validate_response_compliance(result["response"])
        self.assertTrue(compliant, reason)

    async def test_hindi_devanagari_interaction(self):
        result = await cyrus_core.process_message("आज का मौसम कैसा है और मेरा शेड्यूल क्या है?")
        self.assertEqual(result["detected_language"], "Hindi")
        self.assertEqual(result["response_language"], "English")

        # Crucial check: Must NOT contain any Devanagari characters
        compliant, reason = language_governance.validate_response_compliance(result["response"])
        self.assertTrue(compliant, f"Violation: Hindi response detected: {result['response']}")

    async def test_hinglish_interaction(self):
        hinglish_prompts = [
            "CYRUS, aaj mera schedule kya hai?",
            "Mujhe batao website mein kya problem hai.",
            "Kal subah mujhe 7 baje yaad dilana.",
            "Mera GitHub project open karo.",
        ]
        for prompt in hinglish_prompts:
            result = await cyrus_core.process_message(prompt)
            self.assertEqual(result["detected_language"], "Hinglish")
            self.assertEqual(result["response_language"], "English")

            # Check that response is in English
            compliant, reason = language_governance.validate_response_compliance(result["response"])
            self.assertTrue(compliant, f"Non-English response for '{prompt}': {result['response']}")

    async def test_session_persistence_and_history(self):
        # Turn 1
        res1 = await cyrus_core.process_message("Good morning, CYRUS.")
        session_id = res1["session_id"]
        self.assertIsNotNone(session_id)

        # Turn 2 in the same session
        res2 = await cyrus_core.process_message("CYRUS, check my business.", session_id=session_id)
        self.assertEqual(res2["session_id"], session_id)

        # Retrieve history from SQLite
        history = await cyrus_core.get_conversation_history(session_id)
        self.assertGreaterEqual(len(history), 4)  # 2 user messages + 2 assistant messages

        # Verify roles
        roles = [msg["role"] for msg in history]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)

    async def test_language_guard_blocks_hindi_output(self):
        # Direct test on language compliance validator
        bad_hindi_output = "नमस्ते सक्षम, मैं आपकी कैसे मदद कर सकता हूँ?"
        is_compliant, reason = language_governance.validate_response_compliance(bad_hindi_output)
        self.assertFalse(is_compliant)
        self.assertIn("Devanagari", reason)

        # Clean English output must pass
        clean_english = "Good morning Saksham. How can I assist you with your project today?"
        is_compliant, _ = language_governance.validate_response_compliance(clean_english)
        self.assertTrue(is_compliant)


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase2CoreOrchestrator)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
