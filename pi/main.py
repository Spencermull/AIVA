"""Main Robot Application

Purpose:
Entry point for the Raspberry Pi AI robot system.

Responsibilities:
- Initialize camera
- Run hazard detection loop
- Send movement commands based on AI results
- Coordinate detector, controller, and API modules
"""

import sys
from serial_bridge import SerialBridge
from controller import run_keyboard_controller


def main() -> None:
    """Application entry point."""
    port = sys.argv[1] if len(sys.argv) > 1 else None  # optional: pass port as arg

    try:
        with SerialBridge(port) as bridge:
            run_keyboard_controller(bridge)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
