import csv
import io
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from .. import models
from ...infra import repository

def import_devices_from_csv(db: Session, job_id: int, csv_content: str) -> Tuple[int, List[str]]:
    """
    Parses CSV and creates devices for a job.
    Returns (count_success, errors).
    """
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)
    
    success_count = 0
    errors = []
    
    # Required fields based on requirements
    required_fields = ["hostname", "mgmt_ip", "mask", "gateway"]
    
    for i, row in enumerate(reader, start=1):
        # Trim spaces
        row = {k.strip(): v.strip() for k, v in row.items() if k and v}
        
        # Check for required fields
        missing = [field for field in required_fields if field not in row or not row[field]]
        if missing:
            errors.append(f"Line {i}: Missing required fields: {', '.join(missing)}")
            continue
            
        try:
            device_data = {
                "job_id": job_id,
                "hostname": row.get("hostname"),
                "mgmt_ip": row.get("mgmt_ip"),
                "mask": row.get("mask"),
                "gateway": row.get("gateway"),
                "port": int(row["port"]) if row.get("port") and row["port"].isdigit() else None,
                "vendor": row.get("vendor"),
                "model": row.get("model"),
                "mgmt_vlan": int(row["mgmt_vlan"]) if row.get("mgmt_vlan") and row["mgmt_vlan"].isdigit() else None,
                "status": "pending"
            }
            
            device_create = models.DeviceCreate(**device_data)
            repository.create_device(db, device_create)
            success_count += 1
        except Exception as e:
            errors.append(f"Line {i}: Error processing: {str(e)}")
            
    return success_count, errors
