"""
sign_classifier.py — Secondary sign classifier for AIVA.

Runs alongside YOLO (yolo11n.pt) to detect Alberta signs not in COCO:
  LEFT, RIGHT, DEAD END, PED CROSSING
and reinforces the COCO stop sign detection.

Strategy
--------
1. YOLO already fires on class 11 (stop sign).  We accept that directly.
2. For turn signs (green circle on white square) and ped crossing (white on white),
   we use HSV colour masking to find candidate regions, then rank them against
   template images via normalised cross-correlation (cv2.matchTemplate TM_CCOEFF_NORMED).
3. Dead-end sign is the yellow/black checkerboard diamond — detected via HSV yellow mask.

Templates
---------
Place 64×64 px greyscale PNGs in  pi/sign_templates/:
    left.png          right.png
    ped_crossing.png  dead_end.png

If a template file is missing the class is simply skipped (no crash).

Usage
-----
    clf = SignClassifier()                     # load templates once
    results = clf.classify(frame, yolo_boxes)  # call every frame
    for r in results:
        print(r.label, r.conf, r.xyxy)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

TEMPLATE_DIR = Path(__file__).parent / "sign_templates"
TEMPLATE_SIZE = (64, 64)

# HSV ranges (H in 0-179, S/V in 0-255)
# Green circle signs (turn signs, ped crossing)
GREEN_LOWER = np.array([40,  80, 80],  dtype=np.uint8)
GREEN_UPPER = np.array([85, 255, 255], dtype=np.uint8)

# Yellow diamond (dead end)
YELLOW_LOWER = np.array([18,  120, 120], dtype=np.uint8)
YELLOW_UPPER = np.array([35,  255, 255], dtype=np.uint8)

# Red octagon (stop — backup if YOLO misses it)
RED_LOWER1 = np.array([0,   120, 100], dtype=np.uint8)
RED_UPPER1 = np.array([8,   255, 255], dtype=np.uint8)
RED_LOWER2 = np.array([170, 120, 100], dtype=np.uint8)
RED_UPPER2 = np.array([179, 255, 255], dtype=np.uint8)

# Minimum contour area (px²) to bother classifying
MIN_AREA = 900   # ~30×30
MAX_AREA = 80000 # ignore huge regions (sky, car body)

MATCH_THRESHOLD = 0.45  # normalised cross-correlation minimum


@dataclass
class SignResult:
    label: str          # 'LEFT' | 'RIGHT' | 'DEAD_END' | 'PED_CROSSING' | 'STOP'
    conf:  float        # template match score 0–1  (1.0 = YOLO-sourced stop sign)
    xyxy:  tuple[int, int, int, int]   # bounding box in original frame coords


class SignClassifier:
    def __init__(self, template_dir: Path = TEMPLATE_DIR, threshold: float = MATCH_THRESHOLD):
        self.threshold = threshold
        self.templates: dict[str, np.ndarray] = {}
        self._load_templates(template_dir)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_templates(self, template_dir: Path) -> None:
        mapping = {
            "LEFT":         "left.png",
            "RIGHT":        "right.png",
            "PED_CROSSING": "ped_crossing.png",
            "DEAD_END":     "dead_end.png",
        }
        for label, fname in mapping.items():
            p = template_dir / fname
            if not p.exists():
                continue
            img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            self.templates[label] = cv2.resize(img, TEMPLATE_SIZE)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, frame: np.ndarray, yolo_boxes=None) -> list[SignResult]:
        """
        Parameters
        ----------
        frame       : BGR frame from camera
        yolo_boxes  : ultralytics Boxes object (result.boxes) or None

        Returns
        -------
        List of SignResult, one per detected sign.  May be empty.
        """
        results: list[SignResult] = []

        # 1. Pass through YOLO stop-sign detections directly
        results.extend(self._extract_yolo_stops(frame, yolo_boxes))

        # 2. HSV candidate extraction
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Green-circle signs → LEFT / RIGHT / PED_CROSSING
        green_candidates = self._mask_candidates(frame, hsv, GREEN_LOWER, GREEN_UPPER)
        for crop, xyxy in green_candidates:
            match = self._best_template_match(crop, ["LEFT", "RIGHT", "PED_CROSSING"])
            if match:
                label, score = match
                results.append(SignResult(label=label, conf=score, xyxy=xyxy))

        # Yellow diamond → DEAD_END
        yellow_candidates = self._mask_candidates(frame, hsv, YELLOW_LOWER, YELLOW_UPPER)
        for crop, xyxy in yellow_candidates:
            match = self._best_template_match(crop, ["DEAD_END"])
            if match:
                label, score = match
                results.append(SignResult(label=label, conf=score, xyxy=xyxy))

        # Red octagon → STOP (fallback if YOLO missed it)
        yolo_stop_boxes = {r.xyxy for r in results if r.label == "STOP"}
        red_candidates = self._mask_candidates_red(frame, hsv)
        for crop, xyxy in red_candidates:
            if self._overlaps_any(xyxy, yolo_stop_boxes):
                continue  # already captured by YOLO
            # Red octagon is distinctive enough to accept on colour alone
            results.append(SignResult(label="STOP", conf=0.6, xyxy=xyxy))

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_yolo_stops(self, frame: np.ndarray, yolo_boxes) -> list[SignResult]:
        out = []
        if yolo_boxes is None or len(yolo_boxes) == 0:
            return out
        try:
            xyxy_arr = yolo_boxes.xyxy.cpu().numpy()
            cls_arr  = yolo_boxes.cls.cpu().numpy().astype(int)
            conf_arr = yolo_boxes.conf.cpu().numpy()
        except Exception:
            return out
        for i in range(len(xyxy_arr)):
            if int(cls_arr[i]) == 11:  # COCO stop sign
                x1, y1, x2, y2 = (int(v) for v in xyxy_arr[i])
                out.append(SignResult(
                    label="STOP",
                    conf=float(conf_arr[i]),
                    xyxy=(x1, y1, x2, y2),
                ))
        return out

    def _mask_candidates(
        self,
        frame: np.ndarray,
        hsv: np.ndarray,
        lower: np.ndarray,
        upper: np.ndarray,
    ) -> list[tuple[np.ndarray, tuple[int, int, int, int]]]:
        mask = cv2.inRange(hsv, lower, upper)
        return self._contours_to_crops(frame, mask)

    def _mask_candidates_red(
        self,
        frame: np.ndarray,
        hsv: np.ndarray,
    ) -> list[tuple[np.ndarray, tuple[int, int, int, int]]]:
        mask = cv2.inRange(hsv, RED_LOWER1, RED_UPPER1) | cv2.inRange(hsv, RED_LOWER2, RED_UPPER2)
        return self._contours_to_crops(frame, mask)

    def _contours_to_crops(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
    ) -> list[tuple[np.ndarray, tuple[int, int, int, int]]]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame.shape[:2]
        crops = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (MIN_AREA <= area <= MAX_AREA):
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Expand bounding box slightly to capture full sign
            pad = 8
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(w, x + bw + pad)
            y2 = min(h, y + bh + pad)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            crops.append((crop, (x1, y1, x2, y2)))
        return crops

    def _best_template_match(
        self,
        crop: np.ndarray,
        labels: list[str],
    ) -> Optional[tuple[str, float]]:
        """Return (label, score) for the best matching template above threshold."""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, TEMPLATE_SIZE)
        best_label: Optional[str] = None
        best_score: float = self.threshold
        for label in labels:
            tmpl = self.templates.get(label)
            if tmpl is None:
                continue
            res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, _ = cv2.minMaxLoc(res)
            if score > best_score:
                best_score = score
                best_label = label
        if best_label is None:
            return None
        return best_label, best_score

    @staticmethod
    def _overlaps_any(
        xyxy: tuple[int, int, int, int],
        boxes: set[tuple[int, int, int, int]],
        iou_thresh: float = 0.3,
    ) -> bool:
        for other in boxes:
            if SignClassifier._iou(xyxy, other) >= iou_thresh:
                return True
        return False

    @staticmethod
    def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1 = max(ax1, bx1); iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2); iy2 = min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        if inter == 0:
            return 0.0
        union = (ax2-ax1)*(ay2-ay1) + (bx2-bx1)*(by2-by1) - inter
        return inter / union if union > 0 else 0.0