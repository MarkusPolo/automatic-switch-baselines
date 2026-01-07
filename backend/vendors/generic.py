import os
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from .base import BaseVendor, CommandBlock

class GenericVendor(BaseVendor):
    @property
    def vendor_id(self) -> str:
        return "generic"

    def detect(self, transcript: str) -> float:
        return 0.1 # Very low confidence for generic

    async def get_bootstrap_commands(self, device_data: Dict[str, Any]) -> List[CommandBlock]:
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "generic")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("bootstrap.j2")
        rendered = template.render(**device_data)
        
        return [
            CommandBlock(
                name="Bootstrap",
                commands=[line for line in rendered.split("\n") if line.strip()],
                critical=True
            )
        ]

    async def get_save_commands(self, device_data: Dict[str, Any]) -> List[str]:
        return ["write", "copy run start"]

    async def get_verify_commands(self, device_data: Dict[str, Any]) -> List[str]:
        return ["show ip interface brief"]

    def parse_verify(self, output: str) -> Dict[str, Any]:
        return {"success": True, "details": "Generic verification complete"}
