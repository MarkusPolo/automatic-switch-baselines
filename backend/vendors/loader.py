from typing import Dict, Type
from .base import BaseVendor
from .generic import GenericVendor
from .cisco import CiscoVendor

class VendorLoader:
    _vendors: Dict[str, Type[BaseVendor]] = {
        "generic": GenericVendor,
        "cisco": CiscoVendor,
        # Cisco IOS alias
        "cisco_ios": CiscoVendor,
    }

    @classmethod
    def get_vendor(cls, vendor_id: str) -> BaseVendor:
        vendor_class = cls._vendors.get(vendor_id, GenericVendor)
        return vendor_class()

def get_vendor(vendor_id: str) -> BaseVendor:
    return VendorLoader.get_vendor(vendor_id)
