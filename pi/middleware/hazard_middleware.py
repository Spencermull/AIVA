"""
Hazard middleware: YOLO camera stream -> evasion decision -> Flask /move and /stop.

Run the Flask API in a separate process first (python main.py --api) so this
process only uses HTTP and does not compete for the serial port.

Evasion assumes the vehicle is driving forward; lateral threats steer away from
the side where the hazard sits in the image. Centered blocking hazards trigger
stop (and optional short backup if configured).
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable, Optional

import cv2
import numpy as np
import requests
from ultralytics import YOLO

# COCO class IDs aligned with street-detection-model (traffic-related hazards)
HAZARD_CLASS_NAMES: dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    9: "traffic light",
    11: "stop sign",
}

HAZARD_CLASS_IDS: list[int] = list(HAZARD_CLASS_NAMES.keys())

# Regulators that should bias toward stopping rather than swerving
STOP_BIAS_CLASS_IDS: frozenset[int] = frozenset({9, 11})


def _intersects_ahead_roi(
    xyxy: np.ndarray,
    width: int,
    height: int,
    roi_y0_frac: float = 0.42,
    roi_x0_frac: float = 0.12,
    roi_x1_frac: float = 0.88,
) -> bool:
    """True if box overlaps the lower-center 'road ahead' region."""
    x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
    roi_y0 = height * roi_y0_frac
    roi_x0 = width * roi_x0_frac
    roi_x1 = width * roi_x1_frac
    if y2 < roi_y0:
        return False
    if x2 < roi_x0 or x1 > roi_x1:
        return False
    return True


def _largest_ahead_threat(
    boxes,
    width: int,
    height: int,
) -> Optional[tuple[float, float, int]]:
    """
    Returns (center_x, area, class_id) for the largest hazard in the ahead ROI,
    or None.
    """
    if boxes is None or len(boxes) == 0:
        return None
    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy().astype(int)
    best: Optional[tuple[float, float, int]] = None
    for i in range(len(xyxy)):
        c = int(cls[i])
        if c not in HAZARD_CLASS_NAMES:
            continue
        row = xyxy[i]
        if not _intersects_ahead_roi(row, width, height):
            continue
        x1, y1, x2, y2 = row
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        cx = (x1 + x2) * 0.5
        if best is None or area > best[1]:
            best = (cx, area, c)
    return best


def _choose_action(
    frame_width: int,
    threat: Optional[tuple[float, float, int]],
    center_deadband_frac: float = 0.08,
) -> Optional[str]:
    """
    Map threat position to API direction: left, right, stop, or None (no action).
    """
    if threat is None:
        return None
    cx, _area, cls_id = threat
    if cls_id in STOP_BIAS_CLASS_IDS:
        return "stop"  # API maps stop separately via /stop
    mid = frame_width * 0.5
    band = frame_width * center_deadband_frac
    if abs(cx - mid) <= band:
        return "backward"
    if cx < mid:
        return "right"
    return "left"


class FlaskMovementClient:
    def __init__(self, base_url: str, timeout_s: float = 3.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=self.timeout_s)
            return r.ok
        except requests.RequestException:
            return False

    def move(self, direction: str) -> bool:
        try:
            r = requests.post(
                f"{self.base_url}/move",
                json={"direction": direction},
                timeout=self.timeout_s,
            )
            return r.ok
        except requests.RequestException:
            return False

    def stop(self) -> bool:
        try:
            r = requests.post(f"{self.base_url}/stop", timeout=self.timeout_s)
            return r.ok
        except requests.RequestException:
            return False


def run_hazard_middleware(
    *,
    api_base: str = "http://127.0.0.1:5000",
    camera_index: int = 0,
    model_path: str = "yolo11n.pt",
    conf: float = 0.35,
    imgsz: int = 640,
    min_command_interval_s: float = 0.35,
    clear_hold_s: float = 0.6,
    window: bool = True,
) -> None:
    client = FlaskMovementClient(api_base)
    if not client.health():
        print(
            "Warning: Flask API health check failed. Start the API with:\n"
            "  python main.py --api\n"
            f"Continuing anyway (target: {api_base}).",
            file=sys.stderr,
        )

    model = YOLO(model_path)
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}")

    last_cmd_wall: float = 0.0
    last_sent: Optional[str] = None
    last_hazard_wall: float = 0.0
    saw_hazard: bool = False

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            height, width = frame.shape[:2]
            results = model.predict(
                source=frame,
                conf=conf,
                imgsz=imgsz,
                classes=HAZARD_CLASS_IDS,
                verbose=False,
            )
            result = results[0]
            threat = _largest_ahead_threat(result.boxes, width, height)
            now = time.time()

            if threat is not None:
                last_hazard_wall = now
                saw_hazard = True

            # After hazards clear, stop so the car does not keep circling
            if (
                threat is None
                and saw_hazard
                and (now - last_hazard_wall) > clear_hold_s
            ):
                if last_sent != "clear":
                    client.stop()
                    last_sent = "clear"
                if window:
                    cv2.imshow("AIVA hazard middleware", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            action = _choose_action(width, threat)
            if action is None:
                if window:
                    cv2.imshow("AIVA hazard middleware", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            if action == "stop":
                api_action = "stop"
            else:
                api_action = action

            if (now - last_cmd_wall) < min_command_interval_s and api_action == last_sent:
                if window:
                    cv2.imshow("AIVA hazard middleware", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            if api_action == "stop":
                ok_stop = client.stop()
                last_cmd_wall = now
                last_sent = "stop"
                if not ok_stop:
                    print("Failed POST /stop", file=sys.stderr)
            else:
                ok_move = client.move(api_action)
                last_cmd_wall = now
                last_sent = api_action
                if not ok_move:
                    print(f"Failed POST /move ({api_action})", file=sys.stderr)

            if window:
                label = f"threat -> {api_action}"
                cv2.putText(
                    frame,
                    label,
                    (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 200, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow("AIVA hazard middleware", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cap.release()
        client.stop()
        if window:
            cv2.destroyAllWindows()


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="YOLO -> Flask hazard middleware")
    parser.add_argument("--api-base", default="http://127.0.0.1:5000")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--min-interval", type=float, default=0.35)
    parser.add_argument("--clear-hold", type=float, default=0.6)
    parser.add_argument("--no-window", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    run_hazard_middleware(
        api_base=args.api_base,
        camera_index=args.camera,
        model_path=args.model,
        conf=args.conf,
        imgsz=args.imgsz,
        min_command_interval_s=args.min_interval,
        clear_hold_s=args.clear_hold,
        window=not args.no_window,
    )


if __name__ == "__main__":
    main()
