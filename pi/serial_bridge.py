import os

import serial


def open_serial_port(port=None, baudrate=115200, timeout=1.0):
    selected_port = port or os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
    return serial.Serial(selected_port, baudrate=baudrate, timeout=timeout)


def ping_arduino(port=None):
    with open_serial_port(port=port) as conn:
        conn.reset_input_buffer()
        conn.write(b"PING\n")
        conn.flush()
        return conn.readline().decode("utf-8", errors="replace").strip()
