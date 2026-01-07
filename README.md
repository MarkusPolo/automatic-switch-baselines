# Automatic Switch Configuration System

An automated solution for serial-based switch configuration, designed for high-density console environments (e.g., Raspberry Pi with 16-port serial adapter).

## Architecture

- **Frontend**: Live dashboard and wizard for job management.
- **Backend (FastAPI)**: API for managing devices, jobs, and serial runs.
- **Engine**: State-machine based serial communication engine.
- **Templates**: Jinja2-based configuration templates for various vendors.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
3. Start the frontend (see frontend directory for details).

## Features

- Parallel configuration of up to 16 devices.
- Multi-phase provisioning (Console Bootstrap -> Remote Provisioning).
- Live logs and verification reports.
- CSV import for bulk device staging.
