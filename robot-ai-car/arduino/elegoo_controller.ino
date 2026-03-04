/*
Elegoo Motor Controller

Purpose:
Handles low-level motor control and sensor reading for the robot.

Responsibilities:
- Parse serial commands from Raspberry Pi
- Control motor direction and speed using PWM
- Implement STOP and movement commands
- Optionally send telemetry data (distance sensors, status)
*/

void setup() {
  Serial.begin(115200);
}

void loop() {
  // Read serial commands and control motors
}

