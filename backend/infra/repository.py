from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import DBJob, DBDevice, DBRun, DBRunDevice, DBEventLog
from ..core import models

def get_job(db: Session, job_id: int):
    return db.query(DBJob).filter(DBJob.id == job_id).first()

def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(DBJob).offset(skip).limit(limit).all()

def create_job(db: Session, job: models.JobCreate):
    db_job = DBJob(name=job.name, customer=job.customer)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_devices_by_job(db: Session, job_id: int):
    return db.query(DBDevice).filter(DBDevice.job_id == job_id).all()

def create_device(db: Session, device: models.DeviceCreate):
    db_device = DBDevice(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def update_device(db: Session, device_id: int, device_update: models.DeviceUpdate):
    db_device = db.query(DBDevice).filter(DBDevice.id == device_id).first()
    if db_device:
        update_data = device_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_device, key, value)
        db.commit()
        db.refresh(db_device)
    return db_device

def delete_device(db: Session, device_id: int):
    db_device = db.query(DBDevice).filter(DBDevice.id == device_id).first()
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False

def create_run(db: Session, run: models.RunCreate):
    db_run = DBRun(job_id=run.job_id, parallelism=run.parallelism)
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def get_run(db: Session, run_id: int):
    return db.query(DBRun).filter(DBRun.id == run_id).first()

def get_run_logs(db: Session, run_id: int):
    return db.query(DBEventLog).filter(DBEventLog.run_id == run_id).all()

def get_device_by_id(db: Session, device_id: int):
    return db.query(DBDevice).filter(DBDevice.id == device_id).first()

def update_run_device_status(db: Session, run_id: int, device_id: int, status: str, error_message: Optional[str] = None, error_code: Optional[str] = None, template_hash: Optional[str] = None):
    db_rd = db.query(DBRunDevice).filter(DBRunDevice.run_id == run_id, DBRunDevice.device_id == device_id).first()
    if not db_rd:
        db_rd = DBRunDevice(run_id=run_id, device_id=device_id)
        db.add(db_rd)
    
    db_rd.status = status
    if status == "RUNNING":
        db_rd.started_at = datetime.now(timezone.utc)
    elif status in ["VERIFIED", "FAILED"]:
        db_rd.finished_at = datetime.now(timezone.utc)
        if error_message:
            db_rd.error_message = error_message
        if error_code:
            db_rd.error_code = error_code
        if template_hash:
            db_rd.template_hash = template_hash
    
    db.commit()
    db.refresh(db_rd)
    return db_rd

def update_run_status(db: Session, run_id: int, status: str):
    db_run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if db_run:
        db_run.status = status
        if status in ["COMPLETED", "FAILED"]:
            db_run.finished_at = datetime.now(timezone.utc)
        db.commit()
    return db_run
