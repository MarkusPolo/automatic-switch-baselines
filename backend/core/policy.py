import re
import ipaddress
from typing import List, Optional
from . import models

HOSTNAME_REGEX = re.compile(r"^[a-zA-Z0-9-]{1,63}$")

def normalize_mask(mask: str) -> str:
    """
    Normalizes a mask (CIDR or dotted decimal) to dotted decimal.
    Example: '/24' -> '255.255.255.0', '255.255.255.0' -> '255.255.255.0'
    """
    mask = mask.strip()
    if mask.startswith("/"):
        prefix = int(mask[1:])
        return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask)
    if mask.isdigit():
        prefix = int(mask)
        return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask)
    # Assume it's already dotted decimal or invalid (ipaddress will catch it later)
    return mask

def validate_device_config(
    device: models.Device, 
    all_devices: List[models.Device]
) -> List[models.ValidationError]:
    errors = []
    
    # 1) Hostname Validation
    if not HOSTNAME_REGEX.match(device.hostname):
        errors.append(models.ValidationError(
            field="hostname",
            device_id=device.id,
            message=f"Invalid hostname: '{device.hostname}'. Must be 1-63 chars, alphanumeric or hyphen, no spaces.",
            suggestion="Use something like 'sw-lab-01'."
        ))
        
    # 2) IP & Mask Validation
    try:
        ip = ipaddress.IPv4Address(device.mgmt_ip)
    except ValueError:
        errors.append(models.ValidationError(
            field="mgmt_ip",
            device_id=device.id,
            message=f"Invalid IPv4 address: '{device.mgmt_ip}'."
        ))
        ip = None
        
    norm_mask = normalize_mask(device.mask)
    try:
        mask_obj = ipaddress.IPv4Address(norm_mask)
        # Check if it's a valid netmask
        # Simple way: check if it's in the list of valid netmasks
        valid_masks = [str(ipaddress.IPv4Network(f"0.0.0.0/{i}").netmask) for i in range(1, 33)]
        if norm_mask not in valid_masks:
            raise ValueError("Invalid netmask")
    except ValueError:
        errors.append(models.ValidationError(
            field="mask",
            device_id=device.id,
            message=f"Invalid subnet mask: '{device.mask}'."
        ))
        mask_obj = None

    # 3) Gateway in same subnet
    if ip and mask_obj:
        try:
            gw = ipaddress.IPv4Address(device.gateway)
            network = ipaddress.IPv4Network(f"{device.mgmt_ip}/{norm_mask}", strict=False)
            if gw not in network:
                errors.append(models.ValidationError(
                    field="gateway",
                    device_id=device.id,
                    message=f"Gateway '{device.gateway}' is not in the same subnet as IP '{device.mgmt_ip}/{norm_mask}'."
                ))
        except ValueError:
            errors.append(models.ValidationError(
                field="gateway",
                device_id=device.id,
                message=f"Invalid Gateway IPv4: '{device.gateway}'."
            ))

    # 4) Duplicate IP within job
    duplicate_ips = [d for d in all_devices if d.id != device.id and d.mgmt_ip == device.mgmt_ip]
    if duplicate_ips:
        errors.append(models.ValidationError(
            field="mgmt_ip",
            device_id=device.id,
            message=f"Duplicate management IP '{device.mgmt_ip}' found in the same job.",
            suggestion=f"Conflict with device ID {duplicate_ips[0].id}."
        ))

    # 5) Duplicate Port within job
    if device.port:
        duplicate_ports = [d for d in all_devices if d.id != device.id and d.port == device.port]
        if duplicate_ports:
            errors.append(models.ValidationError(
                field="port",
                device_id=device.id,
                message=f"Port {device.port} is already assigned to another device in this job.",
                suggestion=f"Conflict with device ID {duplicate_ports[0].id}."
            ))
            
    # 6) VLAN range
    if device.mgmt_vlan is not None:
        if not (1 <= device.mgmt_vlan <= 4094):
            errors.append(models.ValidationError(
                field="mgmt_vlan",
                device_id=device.id,
                message=f"Invalid VLAN: {device.mgmt_vlan}. Must be between 1 and 4094."
            ))

    # 7) Port range
    if device.port is not None:
        if not (1 <= device.port <= 16):
            errors.append(models.ValidationError(
                field="port",
                device_id=device.id,
                message=f"Invalid port: {device.port}. Raspberry Pi adapter only supports ports 1-16."
            ))

    return errors
