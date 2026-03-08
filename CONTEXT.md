# AIVA Project Context

## Hardware
- **Raspberry Pi** (hostname: AIVA-V1, user: aiva) — brain of the robot
- **Arduino** — connected to Pi via USB at `/dev/ttyUSB0`
- **Car**: Elegoo Smart Car V4.0 — Arduino flashed with stock Elegoo firmware
- **Access**: SSH'd into Pi from iPhone

## Software Setup
- Python venv at `/home/aiva/AIVA/venv` (Python 3.13)
- `pyserial 3.5` installed in venv
- Repo cloned at `/home/aiva/AIVA/`
- Run with: `python3 pi/main.py /dev/ttyUSB0`

## Project Structure
```
AIVA/
└── pi/
    ├── main.py          # entry point
    ├── serial_bridge.py # serial comms with Arduino
    ├── controller.py    # keyboard control (WASD + arrow keys)
    ├── camera.py        # (scaffolded)
    ├── detector.py      # (scaffolded)
    └── api_server.py    # (scaffolded)
```

## Serial Communication
- Baud rate: 9600 (stock Elegoo firmware)
- Commands: `F` Forward, `B` Backward, `L` Left, `R` Right, `S` Stop
- **Status**: Connected successfully, but motor response unconfirmed — debugging in progress

## Known Issues / Notes
- `brltty` service was grabbing `/dev/ttyUSB0` — disabled with `systemctl disable brltty --now`
- If port busy again: `sudo fuser -k /dev/ttyUSB0`
- Car battery pack must be switched on separately for motors to run (Arduino powers from USB only)
- Elegoo firmware command protocol not yet confirmed — may need 115200 baud or `\n` line endings

## Goal
Control the Elegoo Smart Car V4.0 from the Raspberry Pi via serial, eventually integrating AI-based hazard detection (camera + detector modules).
