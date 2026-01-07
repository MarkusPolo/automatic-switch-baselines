from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from . import models

router = APIRouter()

@router.get("/jobs")
def get_jobs(db: Session = Depends(get_db)):
    return db.query(models.Job).all()

@router.post("/jobs")
def create_job(name: String, db: Session = Depends(get_db)):
    db_job = models.Job(name=name)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job
