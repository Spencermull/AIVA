#include <string.h>

static const size_t kLineBufferSize = 32;
char lineBuffer[kLineBufferSize];
size_t lineIndex = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
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
