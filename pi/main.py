import argparse
import sys
from api_server import app, run_server
from serial_bridge import SerialBridge
from controller import run_keyboard_controller
from middleware.hazard_middleware import run_hazard_middleware


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", default=None)
    parser.add_argument("--api", action="store_true")
    parser.add_argument(
        "--middleware",
        action="store_true",
        help="YOLO hazard avoidance via HTTP to the Flask API (run --api separately)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--http-port", type=int, default=5000)
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:5000",
        help="Flask base URL for --middleware (default: local 5000)",
    )
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--mw-conf", type=float, default=0.35)
    parser.add_argument("--mw-imgsz", type=int, default=640)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.middleware:
        if args.api:
            print(
                "Use two terminals: one with --api, one with --middleware "
                "(both modes need exclusive serial access).",
                file=sys.stderr,
            )
            sys.exit(2)
        try:
            run_hazard_middleware(
                api_base=args.api_base,
                camera_index=args.camera,
                model_path=args.model,
                conf=args.mw_conf,
                imgsz=args.mw_imgsz,
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            pass
        return

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
