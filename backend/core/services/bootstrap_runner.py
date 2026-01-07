import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import re

from ...infra.serial import SerialSession
from ...infra import repository, database
from ...infra.database import get_db
from .. import models
from ...vendors.loader import get_vendor

logger = logging.getLogger(__name__)

ERROR_PATTERNS = [
    re.compile(r"Invalid input", re.IGNORECASE),
    re.compile(r"Ambiguous command", re.IGNORECASE),
    re.compile(r"Incomplete command", re.IGNORECASE),
    re.compile(r"% Error", re.IGNORECASE),
]

class BootstrapRunner:
    def __init__(self, db: Session, run_id: int, device_id: int):
        self.db = db
        self.run_id = run_id
        self.device_id = device_id
        self.device = repository.get_device_by_id(db, device_id)
        self.session: Optional[SerialSession] = None
        vendor_id = "generic"
        if self.device and self.device.vendor:
            vendor_id = self.device.vendor
        self.vendor = get_vendor(vendor_id)

    async def log_event(self, level: str, message: str, raw: Optional[str] = None):
        event = database.DBEventLog(
            run_id=self.run_id,
            device_id=self.device_id,
            port=self.device.port,
            level=level,
            message=message,
            raw=raw,
            ts=datetime.now(timezone.utc)
        )
        self.db.add(event)
        self.db.commit()

    async def run(self):
        if not self.device or not self.device.port:
            await self.log_event("ERROR", "Device or port not specified")
            return

        port_path = f"/dev/port{self.device.port}"
        
        try:
            repository.update_run_device_status(self.db, self.run_id, self.device_id, "RUNNING")
            await self.log_event("INFO", f"Connecting to {port_path} as {self.vendor.vendor_id}")
            
            # Using asyncio.to_thread for blocking serial I/O
            self.session = SerialSession(port_path)
            await asyncio.to_thread(self.session.open)
            
            # Step 1: Connect and Sync Prompt
            await self.log_event("INFO", "Synchronizing prompt...")
            await asyncio.to_thread(self.session.send_line, "")
            prompt = await asyncio.to_thread(self.session.read_until_prompt)
            await self.log_event("DEBUG", f"Initial prompt detected", raw=prompt)

            # Step 2: Generate Config
            config_params = {
                "hostname": self.device.hostname,
                "mgmt_ip": self.device.mgmt_ip,
                "mgmt_mask": self.device.mask,
                "gateway": self.device.gateway,
                "mgmt_vlan": self.device.mgmt_vlan,
            }
            blocks = await self.vendor.get_bootstrap_commands(config_params)
            
            # Step 3: Apply Command Blocks
            await self.log_event("INFO", f"Applying {len(blocks)} configuration blocks...")
            for block in blocks:
                await self.log_event("INFO", f"Running block: {block.name}")
                for cmd in block.commands:
                    if not cmd.strip():
                        continue
                    
                    await asyncio.to_thread(self.session.send_line, cmd)
                    output = await asyncio.to_thread(self.session.read_until_prompt)
                    
                    # Check for errors
                    for pattern in ERROR_PATTERNS:
                        if pattern.search(output):
                            await self.log_event("ERROR", f"Command failed: {cmd}", raw=output)
                            if block.critical:
                                repository.update_run_device_status(self.db, self.run_id, self.device_id, "FAILED", error_message=f"Critical Error in {block.name}: {cmd}")
                                return
                            else:
                                await self.log_event("WARNING", f"Ignoring non-critical error in {block.name}")

            # Step 4: Verify
            await self.log_event("INFO", "Verifying configuration...")
            verify_cmds = await self.vendor.get_verify_commands(config_params)
            full_output = ""
            for v_cmd in verify_cmds:
                await asyncio.to_thread(self.session.send_line, v_cmd)
                full_output += await asyncio.to_thread(self.session.read_until_prompt)

            verify_result = self.vendor.parse_verify(full_output)
            if verify_result['success']:
                await self.log_event("INFO", f"Verification successful: {verify_result['details']}")
                
                # Step 5: Save
                await self.log_event("INFO", "Saving configuration...")
                save_cmds = await self.vendor.get_save_commands(config_params)
                for s_cmd in save_cmds:
                    await asyncio.to_thread(self.session.send_line, s_cmd)
                    await asyncio.to_thread(self.session.read_until_prompt)
                
                repository.update_run_device_status(self.db, self.run_id, self.device_id, "VERIFIED")
            else:
                await self.log_event("ERROR", f"Verification failed: {verify_result['details']}", raw=full_output)
                repository.update_run_device_status(self.db, self.run_id, self.device_id, "FAILED", error_message=f"Verification failed: {verify_result['details']}")

        except Exception as e:
            await self.log_event("ERROR", f"Execution error: {str(e)}")
            repository.update_run_device_status(self.db, self.run_id, self.device_id, "FAILED", error_message=str(e))
        finally:
            if self.session:
                await asyncio.to_thread(self.session.close)
