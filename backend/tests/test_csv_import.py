from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.infra.database import Base
from backend.core import services, models
from backend.infra import repository

from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_csv_import_valid():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create a job first
    job = repository.create_job(db, models.JobCreate(name="Test Job"))
    
    csv_content = """port,hostname,mgmt_ip,mask,gateway,mgmt_vlan,model
1,Switch1,10.0.0.1,255.255.255.0,10.0.0.254,10,C3750
2,Switch2,10.0.0.2,255.255.255.0,10.0.0.254,10,C3750
"""
    success_count, errors = services.import_devices_from_csv(db, job.id, csv_content)
    
    assert success_count == 2
    assert len(errors) == 0
    
    devices = repository.get_devices_by_job(db, job.id)
    assert len(devices) == 2
    assert devices[0].hostname == "Switch1"
    
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_csv_import_missing_fields():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    job = repository.create_job(db, models.JobCreate(name="Test Job"))
    
    # Missing hostname in second line
    csv_content = """port,hostname,mgmt_ip,mask,gateway,mgmt_vlan,model
1,Switch1,10.0.0.1,255.255.255.0,10.0.0.254,10,C3750
2,,10.0.0.2,255.255.255.0,10.0.0.254,10,C3750
"""
    success_count, errors = services.import_devices_from_csv(db, job.id, csv_content)
    
    assert success_count == 1
    assert len(errors) == 1
    assert "Missing required fields: hostname" in errors[0]
    
    db.close()
    Base.metadata.drop_all(bind=engine)
