// Elegoo Smart Robot Car V4.0 — DRV8835 motor controller
// Pins from the official DRV8835 shield (SmartCar-Shield-V1.0):
//   PWMA → D5  (Motor A speed, RIGHT side)
//   PWMB → D6  (Motor B speed, LEFT side)
//   AIN_1 → D8 (Motor A direction: LOW=forward, HIGH=backward)
//   BIN_1 → D7 (Motor B direction: HIGH=forward, LOW=backward)
//
// Serial commands (single char, 115200 baud):
//   F = Forward     B = Backward
//   L = Left        R = Right
//   S = Stop        PING\n = PONG (health-check)

#include <string.h>

#define PIN_Motor_PWMA  5
#define PIN_Motor_PWMB  6
#define PIN_Motor_BIN_1 7
#define PIN_Motor_AIN_1 8

#define DEFAULT_SPEED 200

static const size_t kLineBufferSize = 32;
char lineBuffer[kLineBufferSize];
size_t lineIndex = 0;

// Motor A (right): dirA LOW=forward, HIGH=backward
// Motor B (left):  dirB HIGH=forward, LOW=backward
void motorControl(uint8_t dirA, uint8_t speedA, uint8_t dirB, uint8_t speedB) {
  digitalWrite(PIN_Motor_AIN_1, dirA);
  analogWrite(PIN_Motor_PWMA, speedA);
  digitalWrite(PIN_Motor_BIN_1, dirB);
  analogWrite(PIN_Motor_PWMB, speedB);
}

void handleCommand(char cmd) {
  switch (cmd) {
    case 'F':
      // Forward: A=LOW, B=HIGH
      motorControl(LOW, DEFAULT_SPEED, HIGH, DEFAULT_SPEED);
      break;
    case 'B':
      // Backward: A=HIGH, B=LOW
      motorControl(HIGH, DEFAULT_SPEED, LOW, DEFAULT_SPEED);
      break;
    case 'L':
      // Left: A forward (LOW), B backward (LOW)
      motorControl(LOW, DEFAULT_SPEED, LOW, DEFAULT_SPEED);
      break;
    case 'R':
      // Right: A backward (HIGH), B forward (HIGH)
      motorControl(HIGH, DEFAULT_SPEED, HIGH, DEFAULT_SPEED);
      break;
    case 'S':
    default:
      motorControl(LOW, 0, HIGH, 0);
      break;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_Motor_PWMA, OUTPUT);
  pinMode(PIN_Motor_PWMB, OUTPUT);
  pinMode(PIN_Motor_AIN_1, OUTPUT);
  pinMode(PIN_Motor_BIN_1, OUTPUT);
  motorControl(LOW, 0, HIGH, 0);
}

void loop() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == 'F' || c == 'B' || c == 'L' || c == 'R' || c == 'S') {
      handleCommand(c);
      continue;
    }
    if (c == '\r') continue;
    if (c == '\n') {
      lineBuffer[lineIndex] = '\0';
      if (strncmp(lineBuffer, "PING", 4) == 0) Serial.println("PONG");
      lineIndex = 0;
      continue;
    }
    if (lineIndex < kLineBufferSize - 1) lineBuffer[lineIndex++] = c;
  }
}
