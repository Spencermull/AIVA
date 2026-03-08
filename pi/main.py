import argparse
import sys
from api_server import app, run_server
from serial_bridge import SerialBridge
from controller import run_keyboard_controller


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", default=None)
    parser.add_argument("--api", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--http-port", type=int, default=5000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        with SerialBridge(args.port) as bridge:
            if args.api:
                app.config["bridge"] = bridge
                run_server(host=args.host, port=args.http_port)
            else:
                run_keyboard_controller(bridge)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
