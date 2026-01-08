from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from ..app.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBJob(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    customer = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    devices = relationship("DBDevice", back_populates="job")
    runs = relationship("DBRun", back_populates="job")

class DBDevice(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    port = Column(Integer, nullable=True)  # 1-16
    vendor = Column(String, nullable=True)
    model = Column(String, nullable=True)
    hostname = Column(String)
    mgmt_ip = Column(String)
    mask = Column(String)
    gateway = Column(String)
    mgmt_vlan = Column(Integer, nullable=True)
    status = Column(String, default="pending")
    job = relationship("DBJob", back_populates="devices")

class DBRun(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    started_at = Column(DateTime, default=datetime.now)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")
    parallelism = Column(Integer, default=4)
    job = relationship("DBJob", back_populates="runs")
    run_devices = relationship("DBRunDevice", back_populates="run")
    event_logs = relationship("DBEventLog", back_populates="run")

class DBRunDevice(Base):
    __tablename__ = "run_devices"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    status = Column(String)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    template_hash = Column(String, nullable=True)
    tasks = Column(Text, nullable=True) # JSON list of verification steps
    captured_config = Column(Text, nullable=True) # Full running config
    run = relationship("DBRun", back_populates="run_devices")

class DBEventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    port = Column(Integer, nullable=True)
    ts = Column(DateTime, default=datetime.now)
    level = Column(String)
    message = Column(Text)
    raw = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    run = relationship("DBRun", back_populates="event_logs")

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Soft migration: Add missing columns if they don't exist
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # Tables to check
        updates = {
            "run_devices": ["error_code", "template_hash", "tasks", "captured_config"],
            "event_logs": ["error_code"]
        }
        
        for table, columns in updates.items():
            existing_columns = [c["name"] for c in inspector.get_columns(table)]
            for col in columns:
                if col not in existing_columns:
                    print(f"Adding missing column {col} to {table}")
                    # Map column name to SQL type
                    col_type = "TEXT" if col in ["template_hash", "tasks", "captured_config"] else "VARCHAR"
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"Failed to add column {col} to {table}: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
