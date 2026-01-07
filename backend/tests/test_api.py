from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.infra.database import Base, get_db
import pytest

from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_and_list_jobs():
    response = client.post("/jobs", json={"name": "Job 1", "customer": "Cust A"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Job 1"
    assert "id" in data

    response = client.get("/jobs")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_ports_status():
    response = client.get("/ports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 16
    assert data["port1"] == "available"

def test_import_csv_endpoint():
    # Create job
    job_resp = client.post("/jobs", json={"name": "Import Job"})
    job_id = job_resp.json()["id"]

    csv_data = "port,hostname,mgmt_ip,mask,gateway,mgmt_vlan,model\n1,Switch1,10.0.0.1,255.255.255.0,10.0.0.254,10,C3750"
    files = {"file": ("data.csv", csv_data, "text/csv")}
    
    response = client.post(f"/jobs/{job_id}/devices/import-csv", files=files)
    assert response.status_code == 200
    assert response.json()["success_count"] == 1
    
    # Check if device created
    dev_resp = client.get(f"/jobs/{job_id}/devices")
    assert len(dev_resp.json()) == 1
    assert dev_resp.json()[0]["hostname"] == "Switch1"

def test_dry_run_endpoint():
    # Create job
    job_resp = client.post("/jobs", json={"name": "Dry Run Job"})
    job_id = job_resp.json()["id"]
    
    # Add two devices with duplicate IP
    client.post(f"/jobs/{job_id}/devices", json={
        "job_id": job_id, "hostname": "sw1", "mgmt_ip": "10.0.0.1", "mask": "/24", "gateway": "10.0.0.254"
    })
    client.post(f"/jobs/{job_id}/devices", json={
        "job_id": job_id, "hostname": "sw2", "mgmt_ip": "10.0.0.1", "mask": "/24", "gateway": "10.0.0.254"
    })
    
    # Run dry-run
    response = client.post(f"/jobs/{job_id}/dry-run")
    assert response.status_code == 200
    errors = response.json()
    assert len(errors) > 0
    assert any("Duplicate management IP" in e["message"] for e in errors)
