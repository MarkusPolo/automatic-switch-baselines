import asyncio
import logging
from sqlalchemy.orm import Session
from .bootstrap_runner import BootstrapRunner
from ...infra import repository, database
from ...infra.database import get_db

logger = logging.getLogger(__name__)

class RunManager:
    def __init__(self, run_id: int):
        self.run_id = run_id

    async def execute_run(self):
        """
        Main entry point for background execution.
        """
        # Create a new DB session for the background task
        db = next(get_db())
        try:
            run = repository.get_run(db, self.run_id)
            if not run:
                logger.error(f"Run {self.run_id} not found")
                return

            # Get all devices for this job
            devices = repository.get_devices_by_job(db, run.job_id)
            if not devices:
                repository.update_run_status(db, self.run_id, "COMPLETED")
                return

            # Batching logic using Semaphore
            semaphore = asyncio.Semaphore(run.parallelism)

            async def run_worker(device_id):
                async with semaphore:
                    # Individual worker session to avoid thread conflicts
                    worker_db = next(get_db())
                    try:
                        runner = BootstrapRunner(worker_db, self.run_id, device_id)
                        await runner.run()
                    finally:
                        worker_db.close()

            # Schedule all devices
            tasks = [run_worker(d.id) for d in devices]
            await asyncio.gather(*tasks)

            repository.update_run_status(db, self.run_id, "COMPLETED")
            
        except Exception as e:
            logger.exception(f"Error in RunManager for run {self.run_id}")
            repository.update_run_status(db, self.run_id, "FAILED")
        finally:
            db.close()
