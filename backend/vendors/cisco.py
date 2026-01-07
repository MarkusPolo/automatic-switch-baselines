import os
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from .base import BaseVendor, CommandBlock

class CiscoVendor(BaseVendor):
    @property
    def vendor_id(self) -> str:
        return "cisco"

    def detect(self, transcript: str) -> float:
        low_transcript = transcript.lower()
        if "cisco" in low_transcript or "ios" in low_transcript:
            return 0.9
        return 0.0

    async def get_bootstrap_commands(self, device_data: Dict[str, Any]) -> List[CommandBlock]:
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "cisco")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("bootstrap.j2")
        rendered = template.render(**device_data)
        
        # Breakdown into blocks for better control
        blocks = []
        lines = rendered.split("\n")
        
        # Filter out empty lines
        clean_lines = [l for l in lines if l.strip()]
        
        # Simple heuristics for blocks (can be improved)
        # Block 1: Enter Config
        blocks.append(CommandBlock(
            name="Enter Configuration",
            commands=["conf t"],
            critical=True
        ))
        
        # Block 2: Main Config
        main_cmds = [l for l in clean_lines if l.strip() not in ["conf t", "end", "write memory"]]
        blocks.append(CommandBlock(
            name="Apply Baseline",
            commands=main_cmds,
            critical=True
        ))
        
        # Block 3: Exit and Save
        blocks.append(CommandBlock(
            name="Save Configuration",
            commands=["end", "write memory"],
            critical=False
        ))
        
        return blocks

    async def get_save_commands(self, device_data: Dict[str, Any]) -> List[str]:
        return ["write memory"]

    async def get_verify_commands(self, device_data: Dict[str, Any]) -> List[str]:
        return ["show ip interface brief", "show version"]

    def parse_verify(self, output: str) -> Dict[str, Any]:
        success = "up" in output.lower()
        return {"success": success, "details": f"Interfaces found: {success}"}
