// Elegoo Smart Robot Car V4.0 — DRV8835 motor controller
// Pins from the official DRV8835 shield (SmartCar-Shield-V1.0):
//   PWMA → D5  (Motor A speed, left side)
//   PWMB → D6  (Motor B speed, right side)
//   BIN_1 → D7 (Motor B direction)
//   AIN_1 → D8 (Motor A direction)
//
// DRV8835 PHASE/ENABLE mode:
//   direction HIGH (1) = forward
//   direction LOW  (0) = backward
//   speed 0-255 via analogWrite (PWM)
//
// Serial commands (single char, 115200 baud):
//   F = Forward     B = Backward
//   L = Left        R = Right
//   S = Stop        PING\n = PONG (health-check)

#include <string.h>

#define PIN_Motor_PWMA 5
#define PIN_Motor_PWMB 6
#define PIN_Motor_BIN_1 7
#define PIN_Motor_AIN_1 8

#define DEFAULT_SPEED 200

static const size_t kLineBufferSize = 32;
char lineBuffer[kLineBufferSize];
size_t lineIndex = 0;

// Drive both motors.
// dirA / dirB: HIGH = forward, LOW = backward
// speedA / speedB: 0-255
void motorControl(uint8_t dirA, uint8_t speedA,
                  uint8_t dirB, uint8_t speedB) {
  digitalWrite(PIN_Motor_AIN_1, dirA);
  analogWrite(PIN_Motor_PWMA, speedA);
  digitalWrite(PIN_Motor_BIN_1, dirB);
  analogWrite(PIN_Motor_PWMB, speedB);
}

void handleCommand(char cmd) {
  switch (cmd) {
    case 'F':
      // Forward: both motors forward, full speed
      motorControl(HIGH, DEFAULT_SPEED, HIGH, DEFAULT_SPEED);
      break;
    case 'B':
      // Backward: both motors backward, full speed
      motorControl(LOW, DEFAULT_SPEED, LOW, DEFAULT_SPEED);
      break;
    case 'L':
      // Left: motor A forward, motor B backward (spin left)
      motorControl(HIGH, DEFAULT_SPEED, LOW, DEFAULT_SPEED);
      break;
    case 'R':
      // Right: motor A backward, motor B forward (spin right)
      motorControl(LOW, DEFAULT_SPEED, HIGH, DEFAULT_SPEED);
      break;
    case 'S':
    default:
      // Stop: zero speed on both motors
      motorControl(HIGH, 0, HIGH, 0);
      break;
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_Motor_PWMA, OUTPUT);
  pinMode(PIN_Motor_PWMB, OUTPUT);
  pinMode(PIN_Motor_AIN_1, OUTPUT);
  pinMode(PIN_Motor_BIN_1, OUTPUT);

  // Start stopped
  motorControl(HIGH, 0, HIGH, 0);
}

void loop() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());

    // Single-character commands — handle immediately
    if (c == 'F' || c == 'B' || c == 'L' || c == 'R' || c == 'S') {
      handleCommand(c);
      continue;
    }

    // Line-buffered commands (e.g. PING\n)
    if (c == '\r') {
      continue;
    }
    if (c == '\n') {
      lineBuffer[lineIndex] = '\0';
      if (strncmp(lineBuffer, "PING", 4) == 0) {
        Serial.println("PONG");
      }
      lineIndex = 0;
      continue;
    }
    if (lineIndex < kLineBufferSize - 1) {
      lineBuffer[lineIndex++] = c;
    }
  }
}
