/*
===========================================================
Project: AIVA Robot Car
Board: Arduino Uno + Smart Car Shield V1.1
Motor Driver: TB6612FNG (dual DC motor driver)

This Arduino sketch receives single-character commands
from a Raspberry Pi over USB serial (115200 baud) and
controls the robot car motors.

IMPORTANT:
The TB6612FNG motor driver requires the STBY pin to be
set HIGH or the motors will remain disabled.

-----------------------------------------------------------
Motor Driver Pin Mapping (Smart Car Shield V1.1)

Right Motor (Motor A)
  PWMA → D5   (PWM speed control)
  AIN1 → D7   (direction)
  AIN2 → D8   (direction)

Left Motor (Motor B)
  PWMB → D6   (PWM speed control)
  BIN1 → D9   (direction)
  BIN2 → D10  (direction)

Driver Control
  STBY → D3   (must be HIGH to enable motors)

-----------------------------------------------------------
Serial Protocol (from Raspberry Pi)

Baud Rate: 115200

Commands (single character):
  F = Forward
  B = Backward
  L = Turn Left
  R = Turn Right
  S = Stop

Health Check:
  "PING\n" → responds with "PONG"

===========================================================
*/

#define PWMA 5
#define AIN1 7
#define AIN2 8
#define PWMB 6
#define BIN1 9
#define BIN2 10
#define STBY 3

const int MOTOR_SPEED = 200;  // 0-255

void stopMotors() {
  analogWrite(PWMA, 0);
  analogWrite(PWMB, 0);

  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
}

void moveForward(int speed) {
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);

  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void moveBackward(int speed) {
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);

  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void turnLeft(int speed) {
  // Right motor forward, left motor backward
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);

  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void turnRight(int speed) {
  // Right motor backward, left motor forward
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);

  analogWrite(PWMA, speed);
  analogWrite(PWMB, speed);
}

void setup() {
  Serial.begin(115200);

  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);

  pinMode(PWMB, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);

  pinMode(STBY, OUTPUT);

  // Wake up TB6612FNG
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
