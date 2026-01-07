import asyncio
import serial
from enum import Enum
from typing import Optional

class SessionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    DETECTING = "detecting"
    CONFIGURING = "configuring"
    VERIFYING = "verifying"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"

class SessionEngine:
    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.state = SessionState.DISCONNECTED
        self.serial_conn: Optional[serial.Serial] = None
        self.log = []

    async def connect(self):
        self.state = SessionState.CONNECTING
        self.log_event(f"Connecting to {self.port}...")
        # In a real environment, this would use pyserial
        # self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
        await asyncio.sleep(1) # Mock delay
        self.state = SessionState.DETECTING
        self.log_event("Connected. Detecting device...")

    async def run_sequence(self, config_commands: list):
        try:
            await self.connect()
            # 1. Detect Vendor/Prompt
            # 2. Enter Enable/Config Mode
            # 3. Apply Commands
            # 4. Verify
            # 5. Save
            self.state = SessionState.CONFIGURING
            for cmd in config_commands:
                self.log_event(f"Applying command: {cmd}")
                await asyncio.sleep(0.5)
            
            self.state = SessionState.COMPLETED
            self.log_event("Configuration sequence completed successfully.")
        except Exception as e:
            self.state = SessionState.FAILED
            self.log_event(f"Error: {str(e)}")

    def log_event(self, message: str):
        self.log.append(f"{self.port}: {message}")
        print(f"[{self.state.value}] {self.port}: {message}")
