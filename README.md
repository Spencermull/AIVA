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

## Serial ping (Pi ↔ Arduino)

1. Upload **arduino/elegoo_controller.ino** to the Arduino (Arduino IDE: open sketch → select board/port → Upload).
2. Connect the Arduino to the Pi with a USB cable.
3. On the Pi, from the repo:  
   `cd pi && python ping_arduino.py`  
   You should see **PONG** in the console.
4. If the port isn’t `/dev/ttyUSB0`, set it before running:  
   `SERIAL_PORT=/dev/ttyUSB1 python ping_arduino.py`  
   (use the port you see in `ls /dev/ttyUSB*` or `ls /dev/serial/by-id/`).
