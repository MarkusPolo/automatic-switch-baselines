import os
import serial
import time
import re
from typing import List, Optional

class SerialSession:
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    def open(self):
        if not self.ser:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )
        if not self.ser.is_open:
            self.ser.open()

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

    def send_line(self, line: str):
        if not self.ser:
            raise RuntimeError("Serial port not open")
        self.ser.write((line + "\n").encode("ascii"))
        self.ser.flush()

    def read_until_prompt(self, prompt_regex: str = r"[#>]", timeout: Optional[float] = None) -> str:
        if not self.ser:
            raise RuntimeError("Serial port not open")
        
        start_time = time.time()
        effective_timeout = timeout if timeout is not None else self.timeout
        output = ""
        
        while True:
            if self.ser.in_waiting > 0:
                char = self.ser.read(1).decode("ascii", errors="ignore")
                output += char
                if re.search(prompt_regex, output):
                    break
            
            if time.time() - start_time > effective_timeout:
                break
            time.sleep(0.01)
            
        return output

    def flush(self):
        if self.ser:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()



def discover_ports(base_path: str = "/dev/port") -> List[str]:
    """
    Finds symlinks like /dev/port1, /dev/port2, ..., /dev/port16.
    """
    available_ports = []
    for i in range(1, 17):
        port_path = f"{base_path}{i}"
        if os.path.exists(port_path):
            available_ports.append(port_path)
    return available_ports
