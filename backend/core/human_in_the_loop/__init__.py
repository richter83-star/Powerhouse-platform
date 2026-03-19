"""
Human-in-the-loop integration modules.

Public API
----------
Feedback / preference learning (existing):
    HumanInTheLoop, HumanFeedback, FeedbackRequest, FeedbackType

Approval gate (new):
    ApprovalGate      – enforces gate | audit | disabled HITL modes
    ApprovalRequest   – per-task approval record (with full audit trail)
    ApprovalStatus    – pending | approved | rejected | timed_out | skipped
    HITLMode          – gate | audit | disabled
    build_approval_gate – convenience factory
"""

from core.human_in_the_loop.human_feedback import (
    HumanInTheLoop,
    HumanFeedback,
    FeedbackRequest,
    FeedbackType,
)

from core.human_in_the_loop.approval_gate import (
    ApprovalGate,
    ApprovalRequest,
    ApprovalStatus,
    HITLMode,
    build_approval_gate,
)

__all__ = [
    # Feedback / preference learning
    "HumanInTheLoop",
    "HumanFeedback",
    "FeedbackRequest",
    "FeedbackType",
    # Approval gate
    "ApprovalGate",
    "ApprovalRequest",
    "ApprovalStatus",
    "HITLMode",
    "build_approval_gate",
]


