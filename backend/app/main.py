from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pathlib import Path

from ..infra import database, repository
from ..core import models, services, policy
from ..infra.serial import discover_ports
from ..core.services.scheduler import RunManager
from .config import settings
import hashlib
from ..vendors.loader import get_vendor
from ..core.services.report_service import ReportService

# Initialize DB
database.init_db()

app = FastAPI(
    title="Automatic Switch Configuration",
    description="Raspberry Pi service for automatic switch configuration.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def passcode_protection(request: Request, call_next):
    # Skip passcode for health and root
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
        
    if settings.API_PASSCODE:
        passcode = request.headers.get("X-Passcode")
        if passcode != settings.API_PASSCODE:
            return JSONResponse(status_code=403, content={"detail": "Invalid or missing passcode"})
    return await call_next(request)

# Health
@app.get("/health")
async def health_check(db: Session = Depends(database.get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
        
    ports = discover_ports()
    
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "serial_ports": {
            "count": len(ports),
            "available": ports
        },
        "frontend_path": str(frontend_path),
        "frontend_exists": frontend_path.exists(),
        "version": "0.1.0"
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
def create_run(job_id: int, run_create: models.RunCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    run_create.job_id = job_id
    if run_create.parallelism is None:
        run_create.parallelism = settings.DEFAULT_PARALLELISM
        
    db_run = repository.create_run(db, run_create)
    
    # Trigger background execution
    manager = RunManager(db_run.id)
    background_tasks.add_task(manager.execute_run)
    
    return db_run

@app.get("/runs/{run_id}", response_model=models.Run)
def get_run(run_id: int, db: Session = Depends(database.get_db)):
    db_run = repository.get_run(db, run_id)
    if not db_run:
        raise HTTPException(status_code=404, detail="Run not found")
    return db_run

@app.get("/runs/{run_id}/logs", response_model=List[models.EventLog])
def get_run_logs(run_id: int, db: Session = Depends(database.get_db)):
    return repository.get_run_logs(db, run_id)

    return all_errors

# Dry-run
@app.post("/jobs/{job_id}/dry-run", response_model=List[models.ValidationError])
async def dry_run_job(job_id: int, db: Session = Depends(database.get_db)):
    db_job = repository.get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    devices = repository.get_devices_by_job(db, job_id)
    all_errors = []
    
    # Convert DB models to Pydantic for policy validation
    pydantic_devices = [models.Device.model_validate(d) for d in devices]
    
    for device in pydantic_devices:
        errors = await policy.validate_device_config(device, pydantic_devices)
        all_errors.extend(errors)
        
    return all_errors

# Preview
@app.get("/jobs/{job_id}/devices/{device_id}/preview", response_model=models.DevicePreview)
async def get_device_preview(job_id: int, device_id: int, db: Session = Depends(database.get_db)):
    db_device = repository.get_device_by_id(db, device_id)
    if not db_device or db_device.job_id != job_id:
        raise HTTPException(status_code=404, detail="Device not found")
    
    vendor = get_vendor(db_device.vendor or "generic")
    config_params = {
        "hostname": db_device.hostname,
        "mgmt_ip": db_device.mgmt_ip,
        "mgmt_mask": db_device.mask,
        "gateway": db_device.gateway,
        "mgmt_vlan": db_device.mgmt_vlan,
    }
    blocks = await vendor.get_bootstrap_commands(config_params)
    
    commands_text = ""
    for block in blocks:
        commands_text += f"! Block: {block.name}\n"
        commands_text += "\n".join(block.commands) + "\n"
    
    cmd_hash = hashlib.sha256(commands_text.encode()).hexdigest()[:12]
    
    return models.DevicePreview(
        device_id=device_id,
        hostname=db_device.hostname,
        vendor=vendor.vendor_id,
        commands=commands_text,
        hash=cmd_hash
    )

@app.post("/jobs/{job_id}/preview", response_model=List[models.DevicePreview])
async def bulk_preview(job_id: int, db: Session = Depends(database.get_db)):
    db_job = repository.get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    devices = repository.get_devices_by_job(db, job_id)
    previews = []
    for device in devices:
        previews.append(await get_device_preview(job_id, device.id, db))
    return previews

# Static Files (Frontend) - Resolved absolute path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
frontend_path = BASE_DIR / "frontend" / "dist"

if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to the Automatic Switch Configuration API.",
            "frontend_status": "Not found",
            "checked_path": str(frontend_path),
            "visit_docs": "/docs"
        }
@app.get("/runs/{run_id}/report.json")
def get_run_report_json(run_id: int, db: Session = Depends(database.get_db)):
    service = ReportService(db)
    report = service.generate_json_report(run_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report

@app.get("/runs/{run_id}/report.csv")
def get_run_report_csv(run_id: int, db: Session = Depends(database.get_db)):
    service = ReportService(db)
    csv_str = service.generate_csv_report(run_id)
    if csv_str == "error,Run not found":
        raise HTTPException(status_code=404, detail="Run not found")
    
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{run_id}.csv"}
    )
