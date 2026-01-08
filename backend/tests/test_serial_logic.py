import pytest
from unittest.mock import MagicMock
import time
from backend.infra.serial import SerialSession

class MockSerial:
    def __init__(self):
        self.in_waiting = 0
        self.buffer = b""
        self.is_open = True
        self._output_buffer = b""

    def read(self, size=1):
        if not self.buffer:
            return b""
        data = self.buffer[:size]
        self.buffer = self.buffer[size:]
        self.in_waiting = len(self.buffer)
        return data
    
    def write(self, data):
        self._output_buffer += data
        
    def flush(self):
        pass
        
    def reset_input_buffer(self):
        self.buffer = b""
        self.in_waiting = 0
        
    def reset_output_buffer(self):
        self._output_buffer = b""
        
    def close(self):
        self.is_open = False

@pytest.fixture
def mock_serial_port():
    mock = MockSerial()
    return mock

def test_read_until_prompt_early_return(mock_serial_port):
    """
    Test that read_until_prompt does NOT return early if the prompt character
    appears in the middle of the output.
    """
    session = SerialSession("COM1", timeout=1.0)
    session.ser = mock_serial_port
    
    # Simulate data coming in chunks
    # This config content contains '#' which matches the default prompt regex
    config_content = "interface Vlan1\n description Management for sw1#2\n ip address 10.0.0.1 255.255.255.0\n"
    prompt = "sw1#"
    
    # We want read_until_prompt to return ONLY when it sees the final prompt,
    # NOT when it sees the '#' in "sw1#2"
    
    mock_serial_port.buffer = (config_content + prompt).encode("ascii")
    mock_serial_port.in_waiting = len(mock_serial_port.buffer)
    
    # Execute
    output = session.read_until_prompt(prompt_regex=r"[#>]")
    
    # Verify
    # If the bug exists, it will stop at "sw1#" inside the description
    assert "ip address" in output, "read_until_prompt returned too early!"
    assert output.endswith(prompt) or output.strip().endswith(prompt)

def test_read_until_prompt_anchored(mock_serial_port):
    """
    Test that the regex is correctly anchored to the end.
    """
    session = SerialSession("COM1", timeout=0.1)
    session.ser = mock_serial_port
    
    # Chunk 1: Partial line with '#' in it
    chunk1 = "description specific entry #1\n"
    # Chunk 2: Real prompt
    chunk2 = "Switch>"
    
    mock_serial_port.buffer = (chunk1 + chunk2).encode("ascii")
    mock_serial_port.in_waiting = len(mock_serial_port.buffer)
    
    output = session.read_until_prompt(prompt_regex=r"[#>]")
    
    assert chunk1 in output
    assert chunk2 in output
