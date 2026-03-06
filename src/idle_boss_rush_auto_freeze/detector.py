from __future__ import annotations

import cv2
import numpy as np

HSV_LOWER = np.array([90, 80, 150])
HSV_UPPER = np.array([115, 255, 255])

MIN_AREA = 150
MAX_AREA = 800
MIN_CIRCULARITY = 0.35
MAX_MEAN_V = 175
MIN_DEDUP_DIST = 30

MORPH_KERNEL = np.ones((3, 3), np.uint8)


def _mean_brightness(
    hsv: np.ndarray, mask: np.ndarray, x: int, y: int, w: int, h: int,
) -> float:
    roi_v = hsv[y:y + h, x:x + w, 2]
    roi_mask = mask[y:y + h, x:x + w]
    masked = roi_v[roi_mask > 0]
    if masked.size == 0:
        return 255.0
    return float(np.mean(masked))


def _is_duplicate(cx: int, cy: int, points: list[tuple[int, int]]) -> bool:
    return any(
        abs(cx - px) < MIN_DEDUP_DIST and abs(cy - py) < MIN_DEDUP_DIST
        for px, py in points
    )


def find_freeze_icons(screen_bgr: np.ndarray) -> list[tuple[int, int]]:
    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    mask = cv2.dilate(mask, MORPH_KERNEL, iterations=2)
    mask = cv2.erode(mask, MORPH_KERNEL, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    points: list[tuple[int, int]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if not (MIN_AREA <= area <= MAX_AREA):
            continue

        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity < MIN_CIRCULARITY:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if _mean_brightness(hsv, mask, x, y, w, h) > MAX_MEAN_V:
            continue

        cx, cy = x + w // 2, y + h // 2
        if not _is_duplicate(cx, cy, points):
            points.append((cx, cy))

    return points


def find_freeze_icons_debug(
    screen_bgr: np.ndarray,
) -> tuple[list[tuple[int, int]], np.ndarray]:
    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    mask = cv2.dilate(mask, MORPH_KERNEL, iterations=2)
    mask = cv2.erode(mask, MORPH_KERNEL, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    annotated = screen_bgr.copy()
    points: list[tuple[int, int]] = []

    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        cx, cy = x + w // 2, y + h // 2

        if not (MIN_AREA <= area <= MAX_AREA):
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 1)
            cv2.putText(annotated, f"a={area:.0f}", (x, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            continue

        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
        if circularity < MIN_CIRCULARITY:
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 255), 1)
            cv2.putText(annotated, f"c={circularity:.2f}", (x, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
            continue

        mv = _mean_brightness(hsv, mask, x, y, w, h)
        if mv > MAX_MEAN_V:
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 165, 255), 1)
            cv2.putText(annotated, f"v={mv:.0f}", (x, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 165, 255), 1)
            continue

        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(annotated, f"FREEZE v={mv:.0f}",
                    (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)

        if not _is_duplicate(cx, cy, points):
            points.append((cx, cy))

    return points, annotated
