# AIVA Project Context

## Hardware
- **Raspberry Pi 5** (hostname: AIVA-V1, user: aiva) — brain of the robot
- **Arduino Uno** — connected to Pi via USB at `/dev/ttyUSB0`
- **Car**: Elegoo Smart Robot Car V4.0 with DRV8835 motor driver shield
- **Access**: SSH'd into Pi from Windows machine (repo at `C:/Users/caden/source/repos/AIVA`)
- **Camera**: Stock Elegoo camera being replaced with a USB webcam (not yet set up)

## Software Setup
- Python venv at `/home/aiva/AIVA/venv` (Python 3.13)
- `pyserial` installed in venv
- `arduino-cli` installed at `/home/aiva/bin/arduino-cli` on Pi
- Repo cloned at `/home/aiva/AIVA/`
- Run server with: `cd ~/AIVA/pi && python main.py --api`

## Project Structure
```
AIVA/
├── arduino/
│   └── elegoo_controller.ino   # custom Arduino sketch (NOT stock Elegoo firmware)
└── pi/
    ├── main.py          # entry point — use --api flag for Flask server
    ├── serial_bridge.py # serial comms with Arduino
    ├── controller.py    # keyboard control (WASD + arrow keys)
    ├── api_server.py    # Flask REST API
    ├── camera.py        # (scaffolded)
    └── detector.py      # (scaffolded)
```

## Serial Communication
- **Baud rate**: 115200 (both Arduino and serial_bridge.py — already updated)
- **Port**: `/dev/ttyUSB0` — confirmed working
- **Commands**: single char — `F` Forward, `B` Backward, `L` Left, `R` Right, `S` Stop
- `PING\n` → `PONG\r\n` (health check — confirmed working)

## Upload-Cam Switch (CRITICAL)
The Elegoo car board has a physical Upload-Cam switch:
- **"Upload" position**: USB serial (`/dev/ttyUSB0`) routes to Arduino — required for BOTH flashing AND runtime Pi→Arduino communication
- **"Cam" position**: USB routes to camera module; Arduino moves to hardware UART (`/dev/ttyAMA10` = `/dev/serial0`), but this path was tested and did NOT respond
- **Conclusion**: Leave switch permanently on "Upload" — this is the only confirmed working path for serial communication. Camera is being replaced with USB webcam anyway so Cam mode is irrelevant.

## Flashing the Arduino from Pi
```bash
# sketch must live in a folder matching its name
mkdir -p /tmp/elegoo_controller
cp ~/AIVA/arduino/elegoo_controller.ino /tmp/elegoo_controller/

# switch must be on "Upload"
~/bin/arduino-cli compile --fqbn arduino:avr:uno /tmp/elegoo_controller
~/bin/arduino-cli upload  --fqbn arduino:avr:uno --port /dev/ttyUSB0 /tmp/elegoo_controller
```

## TB6612FNG Motor Driver Pin Mapping (confirmed by physical testing)
| Arduino Pin | Function         | Notes                        |
|-------------|------------------|------------------------------|
| D3 (STBY)   | Enable           | Must be HIGH to enable motors|
| D5 (PWMA)   | Motor A speed    | Right side, analogWrite 0-255|
| D6 (PWMB)   | Motor B speed    | Left side, analogWrite 0-255 |
| D7 (BIN_1)  | Motor B direction| HIGH=forward, LOW=backward   |
| D8 (AIN_1)  | Motor A direction| HIGH=forward, LOW=backward   |

**Important**: Both motors use the SAME direction logic (HIGH=forward, LOW=backward). The shield's PCB handles mirrored motor wiring internally. Turns use opposite pin values: turnLeft = AIN1 LOW / BIN1 HIGH, turnRight = AIN1 HIGH / BIN1 LOW.

## Current Status: MOTORS WORKING ✓

### What has been confirmed working:
- Flask server starts and receives HTTP requests ✓
- Serial bridge connects to Arduino on `/dev/ttyUSB0` at 115200 baud ✓
- `PING` → `PONG` round-trip confirmed ✓
- `CMD:F` debug echo returned when `F` sent (Arduino receives and processes commands) ✓
- Flask POST `/move` returns 200 and calls `bridge.send("F")` ✓

### What is NOT working:
- Motors do not physically turn despite Arduino processing the commands

### Next debugging step:
Flash a hardware test sketch that runs the motors automatically in `setup()` (no serial command needed) to determine if the issue is in the pin control code or in the physical hardware/wiring:

```cpp
void setup() {
  Serial.begin(115200);
  pinMode(5, OUTPUT); pinMode(6, OUTPUT);
  pinMode(7, OUTPUT); pinMode(8, OUTPUT);
  Serial.println("Waiting 3s...");
  delay(3000);
  Serial.println("Running motors FORWARD");
  digitalWrite(8, LOW);   // AIN_1 = LOW (Motor A forward)
  analogWrite(5, 200);    // PWMA speed
  digitalWrite(7, HIGH);  // BIN_1 = HIGH (Motor B forward)
  analogWrite(6, 200);    // PWMB speed
  delay(2000);
  Serial.println("Stopping");
  analogWrite(5, 0);
  analogWrite(6, 0);
}
void loop() {}
```

If motors move → pin logic is correct, issue was elsewhere in the command-receiving code.
If motors don't move → pin numbers are wrong or there's a hardware/power issue.

### Things already ruled out:
- Baud rate mismatch (fixed: both now 115200)
- Arduino not receiving commands (confirmed with CMD:F echo)
- Battery not on (user confirmed battery switch on, green light)
- Wrong serial port (ttyUSB0 confirmed working)
- brltty grabbing the port (was disabled in a prior session)

## Goal
Control the Elegoo Smart Car V4.0 from the Raspberry Pi via serial, eventually integrating AI-based hazard detection (USB webcam + detector modules).
