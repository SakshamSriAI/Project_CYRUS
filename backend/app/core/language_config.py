"""CYRUS Centralized Language Governance.

Enforces the non-negotiable system-wide policy:
- Understands: English, Hindi (Devanagari), and Hinglish (Roman script Hindi).
- Responds: EXCLUSIVELY in English across all agents, interfaces, and voice pipelines.
"""

import re
from typing import Dict, List, Tuple
from backend.app.config import settings

# Common Hinglish lexical indicators (case-insensitive words/markers)
HINGLISH_MARKERS = {
    "aaj", "kal", "parso", "kya", "hai", "hain", "karo", "karein", "kar",
    "mujhe", "batao", "bataiye", "kaise", "kab", "kyun", "kahan", "kitna",
    "mera", "meri", "mere", "tera", "teri", "tere", "aapka", "aapki", "aapke",
    "karna", "theek", "shuru", "dhanyavaad", "kaam", "bhai", "yaar", "dekho",
    "kholo", "band", "chalao", "roko", "madad", "samjhao", "bolo", "sunao",
    "nahi", "nahin", "hoga", "hogi", "dena", "lelo", "chahiye"
}

# Regex to detect Devanagari Unicode block (Hindi script)
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")


class LanguageGovernance:
    """Centralized Language Governance controller."""

    def __init__(self):
        self.default_response_language = settings.DEFAULT_RESPONSE_LANGUAGE
        self.supported_input_languages = settings.SUPPORTED_INPUT_LANGUAGES
        self.allow_hindi_responses = settings.ALLOW_HINDI_RESPONSES

    def detect_input_language(self, text: str) -> str:
        """Detects whether the user input is Hindi (Devanagari), Hinglish, or English.

        Args:
            text: Raw input string from the user.

        Returns:
            One of 'Hindi', 'Hinglish', or 'English'.
        """
        if not text or not text.strip():
            return "English"

        clean_text = text.strip()

        # 1. Check for Devanagari script
        if DEVANAGARI_REGEX.search(clean_text):
            return "Hindi"

        # 2. Check for Hinglish vocabulary patterns
        tokens = re.findall(r"\b[a-zA-Z]+\b", clean_text.lower())
        if tokens:
            hinglish_count = sum(1 for token in tokens if token in HINGLISH_MARKERS)
            ratio = hinglish_count / len(tokens)
            # If at least 1 prominent marker or >15% tokens match common Hinglish vocabulary
            if hinglish_count >= 1 and (hinglish_count >= 2 or ratio >= 0.15 or len(tokens) <= 3):
                return "Hinglish"

        return "English"

    def validate_response_compliance(self, text: str) -> Tuple[bool, str]:
        """Validates that a generated assistant response conforms to the English-only policy.

        Args:
            text: Assistant response text.

        Returns:
            Tuple of (is_compliant, reason)
        """
        if not text:
            return True, "Empty response is compliant."

        if not self.allow_hindi_responses:
            # Check if any Devanagari character exists in the response
            if DEVANAGARI_REGEX.search(text):
                return False, "Violation: Output contains Devanagari (Hindi) characters."

            # Check for high density of Hinglish markers in the response
            tokens = re.findall(r"\b[a-zA-Z]+\b", text.lower())
            if tokens:
                hinglish_matches = [token for token in tokens if token in HINGLISH_MARKERS]
                # CYRUS responses should not be speaking Hinglish
                if len(hinglish_matches) >= 3 and (len(hinglish_matches) / len(tokens)) > 0.2:
                    return False, "Violation: Output contains excessive Hinglish conversational phrases."

        return True, "Compliant with English-only policy."

    def get_system_language_directive(self) -> str:
        """Returns the mandatory system prompt snippet that guarantees English output."""
        return (
            "MANDATORY LANGUAGE POLICY:\n"
            "- You understand inputs in English, Hindi (Devanagari), and Hinglish (Hindi in Roman script).\n"
            "- You must ALWAYS respond strictly in fluent, natural, professional English.\n"
            "- NEVER respond in Hindi or Hinglish, even if the user asks you in Hindi or Hinglish.\n"
            "- Preserve the exact intent and technical terminology of the user's input.\n"
            "- If a user instruction in Hindi/Hinglish is ambiguous, ask for clarification in English."
        )


# Global singleton instance
language_governance = LanguageGovernance()
