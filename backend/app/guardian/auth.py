"""CYRUS GUARDIAN Authentication & Identity Management.

Provides local cryptographic session tokens, API validation, and identity binding.
Saksham is the sole sovereign owner of CYRUS with root authority.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import os
import secrets
from typing import Dict, Optional
from backend.app.config import settings

OWNER_IDENTITY = "Saksham"


class GuardianAuth:
    """Manages cryptographic tokens and local authentication for CYRUS."""

    def __init__(self):
        self._active_tokens: Dict[str, Dict[str, Any]] = {}
        self._secret_key = settings.CYRUS_SECRET_KEY.encode("utf-8")

    def create_session_token(self, subject: str = OWNER_IDENTITY, role: str = "OWNER") -> str:
        """Generates a secure cryptographic session token."""
        raw_token = secrets.token_hex(32)
        # Create HMAC signature for tamper-evidence
        signature = hmac.new(self._secret_key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()
        token = f"cyrus_{raw_token}_{signature[:16]}"

        now = datetime.now(timezone.utc).isoformat()
        self._active_tokens[token] = {
            "subject": subject,
            "role": role,
            "created_at": now,
            "is_valid": True,
        }
        return token

    def validate_token(self, token: Optional[str]) -> bool:
        """Validates that a presented token was genuinely issued and is active."""
        if not token:
            return False

        record = self._active_tokens.get(token)
        if not record or not record.get("is_valid"):
            return False

        # Verify HMAC signature integrity
        parts = token.split("_")
        if len(parts) != 3 or parts[0] != "cyrus":
            return False

        raw_token, sig = parts[1], parts[2]
        expected_sig = hmac.new(self._secret_key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        return hmac.compare_digest(sig, expected_sig)

    def revoke_all_tokens(self):
        """Immediately invalidates all active session tokens during Emergency Stop."""
        for token in self._active_tokens:
            self._active_tokens[token]["is_valid"] = False


# Global singleton instance
guardian_auth = GuardianAuth()
