"""
Agent Communication Protocol
============================

This module provides the core infrastructure for inter-agent communication,
enabling agents to discover, message, and coordinate with each other regardless
of which subset is deployed.

Key Components:
- MessageBus: Pub/sub message routing system
- AgentRegistry: Service discovery for agents
- SharedContext: Shared state management
- Message: Standardized message format
"""

from .message import Message, MessageType
from .message_bus import MessageBus
from .agent_registry import AgentRegistry
from .shared_context import SharedContext
from .protocol import CommunicationProtocol

__all__ = [
    "Message",
    "MessageType",
    "MessageBus",
    "AgentRegistry",
    "SharedContext",
    "CommunicationProtocol"
]
