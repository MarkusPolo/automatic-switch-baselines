from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class CommandBlock(BaseModel):
    name: str
    commands: List[str]
    expect_prompt: Optional[str] = None
    critical: bool = True

class BaseVendor(ABC):
    @property
    @abstractmethod
    def vendor_id(self) -> str:
        """Unique ID for the vendor (e.g., 'cisco_ios')."""
        pass

    @abstractmethod
    def detect(self, transcript: str) -> float:
        """
        Estimate confidence (0.0 to 1.0) that this vendor matches the transcript.
        """
        pass

    @abstractmethod
    async def get_bootstrap_commands(self, device_data: Dict[str, Any]) -> List[CommandBlock]:
        """
        Generate baseline configuration command blocks using templates.
        """
        pass

    @abstractmethod
    async def get_save_commands(self, device_data: Dict[str, Any]) -> List[str]:
        """
        Generate commands to save configuration.
        """
        pass

    @abstractmethod
    async def get_verify_commands(self, device_data: Dict[str, Any]) -> List[str]:
        """
        Generate commands to verify configuration.
        """
        pass

    @abstractmethod
    def parse_verify(self, output: str) -> Dict[str, Any]:
        """
        Parse verification output. Returns {'success': bool, 'details': str}.
        """
        pass
