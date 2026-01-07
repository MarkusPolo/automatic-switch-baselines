from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVendor(ABC):
    """
    Base interface for all vendor plugins.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor name (e.g., Cisco, HP, Aruba)."""
        pass

    @abstractmethod
    async def bootstrap_config(self, params: Dict[str, Any]) -> str:
        """
        Generate baseline configuration commands.
        """
        pass

    @abstractmethod
    async def verify_connectivity(self) -> bool:
        """
        Check if the device is reachable.
        """
        pass
