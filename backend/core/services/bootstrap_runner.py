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
from ...vendors.cisco_ios import CiscoIOSVendor  # MVP: explicitly use Cisco for now

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
        self.vendor = CiscoIOSVendor()  # MVP limitation

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
        # For local testing, we might want to override this, but as per requirements:
        # Raspberry Pi uses /dev/port1..16
        
        try:
            repository.update_run_device_status(self.db, self.run_id, self.device_id, "RUNNING")
            await self.log_event("INFO", f"Connecting to {port_path}")
            
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
            }
            commands = await self.vendor.bootstrap_config(config_params)
            
            # Step 3: Apply Commands
            await self.log_event("INFO", "Applying configuration commands...")
            for cmd in commands.split("\n"):
                if not cmd.strip():
                    continue
                
                await asyncio.to_thread(self.session.send_line, cmd)
                output = await asyncio.to_thread(self.session.read_until_prompt)
                
                # Check for errors
                for pattern in ERROR_PATTERNS:
                    if pattern.search(output):
                        await self.log_event("ERROR", f"Command failed: {cmd}", raw=output)
                        # Decide if fail-fast or continue. Requirements say fail-fast for critical items.
                        # For MVP, let's mark as failed and stop.
                        repository.update_run_device_status(self.db, self.run_id, self.device_id, "FAILED", error_message=f"CLI Error in command: {cmd}")
                        return

            # Step 4: Verify
            await self.log_event("INFO", "Verifying configuration...")
            # Simple verification for MVP: check if hostname changed
            await asyncio.to_thread(self.session.send_line, "")
            final_prompt = await asyncio.to_thread(self.session.read_until_prompt)
            if self.device.hostname in final_prompt:
                await self.log_event("INFO", "Verification successful (hostname detected in prompt)")
                repository.update_run_device_status(self.db, self.run_id, self.device_id, "VERIFIED")
            else:
                await self.log_event("WARNING", "Verification failed (hostname not in prompt)", raw=final_prompt)
                repository.update_run_device_status(self.db, self.run_id, self.device_id, "FAILED", error_message="Verification failed")

        except Exception as e:
            await self.log_event("ERROR", f"Execution error: {str(e)}")
            repository.update_run_device_status(self.db, self.run_id, self.device_id, "FAILED", error_message=str(e))
        finally:
            if self.session:
                await asyncio.to_thread(self.session.close)
