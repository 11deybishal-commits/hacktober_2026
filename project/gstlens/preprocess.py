"""
GSTLens Image Preprocessor for Real Camera Shots & Scans.
Provides EXIF auto-rotation, 4-corner perspective warping, deskewing,
shadow/illumination correction via CLAHE, quality scoring, and crop extraction.
"""
import os
import io
import cv2
import numpy as np
from PIL import Image, ImageOps
from typing import Tuple, Dict, Any, Optional, List


def load_image(image_path_or_bytes: Any) -> np.ndarray:
    """
    Loads an image into a standard BGR numpy array.
    Automatically applies EXIF orientation correction so phone camera photos
    taken in portrait or rotated angles are correctly oriented.
    """
    if isinstance(image_path_or_bytes, str):
        if not os.path.exists(image_path_or_bytes):
            raise FileNotFoundError(f"Image file not found: {image_path_or_bytes}")
        try:
            pil_img = Image.open(image_path_or_bytes)
            # Correct EXIF orientation
            pil_img = ImageOps.exif_transpose(pil_img)
            rgb_img = pil_img.convert("RGB")
            return cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
        except Exception:
            img = cv2.imread(image_path_or_bytes)
            if img is not None:
                return img
            raise ValueError(f"Failed to load image from {image_path_or_bytes}")

    elif isinstance(image_path_or_bytes, bytes):
        try:
            pil_img = Image.open(io.BytesIO(image_path_or_bytes))
            pil_img = ImageOps.exif_transpose(pil_img)
            rgb_img = pil_img.convert("RGB")
            return cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
        except Exception:
            nparr = np.frombuffer(image_path_or_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                return img
            raise ValueError("Failed to decode image from bytes")

    elif isinstance(image_path_or_bytes, np.ndarray):
        return image_path_or_bytes

    elif isinstance(image_path_or_bytes, Image.Image):
        pil_img = ImageOps.exif_transpose(image_path_or_bytes)
        return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

    else:
        raise ValueError(f"Unsupported image input type: {type(image_path_or_bytes)}")


def order_points(pts: np.ndarray) -> np.ndarray:
    """Orders 4 coordinates: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-left has smallest sum
    rect[2] = pts[np.argmax(s)]  # Bottom-right has largest sum

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right has smallest diff
    rect[3] = pts[np.argmax(diff)]  # Bottom-left has largest diff
    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Applies perspective transform to flatten a 4-point quadrilateral into a rectangle."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute width of new image
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    # Compute height of new image
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    return warped


def detect_document_corners_and_warp(image: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Detects paper boundaries of a bill sitting on a desk/table and unwarps perspective.
    Returns (warped_image, was_warped).
    """
    if image is None or image.size == 0:
        return image, False

    h, w = image.shape[:2]
    # Downscale for fast contour detection
    scale = 800.0 / max(h, w) if max(h, w) > 800 else 1.0
    small = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection and morphology
    edged = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edged, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            area = cv2.contourArea(approx)
            # Must occupy at least 30% of the image area to be considered the document
            if area > (small.shape[0] * small.shape[1] * 0.30):
                orig_pts = approx.reshape(4, 2) / scale
                warped = four_point_transform(image, orig_pts)
                return warped, True

    return image, False


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Corrects minor camera rotation/skew using Hough line transform."""
    if image is None or image.size == 0:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)

    if lines is None:
        return image

    angles = []
    for line in lines:
        coords = line[0] if (hasattr(line, "__len__") and len(line) == 1 and hasattr(line[0], "__len__")) else line
        if hasattr(coords, "__len__") and len(coords) == 4:
            x1, y1, x2, y2 = coords
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Keep horizontal-ish lines
            if abs(angle) < 45:
                angles.append(angle)

    if not angles:
        return image

    median_angle = np.median(angles)
    if abs(median_angle) < 0.5:
        return image  # Negligible skew

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def enhance_for_camera(image: np.ndarray) -> np.ndarray:
    """
    Removes lighting shadows and flash glare using CLAHE on the L-channel in LAB space.
    Enhances contrast of faint handwriting and printed thermal ink.
    """
    if image is None or image.size == 0:
        return image

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return enhanced


def compute_quality_score(image: np.ndarray) -> float:
    """
    Computes an image quality score in range [0.0, 1.0].
    Measures sharpness (Laplacian variance), contrast, and resolution.
    """
    if image is None or image.size == 0:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # 1. Blur / Sharpness check
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_score = min(1.0, variance / 500.0)

    # 2. Contrast check
    min_val, max_val, _, _ = cv2.minMaxLoc(gray)
    contrast_score = (max_val - min_val) / 255.0

    # 3. Resolution factor
    h, w = image.shape[:2]
    res_score = min(1.0, max(h, w) / 1200.0)

    quality = (blur_score * 0.5) + (contrast_score * 0.3) + (res_score * 0.2)
    return round(float(np.clip(quality, 0.1, 0.99)), 3)


def preprocess_camera_photo(image_input: Any) -> Tuple[np.ndarray, float, Dict[str, Any]]:
    """
    Full end-to-end preprocessing pipeline for phone camera pictures:
    1. EXIF auto-rotate
    2. Paper boundary detection and 4-point perspective warp
    3. Fine-grain deskew
    4. Shadow & glare normalization (CLAHE)
    5. Quality score computation
    Returns (cleaned_bgr_image, quality_score, metadata).
    """
    raw_bgr = load_image(image_input)
    warped, was_warped = detect_document_corners_and_warp(raw_bgr)
    deskewed = deskew_image(warped)
    enhanced = enhance_for_camera(deskewed)
    quality = compute_quality_score(enhanced)

    meta = {
        "original_shape": raw_bgr.shape[:2],
        "processed_shape": enhanced.shape[:2],
        "was_perspective_warped": was_warped,
        "quality_score": quality,
    }
    return enhanced, quality, meta


def extract_field_crop(
    image: np.ndarray,
    box: Tuple[float, float, float, float],
    view: str = "base",
    padding: int = 8
) -> np.ndarray:
    """
    Extracts a region crop corresponding to normalized coordinates (x0, y0, x1, y1)
    and applies requested view transform:
    - 'base': standard crop
    - 'upscaled': 2x bicubic upscale
    - 'contrast': CLAHE high contrast enhancement
    - 'binary': Otsu thresholding
    """
    h, w = image.shape[:2]
    x0, y0, x1, y1 = box

    px0 = max(0, int(x0 * w) - padding)
    py0 = max(0, int(y0 * h) - padding)
    px1 = min(w, int(x1 * w) + padding)
    py1 = min(h, int(y1 * h) + padding)

    if px1 <= px0 or py1 <= py0:
        return np.ones((50, 150, 3), dtype=np.uint8) * 255

    crop = image[py0:py1, px0:px1].copy()

    if view == "upscaled":
        crop = cv2.resize(crop, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    elif view == "contrast":
        crop = enhance_for_camera(crop)
    elif view == "binary":
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        _, crop = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)

    return crop
