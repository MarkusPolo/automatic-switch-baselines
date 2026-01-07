import pytest
import csv
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.infra import database, repository
from backend.core import models
from backend.core.services.report_service import ReportService

# Setup in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    database.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    database.Base.metadata.drop_all(bind=engine)

def test_generate_json_report(db):
    # 1. Setup Data
    job = repository.create_job(db, models.JobCreate(name="Reporting Job"))
    dev1 = repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw1", mgmt_ip="1.1.1.1", mask="/24", gateway="1.1.1.254"
    ))
    run = repository.create_run(db, models.RunCreate(job_id=job.id))
    
    repository.update_run_device_status(
        db, run.id, dev1.id, "VERIFIED", 
        template_hash="abc123hash"
    )
    
    # 2. Generate Report
    service = ReportService(db)
    report = service.generate_json_report(run.id)
    
    # 3. Assertions
    assert report["run_id"] == run.id
    assert len(report["devices"]) == 1
    assert report["devices"][0]["hostname"] == "sw1"
    assert report["devices"][0]["template_hash"] == "abc123hash"
    assert report["devices"][0]["status"] == "VERIFIED"

def test_generate_csv_report(db):
    job = repository.create_job(db, models.JobCreate(name="CSV Job"))
    dev1 = repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw-csv", mgmt_ip="1.1.1.2", mask="/24", gateway="1.1.1.1"
    ))
    run = repository.create_run(db, models.RunCreate(job_id=job.id))
    repository.update_run_device_status(db, run.id, dev1.id, "FAILED", error_code="SERIAL_TIMEOUT", error_message="Link down")
    
    service = ReportService(db)
    csv_str = service.generate_csv_report(run.id)
    
    # Check CSV Content
    f = io.StringIO(csv_str)
    reader = csv.DictReader(f)
    rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["hostname"] == "sw-csv"
    assert rows[0]["error_code"] == "SERIAL_TIMEOUT"
    assert rows[0]["status"] == "FAILED"
