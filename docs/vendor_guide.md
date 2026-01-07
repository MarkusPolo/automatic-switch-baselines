# Vendor Development Guide

This guide explains how to add support for a new switch vendor to the Automatic Switch Configuration system.

## 1. Create the Vendor Plugin

Add a new file in `backend/vendors/` (e.g., `hp.py`). Implement the `BaseVendor` class:

```python
from .base import BaseVendor, CommandBlock
from typing import List, Dict, Any

class HPVendor(BaseVendor):
    @property
    def vendor_id(self) -> str:
        return "hp"

    async def get_bootstrap_commands(self, data: Dict[str, Any]) -> List[CommandBlock]:
        # Render your Jinja2 templates here
        pass

    def parse_verify(self, output: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
        # Use regex to verify the configuration applied correctly
        pass
```

## 2. Register Template

Create a Jinja2 template in `backend/vendors/templates/` (e.g., `hp_bootstrap.j2`). Use the common variables:
- `hostname`
- `mgmt_ip`
- `mgmt_mask` (CIDR or Mask)
- `gateway`
- `mgmt_vlan`

## 3. Register in Loader

Update `backend/vendors/loader.py` to include your new vendor:

```python
from .hp import HPVendor

def get_vendor(vendor_id: str) -> BaseVendor:
    vendors = {
        "cisco": CiscoVendor(),
        "hp": HPVendor(),
        "generic": GenericVendor(),
    }
    return vendors.get(vendor_id.lower(), GenericVendor())
```

## 4. Testing

Add a new test file in `backend/tests/` to verify your Jinja2 rendering and regex parsing logic. Clone `test_verification.py` as a starting point.
