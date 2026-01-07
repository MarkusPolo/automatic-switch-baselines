import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.infra import database, repository
from backend.core import models

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def client():
    database.Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()
    database.Base.metadata.drop_all(bind=engine)

def test_get_preview_endpoint(client):
    # Setup: Create a job and device
    db = TestingSessionLocal()
    job = repository.create_job(db, models.JobCreate(name="Preview Job"))
    device = repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw-preview", mgmt_ip="1.1.1.1", 
        mask="/24", gateway="1.1.1.254", vendor="cisco"
    ))
    job_id = job.id
    device_id = device.id
    db.close()

    response = client.get(f"/jobs/{job_id}/devices/{device_id}/preview")
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == "sw-preview"
    assert data["vendor"] == "cisco"
    assert "! Block: Enter Configuration" in data["commands"]
    assert "conf t" in data["commands"]
    assert len(data["hash"]) == 12

def test_bulk_preview_endpoint(client):
    db = TestingSessionLocal()
    job = repository.create_job(db, models.JobCreate(name="Bulk Preview"))
    repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw1", mgmt_ip="1.1.1.1", mask="/24", gateway="1.1.1.254"
    ))
    repository.create_device(db, models.DeviceCreate(
        job_id=job.id, hostname="sw2", mgmt_ip="1.1.1.2", mask="/24", gateway="1.1.1.254"
    ))
    job_id = job.id
    db.close()

    response = client.post(f"/jobs/{job_id}/preview")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["hostname"] == "sw1"
    assert data[1]["hostname"] == "sw2"
