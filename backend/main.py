from fastapi import FastAPI
from .database import engine, Base
from .api import router

app = FastAPI(title="Automatic Switch Config API")

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Automatic Switch Configuration API is running"}
