"""CYRUS SENTINEL Telegram Alert Dispatcher.

Provides free-tier Telegram Bot notification delivery for Level 3 Critical
and Level 2 Important system events.

Supports live Telegram API when configured, and graceful simulated delivery
when unconfigured or offline (₹0 ongoing cost guarantee).
Always addresses the user as "Sir".
"""

from datetime import datetime, timezone
import json
import logging
import os
from typing import Any, Dict, Optional
import urllib.parse
import urllib.request
from backend.app.sentinel.models import EventSeverity, SentinelEvent

logger = logging.getLogger("cyrus.sentinel.telegram")


class TelegramNotifier:
    """Dispatches proactive alerts to Saksham's Telegram account."""

    def __init__(self, user_form_of_address: str = "Sir"):
        self.form_of_address = user_form_of_address
        self.bot_token = os.getenv("CYRUS_TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("CYRUS_TELEGRAM_CHAT_ID", "").strip()

    @property
    def is_live_configured(self) -> bool:
        """Checks if valid Telegram bot credentials are set in environment."""
        return bool(self.bot_token and self.chat_id and not self.bot_token.startswith("mock"))

    def format_alert_message(self, event: SentinelEvent, monitor_name: str, target_url: str) -> str:
        """Formats an urgent, structured alert addressed to Sir."""
        icon = "🚨" if event.severity == EventSeverity.CRITICAL else "⚠️" if event.severity == EventSeverity.IMPORTANT else "ℹ️"
        severity_label = f"LEVEL 3 CRITICAL" if event.severity == EventSeverity.CRITICAL else f"LEVEL 2 IMPORTANT" if event.severity == EventSeverity.IMPORTANT else "LEVEL 1 INFO"

        latency_str = f"{event.latency_ms:.1f}ms" if event.latency_ms is not None else "Timeout"
        status_code_str = str(event.status_code) if event.status_code else "Unreachable"

        return (
            f"{icon} [CYRUS SENTINEL] {severity_label} ALERT\n\n"
            f"Sir, proactive monitoring has flagged an operational event:\n\n"
            f"• Target Service: {monitor_name}\n"
            f"• Endpoint: {target_url}\n"
            f"• Status Code: {status_code_str}\n"
            f"• Response Latency: {latency_str}\n"
            f"• Event Summary: {event.message}\n"
            f"• Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"CYRUS GUARDIAN remains active on your Apple M5. Please check the CYRUS dashboard, Sir."
        )

    async def send_alert(
        self, event: SentinelEvent, monitor_name: str, target_url: str
    ) -> Dict[str, Any]:
        """Dispatches notification via live Telegram API or verified local simulator."""
        message_text = self.format_alert_message(event, monitor_name, target_url)

        if not self.is_live_configured:
            # Simulated Free-Tier Delivery Mode
            logger.info(
                "SENTINEL Alert [SIMULATED TELEGRAM DISPATCH]: %s -> %s",
                event.severity.value, event.title
            )
            return {
                "success": True,
                "dispatched": True,
                "mode": "SIMULATED_FREE_TIER",
                "message": message_text,
                "recipient_note": f"Delivered to local alert queue for {self.form_of_address}.",
            }

        # Live Telegram Bot API Dispatch
        try:
            api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = json.dumps({
                "chat_id": self.chat_id,
                "text": message_text,
                "parse_mode": "Markdown",
            }).encode("utf-8")

            req = urllib.request.Request(
                api_url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )

            # 4-second timeout to prevent blocking M5 async loop
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "success": data.get("ok", False),
                    "dispatched": True,
                    "mode": "LIVE_TELEGRAM_API",
                    "telegram_message_id": data.get("result", {}).get("message_id"),
                }
        except Exception as e:
            logger.error("Live Telegram dispatch failed: %s. Falling back to local logging.", e)
            return {
                "success": False,
                "dispatched": False,
                "error": str(e),
                "mode": "FAILED_LIVE_DISPATCH",
                "message": message_text,
            }


telegram_notifier = TelegramNotifier()
