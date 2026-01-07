from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .database import Base

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    
    devices = relationship("Device", back_populates="job")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    hostname = Column(String)
    mgmt_ip = Column(String)
    mask = Column(String)
    gateway = Column(String)
    mgmt_vlan = Column(Integer, nullable=True)
    vendor = Column(String)
    model = Column(String)
    port = Column(String) # e.g., port1
    status = Column(String, default="pending")
    
    job = relationship("Job", back_populates="devices")
