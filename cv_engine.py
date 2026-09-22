import io
import math
from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image


# Demo profiles only.
# Replace these with validated profiles/calibration data for the actual kit.
POSITIVE_TARGET = np.array([205.0, 45.0, 125.0])   # magenta/pink
NEGATIVE_TARGET = np.array([205.0, 220.0, 70.0])   # yellow/green


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode the captured image.")
    return img


def _center_roi(img: np.ndarray, x1: float, y1: float,
                x2: float, y2: float) -> np.ndarray:
    h, w = img.shape[:2]
    xa, ya = int(w * x1), int(h * y1)
    xb, yb = int(w * x2), int(h * y2)
    return img[max(0, ya):min(h, yb), max(0, xa):min(w, xb)]


def _robust_mean_rgb(roi_bgr: np.ndarray) -> np.ndarray:
    if roi_bgr.size == 0:
        raise ValueError("Empty color region.")

    rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
    pixels = rgb.reshape(-1, 3).astype(np.float32)

    # Remove extreme pixels to reduce glare/shadow influence.
    low = np.percentile(pixels, 10, axis=0)
    high = np.percentile(pixels, 90, axis=0)
    mask = np.all((pixels >= low) & (pixels <= high), axis=1)
    kept = pixels[mask] if mask.sum() > 20 else pixels

    return kept.mean(axis=0)


def _calibrate_rgb(rgb: np.ndarray, reference_rgb: np.ndarray) -> np.ndarray:
    # Prototype white/neutral reference calibration.
    # Target neutral brightness is 210 for a demo print card.
    target = 210.0
    ref_luma = (
        0.2126 * reference_rgb[0]
        + 0.7152 * reference_rgb[1]
        + 0.0722 * reference_rgb[2]
    )
    gain = target / max(ref_luma, 1.0)
    gain = float(np.clip(gain, 0.55, 1.8))
    return np.clip(rgb * gain, 0, 255)


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def analyze_image(image_bytes: bytes) -> Dict:
    """
    Prototype CV pipeline.

    Layout assumption for the printed demo card:
      LEFT = reference card
      RIGHT = test strip

    The function intentionally keeps the geometry simple and deterministic
    for a college prototype. A production version should replace fixed ROIs
    with automatic card/strip detection and validated kit-specific models.
    """
    img = _decode_image(image_bytes)
    h, w = img.shape[:2]

    # Reference region: left-center.
    reference_roi = _center_roi(img, 0.05, 0.25, 0.47, 0.75)

    # Test region: right-center.
    test_roi = _center_roi(img, 0.53, 0.25, 0.95, 0.75)

    reference_rgb = _robust_mean_rgb(reference_roi)
    raw_test_rgb = _robust_mean_rgb(test_roi)

    calibrated = _calibrate_rgb(raw_test_rgb, reference_rgb)

    pos_dist = _distance(calibrated, POSITIVE_TARGET)
    neg_dist = _distance(calibrated, NEGATIVE_TARGET)

    nearest = min(pos_dist, neg_dist)

    # Prototype confidence: smaller distance = higher confidence.
    confidence = 100.0 * math.exp(-nearest / 90.0)
    confidence = float(np.clip(confidence, 0, 99.9))

    # If colors are too far from both demo profiles, call inconclusive.
    if nearest > 135:
        classification = "INCONCLUSIVE"
        confidence = float(np.clip(100.0 * math.exp(-nearest / 100.0), 0, 65))
        reason = (
            "The calibrated test color is not sufficiently close to either "
            "the positive or negative demo profile."
        )
    elif pos_dist < neg_dist:
        classification = "POSITIVE"
        reason = (
            "The calibrated test-region color is closer to the prototype "
            "positive profile (magenta/pink)."
        )
    else:
        classification = "NEGATIVE"
        reason = (
            "The calibrated test-region color is closer to the prototype "
            "negative profile (yellow/green)."
        )

    # Reference quality heuristic.
    ref_luma = (
        0.2126 * reference_rgb[0]
        + 0.7152 * reference_rgb[1]
        + 0.0722 * reference_rgb[2]
    )
    calibration = "GOOD" if 45 <= ref_luma <= 245 else "CHECK LIGHTING"

    return {
        "classification": classification,
        "confidence": confidence,
        "distance": nearest,
        "calibration": calibration,
        "reference_rgb": [round(float(x), 1) for x in reference_rgb],
        "test_rgb_raw": [round(float(x), 1) for x in raw_test_rgb],
        "test_rgb_calibrated": [round(float(x), 1) for x in calibrated],
        "reason": reason,
        "image_size": [int(w), int(h)],
    }
