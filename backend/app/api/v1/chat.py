"""CYRUS Conversation & Chat API Endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.core.llm_client import llm_client
from backend.app.core.orchestrator import cyrus_core
from backend.app.database import execute_query, execute_write

router = APIRouter(prefix="/chat", tags=["Conversation & Intelligence"])


class ChatMessageRequest(BaseModel):
    """Payload for submitting a message to CYRUS."""
    message: str = Field(..., min_length=1, description="User instruction or question in English, Hindi, or Hinglish")
    session_id: Optional[str] = Field(None, description="Existing session ID or null to create a new session")
    model: Optional[str] = Field(None, description="Optional local model override")


@router.post("/message")
async def send_message(payload: ChatMessageRequest):
    """Processes a user message through CYRUS CORE, enforcing language governance and session persistence."""
    try:
        result = await cyrus_core.process_message(
            user_message=payload.message,
            session_id=payload.session_id,
            model_override=payload.model,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CYRUS CORE error: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Retrieves conversation history for an active session."""
    query = """
    SELECT id, role, detected_language, content, timestamp
    FROM messages
    WHERE session_id = ?
    ORDER BY timestamp ASC;
    """
    messages = await execute_query(query, (session_id,))
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": messages,
    }


@router.get("/models")
async def get_models_status():
    """Returns local Ollama connectivity status and list of downloaded open-weight models."""
    conn = llm_client.check_connection()
    return conn
