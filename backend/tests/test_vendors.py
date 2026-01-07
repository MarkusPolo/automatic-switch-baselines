import pytest
from backend.vendors.loader import get_vendor

@pytest.mark.asyncio
async def test_generic_vendor_rendering():
    vendor = get_vendor("generic")
    data = {
        "hostname": "test-sw",
        "mgmt_ip": "192.168.1.10",
        "mgmt_mask": "255.255.255.0",
        "gateway": "192.168.1.1",
        "mgmt_vlan": None
    }
    blocks = await vendor.get_bootstrap_commands(data)
    assert len(blocks) == 1
    assert blocks[0].name == "Bootstrap"
    
    cmds = "\n".join(blocks[0].commands)
    assert "hostname test-sw" in cmds
    assert "ip address 192.168.1.10 255.255.255.0" in cmds
    assert "ip default-gateway 192.168.1.1" in cmds

@pytest.mark.asyncio
async def test_cisco_vendor_rendering():
    vendor = get_vendor("cisco")
    data = {
        "hostname": "cisco-sw",
        "mgmt_ip": "10.0.0.5",
        "mgmt_mask": "255.255.255.0",
        "gateway": "10.0.0.1",
        "mgmt_vlan": 10
    }
    blocks = await vendor.get_bootstrap_commands(data)
    assert len(blocks) == 3
    assert any(b.name == "Enter Configuration" for b in blocks)
    assert any(b.name == "Apply Baseline" for b in blocks)
    
    # Check Vlan 10
    full_cmds = ""
    for b in blocks:
        full_cmds += "\n".join(b.commands) + "\n"
    
    assert "hostname cisco-sw" in full_cmds
    assert "vlan 10" in full_cmds
    assert "interface Vlan10" in full_cmds
    assert "ip address 10.0.0.5 255.255.255.0" in full_cmds
