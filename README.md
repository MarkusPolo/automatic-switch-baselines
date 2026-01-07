# Automatic Switch Configuration

A Raspberry Pi service for automatic switch configuration. This tool automates the repetitive task of initial switch setup (bootstrapping) to save time and prevent errors.

## Architecture: 2-Phase Design

This project follows a 2-phase approach to ensure reliability and speed:

1.  **Phase 1: Console Bootstrap** (on the Pi)
    - **Goal:** Minimal, standardized baseline to make the device reachable via SSH/HTTPS.
    - **Outcome:** Device has a hostname, management IP, and SSH access enabled.
    - **Concurrency:** Supports up to 16 parallel console sessions (via Raspberry Pi adapter).

2.  **Phase 2: Remote Provisioning** (SSH/Ansible)
    - **Goal:** Full configuration (VLANs, Trunks, STP, etc.) using idempotent methods.
    - **Outcome:** Fully configured and verified switch.

## Quickstart

### Local Development

1.  **Prerequisites:** Python 3.11+, Poetry.
2.  **Install dependencies:**
    ```bash
    make install
    ```
3.  **Run the service:**
    ```bash
    make run
    ```
4.  **Access API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Raspberry Pi Deployment

1.  Clone the repository on your Pi.
2.  Run the installation script (to be implemented).
3.  Configure the systemd service located in `ops/`.
4.  Start the service:
    ```bash
    sudo systemctl enable --now automatic-switch.service
    ```

## Security

- **LAN-only assumption:** This system is designed for use within an isolated management LAN. No authentication is implemented by default.
- **Exposure:** Do not expose this service to the public internet.

## Logging

- Logs are stored in the `logs/` directory (created at runtime).
- Each job and port has its own rotating log file for detailed auditing.

## Tech Stack

- **Backend:** FastAPI, Python 3.11+
- **Serial:** `pyserial`
- **Database:** SQLite (SQLAlchemy)
- **Templating:** Jinja2
