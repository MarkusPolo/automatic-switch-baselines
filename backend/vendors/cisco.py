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

    async def get_init_commands(self) -> List[str]:
        return ["terminal length 0"]

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
            commands=["en", "conf t"],
            critical=True
        ))
        
        # Block 2: Main Config
        main_cmds = [l for l in clean_lines if l.strip() not in ["en", "conf t", "end", "write memory"]]
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
        hostname = device_data.get("hostname")
        
        tasks = []
        issues = []
        
        # 1. Hostname Check
        if hostname:
            # Simple check if hostname appears in prompt or config
             # Heuristic: Prompt should change to hostname
            prompt_pattern = re.compile(rf"^{hostname}[>#]", re.MULTILINE)
            active_hostname = "Unknown"
            # Try to find the prompt in the raw output
            match = prompt_pattern.search(output)
            passed = bool(match) or hostname in output
            
            tasks.append({
                "name": "Verify Hostname",
                "status": "success" if passed else "failed",
                "message": f"Hostname set to {hostname}" if passed else "Hostname mismatch",
                "code": "HOSTNAME_MATCH" if passed else "HOSTNAME_MISMATCH"
            })
            if not passed: issues.append("Hostname mismatch")

        # 2. IP Check
        if expected_ip:
            passed = expected_ip in output
            tasks.append({
                "name": "Verify IP Address",
                "status": "success" if passed else "failed",
                "message": f"IP {expected_ip} found" if passed else f"IP {expected_ip} not found",
                "code": "IP_MATCH" if passed else "IP_MISMATCH"
            })
            if not passed: issues.append(f"IP {expected_ip} missing")
            
        # 3. VLAN Check
        if expected_vlan:
            # Allow optional leading whitespace for tests/indented output
            # Look for the VLAN ID anywhere on the line, followed by whitespace, then 'active'
            vlan_pattern = re.compile(rf"(^|\s){expected_vlan}\s+.*\bactive\b", re.MULTILINE | re.IGNORECASE)
            passed = bool(vlan_pattern.search(output))
            
            tasks.append({
                "name": f"Verify VLAN {expected_vlan}",
                "status": "success" if passed else "failed",
                "message": f"VLAN {expected_vlan} is active" if passed else f"VLAN {expected_vlan} not active/found",
                "code": "VLAN_MATCH" if passed else "VLAN_MISMATCH"
            })
            if not passed: issues.append(f"VLAN {expected_vlan} missing")
        
        # 4. SSH Check
        ssh_passed = "SSH Enabled" in output or "SSH ver" in output
        tasks.append({
            "name": "Verify SSH",
            "status": "success" if ssh_passed else "failed",
            "message": "SSH is enabled" if ssh_passed else "SSH disabled",
            "code": "SSH_ENABLED" if ssh_passed else "SSH_DISABLED"
        })
        if not ssh_passed: issues.append("SSH disabled")
            
        success = len(issues) == 0
        details = "All checks passed" if success else "; ".join(issues)
        
        return {"success": success, "details": details, "tasks": tasks}
