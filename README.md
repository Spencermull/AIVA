# AI Hazard Detection Robot

Robot car controlled by Raspberry Pi AI vision and Arduino motor control.

## Features

- Real-time hazard detection
- Autonomous navigation
- Flask-based control API
- Modular robotics architecture

## Stack

- Raspberry Pi 5
- Arduino Uno
- OpenCV
- YOLOv8 Nano
- Flask

## Flask API

**Purpose:** Control the robot over the network (e.g. from a phone or another computer) instead of using the keyboard. The API runs on the Pi and sends movement commands to the Arduino.

**Start the API server** (on the Pi, from the project root):

```bash
python3 pi/main.py --api
```

Optional: pass the serial port and HTTP port:

```bash
python3 pi/main.py /dev/ttyUSB0 --api --http-port 5000
```

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Check if the server is running |
| POST | `/stop` | Stop the car |
| POST | `/move?direction=forward` | Move (direction: `forward`, `backward`, `left`, `right`) |
| GET | `/telemetry` | See if the serial connection to the Arduino is up |

**Examples** (from another device on the same network; replace `AIVA-V1` with the Pi’s hostname or IP):

```bash
curl http://AIVA-V1:5000/health
curl -X POST http://AIVA-V1:5000/stop
curl -X POST "http://AIVA-V1:5000/move?direction=forward"
curl -X POST http://AIVA-V1:5000/move -H "Content-Type: application/json" -d '{"direction":"left"}'
curl http://AIVA-V1:5000/telemetry
```

**Note:** With `--api`, only the HTTP server runs; keyboard control is off. For keyboard control, run without `--api`.
