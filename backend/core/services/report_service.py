import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ...infra import repository, database
from .. import models

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_json_report(self, run_id: int) -> Dict[str, Any]:
        """
        Generates a comprehensive JSON report for a run.
        """
        run = repository.get_run(self.db, run_id)
        if not run:
            return {"error": "Run not found"}

        devices = self.db.query(database.DBRunDevice).filter_by(run_id=run_id).all()
        job = repository.get_job(self.db, run.job_id)
        
        report = {
            "run_id": run.id,
            "job_name": job.name if job else "Unknown",
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "parallelism": run.parallelism,
            "devices": []
        }

        for rd in devices:
            dev = repository.get_device_by_id(self.db, rd.device_id)
            duration = None
            if rd.started_at and rd.finished_at:
                duration = (rd.finished_at - rd.started_at).total_seconds()

            report["devices"].append({
                "hostname": dev.hostname if dev else "Unknown",
                "mgmt_ip": dev.mgmt_ip if dev else "Unknown",
            tasks_list = []
            if rd.tasks:
                try:
                    tasks_list = json.loads(rd.tasks)
                except:
                    tasks_list = []

            report["devices"].append({
                "hostname": dev.hostname if dev else "Unknown",
                "mgmt_ip": dev.mgmt_ip if dev else "Unknown",
                "port": dev.port if dev else rd.port, # dev has port, rd has port in DB schema (wait, I should check database.py)
                "status": rd.status,
                "started_at": rd.started_at.isoformat() if rd.started_at else None,
                "finished_at": rd.finished_at.isoformat() if rd.finished_at else None,
                "duration_seconds": duration,
                "error_message": rd.error_message,
                "error_code": rd.error_code,
                "template_hash": rd.template_hash,
                "tasks": tasks_list
            })

        return report

    def generate_csv_report(self, run_id: int) -> str:
        """
        Generates a CSV report string for a run.
        """
        json_report = self.generate_json_report(run_id)
        if "error" in json_report:
            return "error,Run not found"

        output = io.StringIO()
        fieldnames = [
            "hostname", "mgmt_ip", "port", "status", 
            "started_at", "finished_at", "duration_seconds", 
            "error_message", "error_code", "template_hash", "tasks_summary"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for dev in json_report["devices"]:
            # Flatten tasks for CSV
            tasks_str = ""
            if dev.get("tasks"):
                tasks_str = "; ".join([f"{t['name']}: {t['status']}" for t in dev["tasks"]])
            dev["tasks_summary"] = tasks_str
            
            # Remove raw tasks list from CSV dict to avoid error
            row = dev.copy()
            if "tasks" in row: del row["tasks"]
            
            writer.writerow(row)
            
        return output.getvalue()
