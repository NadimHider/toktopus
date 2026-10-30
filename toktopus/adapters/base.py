from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgentAdapter(ABC):
    @abstractmethod
    def get_agent_name(self) -> str:
        pass

    @abstractmethod
    def is_detected(self) -> bool:
        pass

    @abstractmethod
    def get_active_session_id(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_session_telemetry(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        pass
