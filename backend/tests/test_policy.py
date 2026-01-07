from backend.core import policy, models
from datetime import datetime

def test_normalize_mask():
    assert policy.normalize_mask("/24") == "255.255.255.0"
    assert policy.normalize_mask("24") == "255.255.255.0"
    assert policy.normalize_mask("255.255.255.0") == "255.255.255.0"

def test_validate_hostname_valid():
    device = models.Device(
        id=1, job_id=1, hostname="sw-lab-01", 
        mgmt_ip="10.0.0.1", mask="255.255.255.0", gateway="10.0.0.254"
    )
    errors = policy.validate_device_config(device, [device])
    assert len(errors) == 0

def test_validate_hostname_invalid():
    device = models.Device(
        id=1, job_id=1, hostname="sw lab 01", 
        mgmt_ip="10.0.0.1", mask="255.255.255.0", gateway="10.0.0.254"
    )
    errors = policy.validate_device_config(device, [device])
    assert len(errors) == 1
    assert errors[0].field == "hostname"

def test_validate_subnet_mismatch():
    device = models.Device(
        id=1, job_id=1, hostname="switch1", 
        mgmt_ip="10.0.0.1", mask="255.255.255.0", gateway="192.168.1.1"
    )
    errors = policy.validate_device_config(device, [device])
    assert any(e.field == "gateway" and "not in the same subnet" in e.message for e in errors)

def test_validate_duplicate_ip():
    d1 = models.Device(id=1, job_id=1, hostname="sw1", mgmt_ip="10.0.0.1", mask="/24", gateway="10.0.0.254")
    d2 = models.Device(id=2, job_id=1, hostname="sw2", mgmt_ip="10.0.0.1", mask="/24", gateway="10.0.0.254")
    errors = policy.validate_device_config(d2, [d1, d2])
    assert any(e.field == "mgmt_ip" and "Duplicate" in e.message for e in errors)

def test_validate_duplicate_port():
    d1 = models.Device(id=1, job_id=1, hostname="sw1", mgmt_ip="10.0.0.1", mask="/24", gateway="10.0.0.254", port=1)
    d2 = models.Device(id=2, job_id=1, hostname="sw2", mgmt_ip="10.0.0.2", mask="/24", gateway="10.0.0.254", port=1)
    errors = policy.validate_device_config(d2, [d1, d2])
    assert any(e.field == "port" and "already assigned" in e.message for e in errors)

def test_validate_vlan_range():
    device = models.Device(
        id=1, job_id=1, hostname="sw1", 
        mgmt_ip="10.0.0.1", mask="/24", gateway="10.0.0.254", mgmt_vlan=5000
    )
    errors = policy.validate_device_config(device, [device])
    assert any(e.field == "mgmt_vlan" and "Must be between" in e.message for e in errors)
