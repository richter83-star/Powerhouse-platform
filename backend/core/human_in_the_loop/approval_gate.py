"""
Approval Gate: Defines and enforces the HITL approval model.

Three modes (set via HITL_MODE in config/settings.py):

  gate     – Synchronous gate.  Execution BLOCKS until a human approves or the
             timeout elapses.  On timeout the configured auto-approval policy
             applies (approve or reject).
             Pipeline: task → reasoning → agent selection → [WAIT] → execution

  audit    – Asynchronous logging.  Execution proceeds immediately; the
             approval request is recorded for post-hoc human review.
             Pipeline: task → ... → execution → [LOG FOR REVIEW]

  disabled – No HITL.  Requests are silently accepted; the audit trail still
             records every decision for debugging.

Trusted agents (read-only, low-risk) can be marked to skip the gate even in
``gate`` mode.

Audit trail:
    Regardless of mode, every ApprovalRequest is appended to the in-memory
    ``ApprovalGate.audit_trail`` list and can be exported via get_audit_trail().
    Wire this to a persistent store (DB, message queue) in production.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class HITLMode(str, Enum):
    """Operating mode for the approval gate."""
    GATE = "gate"
    AUDIT = "audit"
    DISABLED = "disabled"


class ApprovalStatus(str, Enum):
    """Outcome of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"    # Trusted agent or disabled mode


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ApprovalRequest:
    """
    Everything a human reviewer needs to make an approval decision.
    """
    request_id: str
    task: str
    reasoning_summary: str          # Why the system wants to run this
    agent_name: str
    agent_confidence: float         # 0.0 – 1.0
    estimated_impact: str           # "low" | "medium" | "high"
    causal_context: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None
    requester: str = "orchestrator"
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Mutable state updated by the gate
    status: ApprovalStatus = ApprovalStatus.PENDING
    resolved_at: Optional[datetime] = None
    resolver: Optional[str] = None   # human_id or "auto_timeout"
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task": self.task,
            "reasoning_summary": self.reasoning_summary,
            "agent_name": self.agent_name,
            "agent_confidence": self.agent_confidence,
            "estimated_impact": self.estimated_impact,
            "causal_context": self.causal_context,
            "run_id": self.run_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolver": self.resolver,
            "rejection_reason": self.rejection_reason,
        }


# ApprovalHandler: callable that receives an ApprovalRequest and either
# returns True (approved), False (rejected), or None (no decision yet).
ApprovalHandler = Callable[[ApprovalRequest], Optional[bool]]


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

class ApprovalGate:
    """
    Enforces the HITL approval model across three modes.

    Construction example::

        gate = ApprovalGate(
            mode=HITLMode.GATE,
            timeout_seconds=30.0,
            auto_approve_on_timeout=True,
            trusted_agents={"readonly_agent", "monitoring_agent"},
        )

    Gate-mode usage::

        req = gate.create_request(
            task="...", reasoning_summary="...",
            agent_name="react_agent", agent_confidence=0.9,
            estimated_impact="medium",
        )
        approved = gate.request_approval(req)
        if not approved:
            raise PermissionError("Human rejected execution")

    Submitting a decision (from webhook / UI)::

        gate.submit_decision(request_id, approved=True, resolver="user@example.com")
    """

    def __init__(
        self,
        mode: HITLMode = HITLMode.AUDIT,
        timeout_seconds: float = 60.0,
        auto_approve_on_timeout: bool = True,
        trusted_agents: Optional[set] = None,
        approval_handler: Optional[ApprovalHandler] = None,
        audit_log_path: Optional[str] = None,
    ) -> None:
        """
        Args:
            mode: Gate, audit, or disabled.
            timeout_seconds: How long gate mode waits for a human response.
            auto_approve_on_timeout: When True, an unanswered request is
                approved after timeout.  When False it is rejected.
            trusted_agents: Set of agent names that bypass gate checks.
            approval_handler: Optional synchronous callback called once per
                request in gate mode (e.g. webhook POST, Slack message).
                Return True to approve immediately, False to reject, None to
                rely on the timeout / poll loop.
            audit_log_path: Optional path to a JSONL file for persistent audit
                logging.  When set, every resolved request is appended to the
                file and existing records are loaded at construction time so
                history survives server restarts.
        """
        self.mode = HITLMode(mode) if not isinstance(mode, HITLMode) else mode
        self.timeout_seconds = timeout_seconds
        self.auto_approve_on_timeout = auto_approve_on_timeout
        self.trusted_agents: set = trusted_agents or set()
        self.approval_handler = approval_handler
        self._audit_log_path: Optional[Path] = (
            Path(audit_log_path) if audit_log_path else None
        )

        # Request store: request_id → ApprovalRequest
        self._pending: Dict[str, ApprovalRequest] = {}
        # Thread-safe event per request so gate mode can block
        self._events: Dict[str, threading.Event] = {}

        # Audit trail (all requests ever created)
        self.audit_trail: List[ApprovalRequest] = []

        # Load persisted records if log file exists
        if self._audit_log_path:
            self._load_audit_log()

        logger.info(
            "ApprovalGate initialised: mode=%s, timeout=%.1fs, "
            "auto_approve_on_timeout=%s, trusted_agents=%s",
            self.mode.value,
            self.timeout_seconds,
            self.auto_approve_on_timeout,
            self.trusted_agents,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_request(
        self,
        task: str,
        reasoning_summary: str,
        agent_name: str,
        agent_confidence: float = 1.0,
        estimated_impact: str = "medium",
        causal_context: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> ApprovalRequest:
        """Build and register a new ApprovalRequest."""
        req = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            task=task,
            reasoning_summary=reasoning_summary,
            agent_name=agent_name,
            agent_confidence=agent_confidence,
            estimated_impact=estimated_impact,
            causal_context=causal_context,
            run_id=run_id,
        )
        self._pending[req.request_id] = req
        self._events[req.request_id] = threading.Event()
        self.audit_trail.append(req)
        logger.debug("ApprovalRequest created: %s", req.request_id)
        try:
            from core.monitoring.metrics import hitl_requests_total
            hitl_requests_total.labels(
                mode=self.mode.value, impact=estimated_impact
            ).inc()
        except Exception:
            pass
        return req

    def request_approval(self, req: ApprovalRequest) -> bool:
        """
        Enforce the approval policy for *req*.

        Returns:
            True if execution is approved, False if rejected.

        Behaviour by mode:
        - ``disabled``: always True (skipped).
        - ``audit``: always True, request logged asynchronously.
        - ``gate``: blocks until human decides or timeout, then
          auto-approves / auto-rejects per configuration.
        """
        # --- Trusted agent bypass ---
        if req.agent_name in self.trusted_agents:
            self._resolve(req, ApprovalStatus.SKIPPED, resolver="trusted_agent_bypass")
            logger.info("Trusted agent '%s' skipped approval gate", req.agent_name)
            return True

        # --- Disabled mode ---
        if self.mode == HITLMode.DISABLED:
            self._resolve(req, ApprovalStatus.SKIPPED, resolver="mode_disabled")
            return True

        # --- Audit mode ---
        if self.mode == HITLMode.AUDIT:
            # Non-blocking: mark as approved immediately, log for review
            self._resolve(req, ApprovalStatus.APPROVED, resolver="audit_mode_auto")
            logger.info(
                "[AUDIT] Logged approval request %s for '%s' (task: %.60s…)",
                req.request_id,
                req.agent_name,
                req.task,
            )
            return True

        # --- Gate mode ---
        return self._gate_wait(req)

    def submit_decision(
        self,
        request_id: str,
        approved: bool,
        resolver: str = "human",
        rejection_reason: Optional[str] = None,
    ) -> bool:
        """
        Submit a human decision for a pending request.

        Call this from your webhook handler, UI callback, or test harness.

        Returns:
            True if the request was found and updated; False if unknown.
        """
        req = self._pending.get(request_id)
        if req is None:
            logger.warning("submit_decision: unknown request_id=%s", request_id)
            return False

        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        req.rejection_reason = rejection_reason
        self._resolve(req, status, resolver=resolver)

        # Unblock the waiting thread in gate mode
        event = self._events.get(request_id)
        if event:
            event.set()

        logger.info(
            "Decision submitted for %s: %s by '%s'",
            request_id,
            status.value,
            resolver,
        )
        return True

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Return all unresolved requests as serialisable dicts."""
        return [
            req.to_dict()
            for req in self._pending.values()
            if req.status == ApprovalStatus.PENDING
        ]

    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return the most recent *limit* audit records."""
        return [req.to_dict() for req in self.audit_trail[-limit:]]

    def add_trusted_agent(self, agent_name: str) -> None:
        """Mark an agent as trusted (exempt from gate checks)."""
        self.trusted_agents.add(agent_name)
        logger.info("Agent '%s' added to trusted set", agent_name)

    def remove_trusted_agent(self, agent_name: str) -> None:
        """Remove an agent from the trusted set."""
        self.trusted_agents.discard(agent_name)

    def get_statistics(self) -> Dict[str, Any]:
        """Summary statistics for monitoring."""
        total = len(self.audit_trail)
        by_status: Dict[str, int] = {}
        for req in self.audit_trail:
            key = req.status.value
            by_status[key] = by_status.get(key, 0) + 1
        return {
            "mode": self.mode.value,
            "total_requests": total,
            "pending": len(self.get_pending_requests()),
            "by_status": by_status,
            "trusted_agents": list(self.trusted_agents),
            "timeout_seconds": self.timeout_seconds,
            "auto_approve_on_timeout": self.auto_approve_on_timeout,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _gate_wait(self, req: ApprovalRequest) -> bool:
        """
        Block until a human submits a decision or the timeout elapses.
        """
        # Notify external handler (webhook / message queue stub)
        if self.approval_handler:
            try:
                immediate_decision = self.approval_handler(req)
                if immediate_decision is not None:
                    status = (
                        ApprovalStatus.APPROVED
                        if immediate_decision
                        else ApprovalStatus.REJECTED
                    )
                    self._resolve(req, status, resolver="approval_handler")
                    return immediate_decision
            except Exception as exc:
                logger.error("approval_handler raised: %s", exc, exc_info=True)

        event = self._events[req.request_id]
        logger.info(
            "[GATE] Waiting up to %.1fs for approval of request %s "
            "(agent='%s', impact=%s)",
            self.timeout_seconds,
            req.request_id,
            req.agent_name,
            req.estimated_impact,
        )

        signalled = event.wait(timeout=self.timeout_seconds)

        if signalled:
            # Decision was submitted via submit_decision()
            return req.status == ApprovalStatus.APPROVED

        # Timeout
        if self.auto_approve_on_timeout:
            self._resolve(req, ApprovalStatus.APPROVED, resolver="auto_timeout")
            logger.warning(
                "[GATE] Timeout for %s – auto-approved", req.request_id
            )
            return True
        else:
            self._resolve(
                req,
                ApprovalStatus.TIMED_OUT,
                resolver="auto_timeout",
                rejection_reason="No human response within timeout",
            )
            logger.warning(
                "[GATE] Timeout for %s – auto-rejected", req.request_id
            )
            return False

    def _resolve(
        self,
        req: ApprovalRequest,
        status: ApprovalStatus,
        resolver: str = "system",
        rejection_reason: Optional[str] = None,
    ) -> None:
        """Update request status, remove from pending dict, and persist."""
        req.status = status
        req.resolved_at = datetime.utcnow()
        req.resolver = resolver
        if rejection_reason:
            req.rejection_reason = rejection_reason
        self._pending.pop(req.request_id, None)
        self._events.pop(req.request_id, None)
        # Append to on-disk audit log (non-blocking best-effort)
        self._append_audit_log(req)
        try:
            from core.monitoring.metrics import hitl_resolved_total
            hitl_resolved_total.labels(
                mode=self.mode.value,
                status=status.value,
                resolver=resolver,
            ).inc()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _append_audit_log(self, req: ApprovalRequest) -> None:
        """Append a single resolved request to the JSONL audit log."""
        if not self._audit_log_path:
            return
        try:
            self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(req.to_dict()) + "\n")
        except Exception as exc:
            logger.warning("Failed to append audit log: %s", exc)

    def _load_audit_log(self) -> None:
        """Load persisted audit records from the JSONL file into audit_trail."""
        if not self._audit_log_path or not self._audit_log_path.exists():
            return
        loaded = 0
        try:
            with self._audit_log_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        req = ApprovalRequest(
                            request_id=record["request_id"],
                            task=record["task"],
                            reasoning_summary=record.get("reasoning_summary", ""),
                            agent_name=record.get("agent_name", "unknown"),
                            agent_confidence=record.get("agent_confidence", 1.0),
                            estimated_impact=record.get("estimated_impact", "medium"),
                            causal_context=record.get("causal_context"),
                            run_id=record.get("run_id"),
                            requester=record.get("requester", "orchestrator"),
                            created_at=datetime.fromisoformat(
                                record.get("created_at", datetime.utcnow().isoformat())
                            ),
                            status=ApprovalStatus(record.get("status", "approved")),
                            resolved_at=(
                                datetime.fromisoformat(record["resolved_at"])
                                if record.get("resolved_at") else None
                            ),
                            resolver=record.get("resolver"),
                            rejection_reason=record.get("rejection_reason"),
                        )
                        self.audit_trail.append(req)
                        loaded += 1
                    except Exception as exc:
                        logger.warning("Skipping malformed audit record: %s", exc)
        except Exception as exc:
            logger.warning("Failed to load audit log from %s: %s",
                           self._audit_log_path, exc)
        if loaded:
            logger.info("Loaded %d HITL audit records from %s",
                        loaded, self._audit_log_path)

    def flush_audit_log(self) -> None:
        """
        Rewrite the entire in-memory audit trail to disk.

        Useful at shutdown to ensure all records are persisted, including any
        that were created but not yet resolved (e.g. still-pending requests).
        """
        if not self._audit_log_path:
            return
        try:
            self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_log_path.open("w", encoding="utf-8") as fh:
                for req in self.audit_trail:
                    fh.write(json.dumps(req.to_dict()) + "\n")
            logger.info("Flushed %d HITL audit records to %s",
                        len(self.audit_trail), self._audit_log_path)
        except Exception as exc:
            logger.error("Failed to flush audit log: %s", exc)


# ---------------------------------------------------------------------------
# Default instance factory
# ---------------------------------------------------------------------------

def build_approval_gate(
    mode: str = "audit",
    timeout_seconds: float = 60.0,
    auto_approve_on_timeout: bool = True,
    trusted_agents: Optional[set] = None,
    approval_handler: Optional[ApprovalHandler] = None,
    audit_log_path: Optional[str] = None,
) -> ApprovalGate:
    """
    Factory that reads sensible defaults from settings.

    Prefer instantiating ``ApprovalGate`` directly for full control.

    Args:
        audit_log_path: Path to a JSONL file for persistent audit logging.
            When set, records are loaded on startup and appended on every
            resolution so history survives server restarts.
    """
    return ApprovalGate(
        mode=HITLMode(mode),
        timeout_seconds=timeout_seconds,
        auto_approve_on_timeout=auto_approve_on_timeout,
        trusted_agents=trusted_agents,
        approval_handler=approval_handler,
        audit_log_path=audit_log_path,
    )
