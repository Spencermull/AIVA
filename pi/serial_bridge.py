import serial
import time
import glob


def find_arduino_port() -> str:
    """Auto-detect Arduino serial port."""
    candidates = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    if not candidates:
        raise RuntimeError("No Arduino found. Check USB connection.")
    return candidates[0]


class SerialBridge:
    BAUD = 115200
    RESET_DELAY = 2.0  # seconds to wait for Arduino reset after connect

    def __init__(self, port: str = None):
        self.port = port or find_arduino_port()
        self._ser = None

    def connect(self) -> None:
        print(f"Connecting to Arduino on {self.port} at {self.BAUD} baud...")
        self._ser = serial.Serial(self.port, self.BAUD, timeout=1)
        time.sleep(self.RESET_DELAY)
        print("Connected.")

    def send(self, cmd: str) -> None:
        """Send a single-character command to the Arduino."""
        if self._ser and self._ser.is_open:
            self._ser.write(cmd.encode())

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self.send("S")  # stop the car before disconnecting
            self._ser.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()
