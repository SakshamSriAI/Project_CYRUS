"""CYRUS Local LLM Client (Ollama Integration).

Connects to the local Ollama instance on macOS via REST API.
Operates with zero external dependencies using Python's standard library.
Handles connection checks, model listing, streaming/generation, and timeout protection.
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from backend.app.config import settings

logger = logging.getLogger("cyrus.llm_client")


class OllamaClient:
    """Interface to local Ollama inference server running on MacBook."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = settings.OLLAMA_DEFAULT_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    def check_connection(self) -> Dict[str, Any]:
        """Synchronously checks if local Ollama daemon is reachable."""
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "connected": True,
                        "base_url": self.base_url,
                        "available_models": models,
                        "active_model": self.default_model,
                    }
        except Exception as e:
            logger.debug("Ollama connection check failed: %s", e)
            return {
                "connected": False,
                "base_url": self.base_url,
                "available_models": [],
                "error": str(e),
                "suggestion": "Install or start Ollama with 'ollama serve' or open the Ollama app.",
            }
        return {"connected": False, "base_url": self.base_url, "available_models": []}

    async def is_connected(self) -> bool:
        """Asynchronously checks if local Ollama daemon is running."""
        res = await asyncio.to_thread(self.check_connection)
        return res.get("connected", False)

    async def list_local_models(self) -> List[str]:
        """Returns list of downloaded model tags in local Ollama."""
        res = await asyncio.to_thread(self.check_connection)
        return res.get("available_models", [])

    def _sync_generate(self, prompt: str, system_prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Synchronously calls Ollama /api/generate endpoint."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Controlled, focused, professional responses
                "top_p": 0.9,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    result = json.loads(resp.read().decode("utf-8"))
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "model": target_model,
                        "total_duration_ns": result.get("total_duration", 0),
                        "eval_count": result.get("eval_count", 0),
                    }
                return {"success": False, "error": f"Ollama returned HTTP {resp.status}"}
        except urllib.error.URLError as e:
            return {
                "success": False,
                "error": f"Ollama connection error: {e.reason}",
                "offline": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generates a response from the local model."""
        return await asyncio.to_thread(self._sync_generate, prompt, system_prompt, model)


# Global singleton instance
llm_client = OllamaClient()
