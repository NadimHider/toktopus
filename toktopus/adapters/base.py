"""
Base Agent Adapter interface for toktopus.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseAgentAdapter(ABC):
    """Abstract base class that all AI coding agent telemetry adapters implement."""

    @abstractmethod
    def get_agent_name(self) -> str:
        """Name of the AI coding agent (e.g. 'Antigravity 2.0', 'Claude Code')."""
        pass

    @abstractmethod
    def is_detected(self) -> bool:
        """Check if this agent's configuration or files exist on the system."""
        pass

    @abstractmethod
    def get_active_session_id(self) -> Optional[str]:
        """Return ID of the currently active or newest session."""
        pass

    @abstractmethod
    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Return standard telemetry dictionary:
        {
            "agent_name": str,
            "session_id": str,
            "title": str,
            "model_name": str,
            "max_context_tokens": int,
            "input_tokens": int,
            "output_tokens": int,
            "cache_read_tokens": int,
            "total_tokens": int,
            "cache_efficiency": float,
            "tokens_per_step": int,
            "tokens_per_sec": int,
            "recent_steps_tokens": List[int],
            "recent_steps": List[Dict[str, Any]],
            "active_subagents": List[Dict[str, Any]],
            "is_active": bool,
            "last_modified": float
        }
        """
        pass
