"""CYRUS Persistent Voice Preferences.

Stores and restores voice engine preferences in SQLite:
- Default voice: Puck (`am_puck`)
- Alternative voice: Jessica (`af_jessica`)
- Speech speed (0.75x to 1.5x)
- Voice enabled/disabled toggle
Survives system reboots, shutdowns, and crashes.
"""

from dataclasses import asdict, dataclass
import json
import logging
from typing import Any, Dict
from backend.app.memory.memory_store import memory_store
from backend.app.memory.models import FactType, MemoryCategory
from backend.app.voice.voice_config import KOKORO_VOICES, voice_settings

logger = logging.getLogger("cyrus.voice.preferences")


@dataclass
class VoicePreferenceData:
    voice_id: str = "am_puck"
    speed: float = 1.0
    voice_enabled: bool = True
    pitch: float = 1.0


class VoicePreferencesManager:
    """Manages persistent voice settings in SQLite."""

    def __init__(self):
        self._cached_prefs = VoicePreferenceData()
        self._is_loaded = False

    async def get_preferences(self) -> VoicePreferenceData:
        """Retrieves persistent voice preferences from SQLite."""
        if not self._is_loaded:
            try:
                record = await memory_store.get_memory(
                    category=MemoryCategory.PERSONAL,
                    memory_key="voice_preferences",
                    tenant_id="default",
                )
                if record:
                    data = json.loads(record["memory_value"])
                    self._cached_prefs = VoicePreferenceData(
                        voice_id=data.get("voice_id", "am_puck"),
                        speed=float(data.get("speed", 1.0)),
                        voice_enabled=bool(data.get("voice_enabled", True)),
                        pitch=float(data.get("pitch", 1.0)),
                    )
            except Exception as e:
                logger.warning("Failed to load voice preferences from DB: %s", e)
            self._is_loaded = True
        return self._cached_prefs

    async def update_preferences(
        self,
        voice_id: Optional[str] = None,
        speed: Optional[float] = None,
        voice_enabled: Optional[bool] = None,
        pitch: Optional[float] = None,
    ) -> VoicePreferenceData:
        """Updates and persists voice settings into SQLite."""
        current = await self.get_preferences()

        if voice_id is not None:
            if voice_id not in KOKORO_VOICES:
                logger.warning("Unknown voice ID '%s', defaulting to am_puck", voice_id)
                current.voice_id = "am_puck"
            else:
                current.voice_id = voice_id

        if speed is not None:
            current.speed = max(0.75, min(1.5, round(speed, 2)))

        if voice_enabled is not None:
            current.voice_enabled = voice_enabled

        if pitch is not None:
            current.pitch = max(0.8, min(1.2, round(pitch, 2)))

        # Persist to SQLite
        await memory_store.save_memory(
            category=MemoryCategory.PERSONAL,
            memory_key="voice_preferences",
            memory_value=json.dumps(asdict(current)),
            tenant_id="default",
            fact_type=FactType.PREFERENCE,
            confidence=1.0,
            source="user_explicit",
        )
        self._cached_prefs = current
        logger.info("Persisted voice preferences: Voice=%s, Speed=%.2f, Enabled=%s", current.voice_id, current.speed, current.voice_enabled)
        return current


voice_preferences = VoicePreferencesManager()
