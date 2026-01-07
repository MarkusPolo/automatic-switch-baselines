from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class JobBase(BaseModel):
    name: str
    customer: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceBase(BaseModel):
    job_id: int
    port: Optional[int] = Field(None, ge=1, le=16)
    vendor: Optional[str] = None
    model: Optional[str] = None
    hostname: str
    mgmt_ip: str
    mask: str
    gateway: str
    mgmt_vlan: Optional[int] = None
    status: str = "pending"

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    port: Optional[int] = Field(None, ge=1, le=16)
    vendor: Optional[str] = None
    model: Optional[str] = None
    hostname: Optional[str] = None
    mgmt_ip: Optional[str] = None
    mask: Optional[str] = None
    gateway: Optional[str] = None
    mgmt_vlan: Optional[int] = None
    status: Optional[str] = None

class Device(DeviceBase):
    id: int

    class Config:
        from_attributes = True

class RunBase(BaseModel):
    job_id: int
    parallelism: int = 4

class RunCreate(RunBase):
    pass

class Run(RunBase):
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str = "running"

    class Config:
        from_attributes = True

class RunDevice(BaseModel):
    run_id: int
    device_id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class EventLogBase(BaseModel):
    run_id: int
    device_id: Optional[int] = None
    port: Optional[int] = None
    level: str
    message: str
    raw: Optional[str] = None

class EventLog(EventLogBase):
    id: int
    ts: datetime

    class Config:
        from_attributes = True

class ValidationError(BaseModel):
    field: str
    device_id: Optional[int] = None
    row: Optional[int] = None
    message: str
    suggestion: Optional[str] = None
