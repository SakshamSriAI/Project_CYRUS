"""CYRUS Voice Interaction REST API Endpoints."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.voice.tts_service import tts_service
from backend.app.voice.voice_config import voice_settings
from backend.app.voice.voice_pipeline import voice_pipeline

router = APIRouter(prefix="/voice", tags=["Voice Interaction"])


class VoiceInteractPayload(BaseModel):
    transcript: str = Field(..., min_length=1, description="Spoken transcript in English, Hindi, or Hinglish")
    session_id: Optional[str] = Field(None, description="Active session ID")
    voice: Optional[str] = Field(None, description="Optional voice name e.g. Daniel, Samantha")
    speak_on_mac: Optional[bool] = Field(False, description="Whether to also trigger macOS native say speaker output")


class VoiceSynthesizePayload(BaseModel):
    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    speak_on_mac: Optional[bool] = False


@router.get("/status")
async def get_voice_status():
    """Returns voice subsystem status, available voices, and audio policies."""
    voices = tts_service.get_supported_voices()
    return {
        "status": "READY",
        "stt_engine": voice_settings.STT_ENGINE,
        "tts_engine": voice_settings.TTS_ENGINE,
        "default_voice": voice_settings.TTS_DEFAULT_VOICE,
        "speech_rate_wpm": voice_settings.TTS_RATE_WPM,
        "supported_input_languages": ["en-US", "hi-IN", "en-IN"],
        "mandatory_response_language": "English",
        "wake_words": voice_settings.WAKE_WORDS,
        "available_voices": voices,
    }


@router.post("/interact")
async def process_voice_turn(payload: VoiceInteractPayload):
    """Processes spoken input, runs intelligence through CYRUS CORE, and returns synthesized English speech."""
    result = await voice_pipeline.execute_voice_turn(
        raw_transcript=payload.transcript,
        session_id=payload.session_id,
        voice=payload.voice,
        speak_on_mac=payload.speak_on_mac or False,
    )
    return result


@router.post("/synthesize")
async def synthesize_speech(payload: VoiceSynthesizePayload):
    """Synthesizes text into speech payload conforming to English policy."""
    speech_payload = tts_service.prepare_speech_payload(
        text=payload.text,
        voice=payload.voice,
    )
    backend_spoken = False
    if payload.speak_on_mac:
        res = await tts_service.speak_locally_on_mac(payload.text, payload.voice)
        backend_spoken = res.get("backend_spoken", False)

    return {
        "speech_payload": speech_payload,
        "backend_spoken": backend_spoken,
    }


@router.post("/interrupt")
async def interrupt_speech():
    """Immediately stops ongoing voice playback on Mac speakers."""
    stopped = await tts_service.interrupt_speech()
    return {"interrupted": stopped}
