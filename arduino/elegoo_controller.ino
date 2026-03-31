/*
===========================================================
Project: AIVA Robot Car
Board: Arduino Uno + Elegoo Smart Car V4.0 Shield
Motor Driver: DRV8835 (phase/enable mode)

This Arduino sketch receives single-character commands
from a Raspberry Pi over USB serial (115200 baud) and
controls the robot car motors.

-----------------------------------------------------------
DRV8835 Pin Mapping (Elegoo Smart Car V4.0)

Right Motor (Motor A)
  PWMA  → D5   (PWM speed control, analogWrite 0-255)
  AIN_1 → D8   (direction: LOW=forward, HIGH=backward)

Left Motor (Motor B)
  PWMB  → D6   (PWM speed control, analogWrite 0-255)
  BIN_1 → D7   (direction: LOW=forward, HIGH=backward)

Enable
  STBY  → D3   (must be HIGH to enable motors)

NOTE: Both motors use the SAME direction logic (LOW=fwd).
The shield's PCB handles the mirrored motor wiring internally.

-----------------------------------------------------------
Serial Protocol (from Raspberry Pi)

Baud Rate: 115200

Commands (single character):
  F = Forward
  B = Backward
  L = Turn Left
  R = Turn Right
  S = Stop

===========================================================
*/

#define PWMA 5    // Right motor speed
#define AIN1 8    // Right motor direction (HIGH=fwd, LOW=bwd)
#define PWMB 6    // Left motor speed
#define BIN1 7    // Left motor direction (HIGH=fwd, LOW=bwd)
#define STBY 3    // Enable pin (must be HIGH)

const int MOTOR_SPEED = 200;  // 0-255

void stopMotors() {
  analogWrite(PWMA, 0);
  analogWrite(PWMB, 0);
}

void moveForward(int speed) {
  digitalWrite(AIN1, HIGH);  // Right motor forward
  digitalWrite(BIN1, HIGH);  // Left motor forward
  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void moveBackward(int speed) {
  digitalWrite(AIN1, LOW);   // Right motor backward
  digitalWrite(BIN1, LOW);   // Left motor backward
  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void turnLeft(int speed) {
  // Right motor forward, left motor backward
  digitalWrite(AIN1, LOW);
  digitalWrite(BIN1, HIGH);
  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void turnRight(int speed) {
  // Right motor backward, left motor forward
  digitalWrite(AIN1, HIGH);
  digitalWrite(BIN1, LOW);
  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void setup() {
  Serial.begin(115200);

  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(PWMB, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(STBY, OUTPUT);

  // Enable the motor driver
  digitalWrite(STBY, HIGH);

  stopMotors();

  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    // Ignore newline / carriage return
    if (cmd == '\n' || cmd == '\r') {
      return;
    }

    Serial.print("CMD:");
    Serial.println(cmd);

    switch (cmd) {
      case 'F':
        moveForward(MOTOR_SPEED);
        break;

      case 'B':
        moveBackward(MOTOR_SPEED);
        break;

      case 'L':
        turnLeft(MOTOR_SPEED);
        break;

      case 'R':
        turnRight(MOTOR_SPEED);
        break;

      case 'S':
        stopMotors();
        break;

      default:
        stopMotors();
        Serial.println("UNKNOWN");
        break;
    }
  }
}
