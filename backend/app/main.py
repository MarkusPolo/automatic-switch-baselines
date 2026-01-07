from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(
    title="Automatic Switch Configuration",
    description="Raspberry Pi service for automatic switch configuration.",
    version="0.1.0",
)

# Setup templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "message": "Automatic Switch Configuration Service is running."
    }

@app.get("/")
async def root():
    return {"message": "Welcome to the Automatic Switch Configuration API. Visit /docs for API documentation."}
