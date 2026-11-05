"""CYRUS Voice Interaction & Voice Studio REST API Endpoints.

Provides:
- Voice Studio configuration and persistent preferences.
- Puck (`am_puck`) default voice previews and custom text audition.
- Audio file streaming/serving.
- Full conversational voice turn execution.
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.app.config import settings
from backend.app.voice.kokoro_service import kokoro_service
from backend.app.voice.voice_config import KOKORO_VOICES, voice_settings
from backend.app.voice.voice_pipeline import voice_pipeline
from backend.app.voice.voice_preferences import voice_preferences

router = APIRouter(prefix="/voice", tags=["Voice Interaction & Studio"])

AUDIO_DIR = Path(settings.CYRUS_SANDBOX_PATH) / "data" / "audio"


class VoiceInteractPayload(BaseModel):
    transcript: str = Field(..., min_length=1, description="Spoken transcript in English, Hindi, or Hinglish")
    session_id: Optional[str] = Field(None, description="Active session ID")
    voice: Optional[str] = Field(None, description="Optional voice name e.g. am_puck, af_jessica")
    speed: Optional[float] = Field(1.0, ge=0.75, le=1.5, description="Speech rate multiplier")
    speak_on_mac: Optional[bool] = Field(False)


class UpdateVoicePreferencesPayload(BaseModel):
    voice_id: Optional[str] = Field(None, description="am_puck or af_jessica")
    speed: Optional[float] = Field(None, ge=0.75, le=1.5)
    voice_enabled: Optional[bool] = None
    pitch: Optional[float] = Field(None, ge=0.8, le=1.2)


class AuditionPayload(BaseModel):
    text: str = Field(..., min_length=1, description="Custom text to audition")
    voice_id: Optional[str] = Field("am_puck", description="am_puck or af_jessica")
    speed: Optional[float] = Field(1.0, ge=0.75, le=1.5)


@router.get("/status")
async def get_voice_status():
    """Returns voice subsystem status, engine info, and current default voice."""
    prefs = await voice_preferences.get_preferences()
    return {
        "status": "READY",
        "engine": "Kokoro TTS",
        "engine_status": kokoro_service.engine_status,
        "default_voice": prefs.voice_id,
        "speed": prefs.speed,
        "voice_enabled": prefs.voice_enabled,
        "available_voices": kokoro_service.list_available_voices(),
        "wake_words": voice_settings.WAKE_WORDS,
    }


@router.get("/studio/config")
async def get_studio_config():
    """Returns Voice Studio settings, persistent preferences, and voice profiles."""
    prefs = await voice_preferences.get_preferences()
    return {
        "engine": "Kokoro TTS",
        "engine_status": kokoro_service.engine_status,
        "active_voice_id": prefs.voice_id,
        "active_speed": prefs.speed,
        "voice_enabled": prefs.voice_enabled,
        "pitch": prefs.pitch,
        "sample_rate_hz": kokoro_service.sample_rate,
        "voices": kokoro_service.list_available_voices(),
        "puck_details": {
            "id": "am_puck",
            "name": "Puck",
            "role": "Default CYRUS Voice",
            "personality": KOKORO_VOICES["am_puck"].description,
        },
    }


@router.post("/studio/config")
async def update_studio_config(payload: UpdateVoicePreferencesPayload):
    """Updates and persists voice settings in SQLite."""
    updated = await voice_preferences.update_preferences(
        voice_id=payload.voice_id,
        speed=payload.speed,
        voice_enabled=payload.voice_enabled,
        pitch=payload.pitch,
    )
    return {"success": True, "updated_preferences": updated}


@router.post("/studio/preview")
async def preview_puck_voice():
    """Generates the signature Puck (`am_puck`) speech sample."""
    res = await kokoro_service.get_puck_preview()
    return res


@router.post("/studio/audition")
async def audition_custom_text(payload: AuditionPayload):
    """Auditions custom text in real-time with adjustable speed."""
    res = await kokoro_service.synthesize_speech(
        text=payload.text,
        voice_id=payload.voice_id or "am_puck",
        speed=payload.speed or 1.0,
    )
    return res


@router.post("/interact")
async def process_voice_turn(payload: VoiceInteractPayload):
    """Full voice turn: parses transcript, executes CORE turn, synthesizes speech with Puck."""
    result = await voice_pipeline.execute_voice_turn(
        raw_transcript=payload.transcript,
        session_id=payload.session_id,
        voice=payload.voice,
        speed=payload.speed,
        speak_on_mac=payload.speak_on_mac or False,
    )
    return result


@router.get("/audio/{filename}")
async def serve_audio_file(filename: str):
    """Serves generated audio files for instant web playback."""
    file_path = AUDIO_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path=str(file_path), media_type="audio/wav", filename=filename)


@router.post("/interrupt")
async def interrupt_speech():
    """Immediately halts audio playback and unregisters process."""
    stopped = await kokoro_service.interrupt_speech()
    return {"interrupted": stopped}
