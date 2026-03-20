"""
HITL Webhook Handler.

Provides a factory that builds an ``ApprovalHandler`` callback suitable for
passing to ``ApprovalGate(approval_handler=...)``.

When triggered in gate mode the handler:
1. Serialises the ``ApprovalRequest`` to a compact JSON payload that includes
   a ``decide_url`` (the ``/hitl/{request_id}/decide`` endpoint) so the
   receiver can approve or reject without polling.
2. Signs the payload with HMAC-SHA256 using the configured secret (when set)
   and attaches the signature in the ``X-Powerhouse-Signature`` header.
3. POSTs the payload with a short timeout (5 s) and logs the outcome.
4. Returns ``None`` so the gate continues to block until a human calls the
   decide endpoint or the timeout elapses — the webhook is **notify-only**
   and never makes an approval decision itself.

Usage in ph_server.py::

    from core.human_in_the_loop.webhook_handler import build_webhook_handler

    handler = build_webhook_handler(
        url=settings.hitl_webhook_url,
        secret=settings.hitl_webhook_secret,
        server_base_url="http://localhost:8000",
    )
    gate = build_approval_gate(..., approval_handler=handler)
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def build_webhook_handler(
    url: str,
    secret: Optional[str] = None,
    server_base_url: str = "http://localhost:8000",
    timeout_seconds: float = 5.0,
):
    """
    Return an ``ApprovalHandler`` that notifies *url* when the HITL gate fires.

    Args:
        url: Full HTTP(S) URL to POST the notification to.
        secret: Optional HMAC-SHA256 signing secret.  When provided, the
            ``X-Powerhouse-Signature: sha256=<hex>`` header is added to every
            request so the receiver can verify authenticity.
        server_base_url: Base URL of this server, used to build the
            ``decide_url`` included in the payload (default: localhost:8000).
        timeout_seconds: HTTP connect+read timeout in seconds (default: 5).

    Returns:
        An ``ApprovalHandler`` callable — returns ``None`` (notify-only).
    """
    if not url:
        raise ValueError("url must be a non-empty string")

    # Lazy import so httpx is only required when a webhook is configured
    try:
        import httpx
        _httpx_available = True
    except ImportError:
        _httpx_available = False
        logger.warning(
            "httpx not installed — webhook notifications will be logged only. "
            "Install with: pip install httpx"
        )

    def _handler(req):  # type: ApprovalRequest -> Optional[bool]
        """Post a notification and return None (no immediate decision)."""
        decide_url = f"{server_base_url.rstrip('/')}/hitl/{req.request_id}/decide"

        payload = {
            "request_id": req.request_id,
            "task": req.task,
            "agent_name": req.agent_name,
            "reasoning_summary": req.reasoning_summary,
            "estimated_impact": req.estimated_impact,
            "agent_confidence": req.agent_confidence,
            "run_id": req.run_id,
            "requester": req.requester,
            "created_at": req.created_at.isoformat(),
            "decide_url": decide_url,
        }

        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if secret:
            sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-Powerhouse-Signature"] = f"sha256={sig}"

        if not _httpx_available:
            logger.info(
                "[HITL webhook] httpx unavailable — would POST to %s: %s",
                url,
                payload,
            )
            return None

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(url, content=body, headers=headers)
            logger.info(
                "[HITL webhook] POST %s → HTTP %d (request_id=%s)",
                url,
                response.status_code,
                req.request_id,
            )
        except Exception as exc:
            logger.error(
                "[HITL webhook] POST to %s failed: %s (request_id=%s)",
                url,
                exc,
                req.request_id,
            )

        # Always return None — the handler is notify-only
        return None

    return _handler
