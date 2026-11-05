"""CYRUS Voice Engine Configuration.

Defines parameters for speech-to-text, text-to-speech, wake-words,
and hardware privacy controls for macOS.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class VoiceSettings:
    """Central configuration for local speech recognition and synthesis."""

    # Speech-to-Text (STT) Settings
    STT_ENGINE: str = "web_speech_local_bridge"
    STT_INPUT_LANGUAGES: List[str] = field(default_factory=lambda: ["en-US", "hi-IN", "en-IN"])
    STT_CONFIDENCE_THRESHOLD: float = 0.65

    # Text-to-Speech (TTS) Settings
    TTS_ENGINE: str = "macos_native_say"  # Native zero-cost, zero-latency macOS speech
    TTS_DEFAULT_VOICE: str = "Daniel"     # Calm, sophisticated British English
    TTS_FALLBACK_VOICE: str = "Samantha"  # Calm American English
    TTS_RATE_WPM: int = 185               # Natural, articulate cadence
    TTS_PITCH: float = 1.0

    # Wake-word detection
    ENABLE_WAKE_WORD: bool = True
    WAKE_WORDS: List[str] = field(default_factory=lambda: ["cyrus", "hey cyrus", "ok cyrus"])

    # Privacy & Hardware Controls
    AUTO_RELEASE_MICROPHONE: bool = True
    ALLOW_SECRET_RECORDING: bool = False  # Strictly forbidden
    MUTE_ON_EXAM_MODE: bool = True
    MUTE_ON_EMERGENCY_STOP: bool = True


voice_settings = VoiceSettings()
