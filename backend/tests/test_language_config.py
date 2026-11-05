"""Tests for CYRUS Centralized Language Governance."""

import pytest
from backend.app.core.language_config import language_governance


def test_language_detection_english():
    text = "Good morning, CYRUS. How are you today?"
    detected = language_governance.detect_input_language(text)
    assert detected == "English"


def test_language_detection_hindi_devanagari():
    text = "आज का मौसम कैसा है और मेरा शेड्यूल क्या है?"
    detected = language_governance.detect_input_language(text)
    assert detected == "Hindi"


def test_language_detection_hinglish():
    samples = [
        "CYRUS, aaj mera schedule kya hai?",
        "Mujhe batao website mein kya problem hai.",
        "Kal subah mujhe 7 baje yaad dilana.",
        "Mera GitHub project open karo.",
    ]
    for sample in samples:
        detected = language_governance.detect_input_language(sample)
        assert detected == "Hinglish", f"Failed to detect Hinglish for: {sample}"


def test_response_compliance_english():
    response = "Good morning Saksham. All systems are operational. You have 3 tasks scheduled today."
    compliant, reason = language_governance.validate_response_compliance(response)
    assert compliant is True


def test_response_compliance_rejects_hindi_devanagari():
    response = "नमस्ते सक्षम, आपका सिस्टम तैयार है।"
    compliant, reason = language_governance.validate_response_compliance(response)
    assert compliant is False
    assert "Devanagari" in reason


def test_response_compliance_rejects_excessive_hinglish():
    response = "Haan bhai, aaj aapka kaam shuru karte hain aur kal dekhenge."
    compliant, reason = language_governance.validate_response_compliance(response)
    assert compliant is False
    assert "Hinglish" in reason
