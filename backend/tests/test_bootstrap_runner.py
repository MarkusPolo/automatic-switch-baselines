import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.services.bootstrap_runner import BootstrapRunner
from backend.infra import repository, database
from backend.core import models

from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite with SHARED connection
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    database.Base.metadata.create_all(bind=engine)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    with patch("backend.core.services.bootstrap_runner.get_db", side_effect=lambda: override_get_db()):
        yield
    database.Base.metadata.drop_all(bind=engine)

from backend.vendors.base import CommandBlock

@pytest.mark.asyncio
async def test_bootstrap_runner_success():
    db = TestingSessionLocal()
    
    # Create job and device
    job = repository.create_job(db, models.JobCreate(name="Test Job"))
    device = repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw1", mgmt_ip="10.0.0.1", 
        mask="/24", gateway="10.0.0.254", port=1, vendor="generic"
    ))
    run = repository.create_run(db, models.RunCreate(job_id=job.id))
    
    # Mock SerialSession
    mock_ser = MagicMock()
    # 1. sync prompt, 2. conf t, 3. hostname, 4. end, 5. verify, 6. save
    mock_ser.read_until_prompt.side_effect = ["switch>", "sw1#", "sw1#", "sw1#", "sw1#", "sw1#"] 
    
    with patch("backend.core.services.bootstrap_runner.SerialSession", return_value=mock_ser):
        runner = BootstrapRunner(db, run.id, device.id)
        
        # We need to mock the vendor methods
        with patch.object(runner.vendor, "get_bootstrap_commands", return_value=[
            CommandBlock(name="TestBlock", commands=["conf t", "hostname sw1", "end"])
        ]):
            with patch.object(runner.vendor, "get_verify_commands", return_value=["show version"]):
                with patch.object(runner.vendor, "parse_verify", return_value={"success": True, "details": "Matches"}):
                    with patch.object(runner.vendor, "get_save_commands", return_value=["write"]):
                        await runner.run()

    # Check device status
    db_rd = db.query(database.DBRunDevice).filter_by(run_id=run.id, device_id=device.id).first()
    assert db_rd.status == "VERIFIED"
    
    # Check logs
    logs = repository.get_run_logs(db, run.id)
    assert any("Applying 1 configuration blocks" in l.message for l in logs)
    
    db.close()

@pytest.mark.asyncio
async def test_bootstrap_runner_cli_error():
    db = TestingSessionLocal()
    
    job = repository.create_job(db, models.JobCreate(name="Test Job"))
    device = repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw1", mgmt_ip="10.0.0.1", 
        mask="/24", gateway="10.0.0.254", port=1, vendor="generic"
    ))
    run = repository.create_run(db, models.RunCreate(job_id=job.id))
    
    mock_ser = MagicMock()
    # First prompt OK, second one contains an error
    mock_ser.read_until_prompt.side_effect = ["switch>", "% Invalid input detected at", "sw1#"]
    
    with patch("backend.core.services.bootstrap_runner.SerialSession", return_value=mock_ser):
        runner = BootstrapRunner(db, run.id, device.id)
        with patch.object(runner.vendor, "get_bootstrap_commands", return_value=[
            CommandBlock(name="ErrorBlock", commands=["invalid command"], critical=True)
        ]):
            await runner.run()

    # Check device status
    db_rd = db.query(database.DBRunDevice).filter_by(run_id=run.id, device_id=device.id).first()
    assert db_rd.status == "FAILED"
    assert "Critical Error" in db_rd.error_message
    
    db.close()
