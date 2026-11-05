"""CYRUS Voice Engine Configuration.

Configured with Kokoro TTS as the primary neural engine and Puck (`am_puck`)
as the default conversational, warm, and articulate voice.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class VoiceProfile:
    """Metadata for a supported neural voice."""
    voice_id: str
    name: str
    gender: str
    accent: str
    description: str
    is_default: bool = False


# Supported Kokoro Neural Voices
KOKORO_VOICES: Dict[str, VoiceProfile] = {
    "am_puck": VoiceProfile(
        voice_id="am_puck",
        name="Puck (American English - Conversational)",
        gender="Masculine",
        accent="American English",
        description="Warm, approachable, natural, intelligent, composed, and subtly witty. Zero robotic cadence.",
        is_default=True,
    ),
    "af_jessica": VoiceProfile(
        voice_id="af_jessica",
        name="Jessica (American English - Articulate)",
        gender="Feminine",
        accent="American English",
        description="Clear, articulate, sophisticated, and warm alternative voice.",
        is_default=False,
    ),
}


@dataclass
class VoiceSettings:
    """Central configuration for Kokoro neural speech recognition and synthesis."""

    # Primary TTS Engine (Kokoro Neural)
    PRIMARY_TTS_ENGINE: str = "kokoro"
    TTS_ENGINE: str = "kokoro"
    DEFAULT_VOICE_ID: str = "am_puck"
    TTS_DEFAULT_VOICE: str = "am_puck"
    ALTERNATIVE_VOICE_ID: str = "af_jessica"
    TTS_RATE_WPM: int = 175
    TTS_PITCH: float = 1.0
    SAMPLE_RATE_HZ: int = 24000  # Studio 24 kHz audio
    DEFAULT_SPEED: float = 1.0    # 1.0 = Natural conversational cadence (0.75x to 1.5x)
    VOICE_ENABLED: bool = True

    # Speech-to-Text (STT) Settings
    STT_ENGINE: str = "web_speech_local_bridge"
    STT_INPUT_LANGUAGES: List[str] = field(default_factory=lambda: ["en-US", "hi-IN", "en-IN"])
    STT_CONFIDENCE_THRESHOLD: float = 0.65

    # Wake-word detection
    ENABLE_WAKE_WORD: bool = True
    WAKE_WORDS: List[str] = field(default_factory=lambda: ["cyrus", "hey cyrus", "ok cyrus"])

    # Privacy & Hardware Controls
    AUTO_RELEASE_MICROPHONE: bool = True
    ALLOW_SECRET_RECORDING: bool = False  # Strictly forbidden
    MUTE_ON_EXAM_MODE: bool = True
    MUTE_ON_EMERGENCY_STOP: bool = True


voice_settings = VoiceSettings()
