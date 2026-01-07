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
        vlan = device_data.get("mgmt_vlan")
        cmds = ["show ip interface brief", "show vlan brief", "show ip ssh"]
        if vlan:
            cmds.append(f"show running-config interface Vlan{vlan}")
        return cmds

    def parse_verify(self, output: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
        import re
        expected_ip = device_data.get("mgmt_ip")
        expected_vlan = device_data.get("mgmt_vlan")
        
        issues = []
        
        # 1. IP Check
        if expected_ip and expected_ip not in output:
            issues.append(f"IP {expected_ip} not found in output")
            
        # 2. VLAN Check
        if expected_vlan:
            # Allow optional leading whitespace for tests/indented output
            vlan_pattern = re.compile(rf"^\s*{expected_vlan}\s+", re.MULTILINE)
            if not vlan_pattern.search(output):
                issues.append(f"VLAN {expected_vlan} not found in 'show vlan brief'")
        
        # 3. SSH Check
        if "SSH Enabled" not in output and "SSH ver" not in output:
            issues.append("SSH does not appear to be enabled")
            
        success = len(issues) == 0
        details = "All checks passed" if success else "; ".join(issues)
        
        return {"success": success, "details": details}
