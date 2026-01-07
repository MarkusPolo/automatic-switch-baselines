from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from ..infra import database, repository
from ..core import models, services, policy

# Initialize DB
database.init_db()

app = FastAPI(
    title="Automatic Switch Configuration",
    description="Raspberry Pi service for automatic switch configuration.",
    version="0.1.0",
)

# Health
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "message": "Automatic Switch Configuration Service is running."
    }

# Jobs
@app.post("/jobs", response_model=models.Job)
def create_job(job: models.JobCreate, db: Session = Depends(database.get_db)):
    return repository.create_job(db, job)

@app.get("/jobs", response_model=List[models.Job])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return repository.get_jobs(db, skip=skip, limit=limit)

@app.get("/jobs/{job_id}", response_model=models.Job)
def get_job(job_id: int, db: Session = Depends(database.get_db)):
    db_job = repository.get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

# Devices
@app.post("/jobs/{job_id}/devices", response_model=models.Device)
def create_device(job_id: int, device: models.DeviceCreate, db: Session = Depends(database.get_db)):
    device.job_id = job_id
    return repository.create_device(db, device)

@app.get("/jobs/{job_id}/devices", response_model=List[models.Device])
def list_devices(job_id: int, db: Session = Depends(database.get_db)):
    return repository.get_devices_by_job(db, job_id)

@app.post("/jobs/{job_id}/devices/import-csv")
async def import_csv(job_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    content = await file.read()
    csv_text = content.decode("utf-8")
    success_count, errors = services.import_devices_from_csv(db, job_id, csv_text)
    return {
        "job_id": job_id,
        "success_count": success_count,
        "errors": errors
    }

@app.patch("/devices/{device_id}", response_model=models.Device)
def update_device(device_id: int, device_update: models.DeviceUpdate, db: Session = Depends(database.get_db)):
    db_device = repository.update_device(db, device_id, device_update)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device

@app.delete("/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(database.get_db)):
    if not repository.delete_device(db, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "deleted"}

# Ports
@app.get("/ports")
def get_ports(db: Session = Depends(database.get_db)):
    # Simple logic: check which ports are currently assigned in 'pending' or 'running' status
    assigned_ports = {d.port for d in db.query(database.DBDevice).filter(database.DBDevice.port.isnot(None)).all()}
    
    ports = {}
    for i in range(1, 17):
        status = "available"
        if i in assigned_ports:
            status = "busy"
        ports[f"port{i}"] = status
    return ports

# Runs
@app.post("/jobs/{job_id}/runs", response_model=models.Run)
def create_run(job_id: int, run_create: models.RunCreate, db: Session = Depends(database.get_db)):
    run_create.job_id = job_id
    return repository.create_run(db, run_create)

@app.get("/runs/{run_id}", response_model=models.Run)
def get_run(run_id: int, db: Session = Depends(database.get_db)):
    db_run = repository.get_run(db, run_id)
    if not db_run:
        raise HTTPException(status_code=404, detail="Run not found")
    return db_run

@app.get("/runs/{run_id}/logs", response_model=List[models.EventLog])
def get_run_logs(run_id: int, db: Session = Depends(database.get_db)):
    return repository.get_event_logs(db, run_id)

# Dry-run
@app.post("/jobs/{job_id}/dry-run", response_model=List[models.ValidationError])
def dry_run_job(job_id: int, db: Session = Depends(database.get_db)):
    db_job = repository.get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    devices = repository.get_devices_by_job(db, job_id)
    all_errors = []
    
    # Convert DB models to Pydantic for policy validation
    pydantic_devices = [models.Device.model_validate(d) for d in devices]
    
    for device in pydantic_devices:
        errors = policy.validate_device_config(device, pydantic_devices)
        all_errors.extend(errors)
        
    return all_errors

@app.get("/")
async def root():
    return {"message": "Welcome to the Automatic Switch Configuration API. Visit /docs for API documentation."}
