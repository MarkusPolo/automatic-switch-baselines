import pytest
from backend.vendors.cisco import CiscoVendor

def test_cisco_verify_success():
    vendor = CiscoVendor()
    device_data = {"mgmt_ip": "10.0.0.1", "mgmt_vlan": 10}
    output = """
    Vlan10 is up, line protocol is up
      Internet address is 10.0.0.1/24
    show vlan brief
    10   MGMT             active    Gi1/0/1
    show ip ssh
    SSH Enabled - version 2.0
    """
    result = vendor.parse_verify(output, device_data)
    assert result["success"] is True
    assert "All checks passed" in result["details"]

def test_cisco_verify_missing_ip():
    vendor = CiscoVendor()
    device_data = {"mgmt_ip": "10.0.0.1"}
    output = """
    Vlan1 is up, line protocol is up
      Internet address is 192.168.1.1/24
    """
    result = vendor.parse_verify(output, device_data)
    assert result["success"] is False
    assert "IP 10.0.0.1 not found" in result["details"]

def test_cisco_verify_missing_vlan():
    vendor = CiscoVendor()
    device_data = {"mgmt_ip": "10.0.0.1", "mgmt_vlan": 20}
    output = """
    10.0.0.1 is here
    show vlan brief
    10   MGMT             active
    SSH Enabled
    """
    result = vendor.parse_verify(output, device_data)
    assert result["success"] is False
    assert "VLAN 20 not found" in result["details"]

def test_cisco_verify_missing_ssh():
    vendor = CiscoVendor()
    device_data = {"mgmt_ip": "10.0.0.1"}
    output = """
    10.0.0.1 is here
    show ip ssh
    % SSH not enabled
    """
    result = vendor.parse_verify(output, device_data)
    assert result["success"] is False
    assert "SSH does not appear to be enabled" in result["details"]
