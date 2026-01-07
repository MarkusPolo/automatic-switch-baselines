# Operations Runbook

This document provides instructions for setting up, operating, and troubleshooting the Switch Bootstrapper service on a Raspberry Pi.

## Raspberry Pi Setup

1.  **OS Installation**: Use Raspberry Pi OS Lite (64-bit recommended).
2.  **User Configuration**: Ensure the default user (e.g. `administrator`) is in the `dialout` group to access serial ports:
    ```bash
    sudo usermod -a -G dialout administrator
    ```
3.  **udev Rules**: For consistent port mapping (e.g., `/home/administrator/port1`), create `/etc/udev/rules.d/99-serial.rules`:
    ```text
    SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", SYMLINK+="home/administrator/port%n"
    ```
    (Replace IDs with your specific USB-to-Serial hub IDs).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/MarkusPolo/automatic-switch-baselines.git /home/administrator/automatic-switch-baselines
    ```
2.  Setup Python Environment:
    
    ### Option A: venv (Standard)
    ```bash
    cd /home/administrator/automatic-switch-baselines
    python -m venv .venv
    ./.venv/bin/pip install poetry
    ./.venv/bin/poetry install
    ```

    ### Option B: Conda / Miniforge (Alternative)
    If using Conda (e.g. `proj311` environment):
    ```bash
    conda activate proj311
    pip install -e .
    # Note your uvicorn path with: which uvicorn
    ```
3.  Configure Environment:
    ```bash
    sudo cp ops/.env.example /etc/switch-bootstrapper.env
    sudo nano /etc/switch-bootstrapper.env
    ```
4.  Setup systemd:
    ```bash
    sudo cp ops/switch-bootstrapper.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now switch-bootstrapper
    ```

## Frontend Deployment

### Node.js Requirements
The frontend (Vite) requires **Node.js 18.0 or higher**. Your current error suggests an older version (Node 10/12/14) is being used.

#### Updating Node.js on Ubuntu (ARM/Pi)
```bash
# Using NodeSource (Recommended for Ubuntu)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify version
node -v # Should be v20.x
```

### Deployment Strategy: "Single Service"
The backend is now configured to serve the frontend automatically from the `frontend/dist` folder. This means both API and UI run on port 8000.

1.  **Build Frontend**:
    ```bash
    cd frontend
    npm install
    npm run build
    ```
2.  **Verify**:
    If `frontend/dist` exists, the backend serves the UI at `http://<pi-ip>:8000/`.

> [!TIP]
> If building on the Pi is too slow, you can run `npm run build` on your local PC and upload the `frontend/dist` folder to the Pi manually.

## Troubleshooting

### Port Busy or Permission Denied
- **Symptoms**: `RuntimeError: Serial port not open` or `Permission denied`.
- **Check**: Run `ls -l /home/administrator/port*`. Ensure the user running the service is in the `dialout` group.
- **Check**: Run `fuser /home/administrator/port1` to see if another process is using the port.

### No Prompt Found (Timeout)
- **Symptoms**: `ErrorCode: SERIAL_TIMEOUT` in logs.
- **Check**: Verify the physical connection.
- **Check**: Verify the `SERIAL_BAUDRATE` in `/etc/switch-bootstrapper.env` matches the switch defaults (9600 for Cisco).

### Database Corruption
- **Check**: The SQLite database file is at `/home/administrator/automatic-switch-baselines/automatic_switch.db` by default. You can inspect it with `sqlite3`.

## Upgrade Procedure

1.  Pull latest changes: `git pull`
2.  Update dependencies: `poetry install`
3.  Restart service: `sudo systemctl restart switch-bootstrapper`
