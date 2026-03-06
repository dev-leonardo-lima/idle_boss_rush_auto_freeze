"""Auto-clicker for freeze icons in Idle Boss Rush (Steam).

Detects freeze power-up icons on screen using HSV color filtering,
contour shape analysis, and mean brightness thresholding, then
clicks them automatically via pyautogui.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import cv2
import mss
import numpy as np
import pyautogui

from idle_boss_rush_auto_freeze.detector import (
    find_freeze_icons,
    find_freeze_icons_debug,
)

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

DEFAULT_COMBAT_REGION = (200, 100, 950, 650)


def capture_screen(
    sct: mss.mss,
    region: tuple[int, int, int, int],
) -> tuple[np.ndarray, int, int]:
    x, y, w, h = region
    monitor = {"left": x, "top": y, "width": w, "height": h}
    screenshot = sct.grab(monitor)
    img = np.array(screenshot)
    bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return bgr, x, y


def run(
    interval: float = 0.1,
    region: tuple[int, int, int, int] = DEFAULT_COMBAT_REGION,
    debug: bool = False,
) -> None:
    logger.info(
        "Starting auto-freeze (interval=%.2fs, region=%s, debug=%s)",
        interval, region, debug,
    )
    logger.info("Move mouse to top-left corner to abort (fail-safe).")

    clicks_total = 0
    frame_count = 0

    with mss.mss() as sct:
        while True:
            bgr, off_x, off_y = capture_screen(sct, region)

            if debug:
                matches, annotated = find_freeze_icons_debug(bgr)
                frame_count += 1
                if frame_count % 50 == 1 or matches:
                    debug_path = f"debug_frame_{frame_count:04d}.png"
                    cv2.imwrite(debug_path, annotated)
                    logger.debug("Debug frame saved: %s", debug_path)
            else:
                matches = find_freeze_icons(bgr)

            for mx, my in matches:
                screen_x = mx + off_x
                screen_y = my + off_y
                pyautogui.click(screen_x, screen_y)
                clicks_total += 1
                logger.debug(
                    "Click #%d at (%d, %d)", clicks_total, screen_x, screen_y
                )

            if matches:
                logger.info(
                    "Found %d icon(s) — total clicks: %d",
                    len(matches), clicks_total,
                )

            time.sleep(interval)


def parse_region(value: str) -> tuple[int, int, int, int]:
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("Region must be x,y,w,h (e.g. 200,100,950,650)")
    try:
        return tuple(int(p.strip()) for p in parts)  # type: ignore[return-value]
    except ValueError:
        raise argparse.ArgumentTypeError("All region values must be integers")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-clicker for freeze icons in Idle Boss Rush",
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=0.1,
        help="Seconds between screen scans (default: 0.1)",
    )
    parser.add_argument(
        "-r", "--region", type=parse_region,
        default=DEFAULT_COMBAT_REGION,
        help="Screen capture region as x,y,w,h (default: 200,100,950,650)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show debug-level logs (every click)",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Save annotated screenshots for each frame with detections",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        run(
            interval=args.interval,
            region=args.region,
            debug=args.debug,
        )
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
