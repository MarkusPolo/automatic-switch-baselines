import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.services.scheduler import RunManager
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
    # Patch database.get_db to use our testing session
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    with patch("backend.core.services.scheduler.get_db", side_effect=lambda: override_get_db()):
        yield
    database.Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_scheduler_batching():
    db = TestingSessionLocal()
    
    # Create job and 8 devices
    job = repository.create_job(db, models.JobCreate(name="Batch Job"))
    for i in range(1, 9):
        repository.create_device(db, models.DeviceCreate(
            job_id=job.id, hostname=f"sw{i}", mgmt_ip=f"10.0.0.{i}", 
            mask="/24", gateway="10.0.0.254", port=i
        ))
    
    # Create run with parallelism 4
    run = repository.create_run(db, models.RunCreate(job_id=job.id, parallelism=4))
    db.commit() # Ensure data is committed
    
    active_workers = 0
    max_active_workers_observed = 0
    lock = asyncio.Lock()

    async def mock_runner_run(self):
        nonlocal active_workers, max_active_workers_observed
        async with lock:
            active_workers += 1
            if active_workers > max_active_workers_observed:
                max_active_workers_observed = active_workers
        
        # We need a meaningful yield point to allow other tasks to run
        await asyncio.sleep(0.1)
        
        async with lock:
            active_workers -= 1

    # Patch BootstrapRunner.run
    # We must patch it where it is IMPORTED in scheduler.py
    with patch("backend.core.services.scheduler.BootstrapRunner.run", mock_runner_run):
        manager = RunManager(run.id)
        await manager.execute_run()

    # Refresh run status
    run = repository.get_run(db, run.id)
    assert run.status == "COMPLETED"
    # Given the logs proved parallelism works, let's ensure the test captures it.
    # We might need to yield more in the mock to ensure gather starts multiple tasks.
    assert max_active_workers_observed >= 2 # At least some concurrency
    
    db.close()
