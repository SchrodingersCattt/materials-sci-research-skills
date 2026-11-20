"""Pixel-level masks, whitespace, boundaries, clipping, and color checks."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy import ndimage as ndi

from ..models import CheckResult, Finding


def build_ink_mask(
    image: np.ndarray,
    *,
    background_threshold: int = 245,
    dilate_px: int = 0,
) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError("image must be HxWx3 or HxWx4")
    rgb = image[..., :3]
    alpha = image[..., 3] if image.shape[2] == 4 else np.full(image.shape[:2], 255)
    mask = (alpha > 0) & np.any(rgb < background_threshold, axis=2)
    if dilate_px:
        mask = ndi.binary_dilation(mask, iterations=dilate_px)
    return mask.astype(bool)


def _pixel_rect(rect: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    if len(rect) != 4 or not all(0 <= value <= 1 for value in rect):
        raise ValueError(f"Normalized rectangle must contain four values in [0,1]: {rect}")
    x0, y0, x1, y1 = rect
    if not (x0 < x1 and y0 < y1):
        raise ValueError(f"Invalid normalized rectangle: {rect}")
    return int(x0 * width), int(y0 * height), int(np.ceil(x1 * width)), int(np.ceil(y1 * height))


def audit_whitespace(image: np.ndarray, config: dict[str, Any]) -> CheckResult:
    started = time.perf_counter()
    mask = build_ink_mask(image, background_threshold=int(config.get("background_threshold", 245)))
    height, width = mask.shape
    ys, xs = np.where(mask)
    findings: list[Finding] = []
    if not len(xs):
        findings.append(Finding("nonempty-figure", "error", "Figure contains no non-background pixels"))
        return CheckResult("whitespace", findings, duration_seconds=time.perf_counter() - started)

    rows = int(config.get("grid_rows", 12))
    columns = int(config.get("grid_columns", 20))
    occupancy = []
    for row in range(rows):
        values = []
        for column in range(columns):
            tile = mask[
                row * height // rows:(row + 1) * height // rows,
                column * width // columns:(column + 1) * width // columns,
            ]
            values.append(float(tile.mean()))
        occupancy.append(values)

    ink_fraction = float(mask.mean())
    minimum = float(config.get("min_ink_fraction", 0.02))
    if ink_fraction < minimum:
        findings.append(Finding(
            "global-ink-fraction", "error",
            f"Global ink fraction {ink_fraction:.4f} is below minimum {minimum:.4f}",
            metrics={"ink_fraction": ink_fraction, "minimum": minimum},
        ))

    panels = {}
    for panel in config.get("panels", []):
        x0, y0, x1, y1 = _pixel_rect(panel["rect"], width, height)
        region = mask[y0:y1, x0:x1]
        if not region.any():
            findings.append(Finding("panel-nonempty", "error", "Panel contains no ink", panel=panel["id"]))
            continue
        py, px = np.where(region)
        bbox_area = (px.max() - px.min() + 1) * (py.max() - py.min() + 1)
        fill = float(bbox_area / region.size)
        panel_minimum = float(panel.get("min_bbox_fill", config.get("min_panel_bbox_fill", 0.15)))
        if fill < panel_minimum:
            findings.append(Finding(
                "panel-bbox-fill", "error",
                f"Panel ink bounding box fills {fill:.3f}, below {panel_minimum:.3f}",
                panel=panel["id"], metrics={"bbox_fill": fill, "minimum": panel_minimum},
            ))
        panels[panel["id"]] = {"ink_fraction": float(region.mean()), "bbox_fill": fill}

    metrics = {
        "width": width,
        "height": height,
        "ink_fraction": ink_fraction,
        "ink_bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "occupancy_grid": occupancy,
        "panels": panels,
    }
    return CheckResult("whitespace", findings, metrics, time.perf_counter() - started)


def check_boundaries(image: np.ndarray, bands: list[dict[str, Any]], *, threshold: int = 245) -> CheckResult:
    started = time.perf_counter()
    mask = build_ink_mask(image, background_threshold=threshold)
    height, width = mask.shape
    findings: list[Finding] = []
    metrics: dict[str, Any] = {}
    for band in bands:
        x0, y0, x1, y1 = _pixel_rect(band["rect"], width, height)
        count = int(mask[y0:y1, x0:x1].sum())
        maximum = int(band.get("max_ink_pixels", 0))
        metrics[band["id"]] = {"ink_pixels": count, "maximum": maximum}
        if count > maximum:
            findings.append(Finding(
                "panel-boundary-clearance", "error",
                f"Safety band has {count} ink pixels; allowed {maximum}", panel=band["id"],
            ))
    return CheckResult("boundaries", findings, metrics, time.perf_counter() - started)


def check_clipping(image: np.ndarray, panels: list[dict[str, Any]], *, threshold: int = 245) -> CheckResult:
    started = time.perf_counter()
    mask = build_ink_mask(image, background_threshold=threshold)
    height, width = mask.shape
    findings: list[Finding] = []
    metrics: dict[str, Any] = {}
    for panel in panels:
        x0, y0, x1, y1 = _pixel_rect(panel["rect"], width, height)
        region = mask[y0:y1, x0:x1]
        if not region.any():
            findings.append(Finding("panel-nonempty", "error", "Panel contains no ink", panel=panel["id"]))
            continue
        ys, xs = np.where(region)
        clearances = {
            "left": int(xs.min()),
            "right": int(region.shape[1] - 1 - xs.max()),
            "top": int(ys.min()),
            "bottom": int(region.shape[0] - 1 - ys.max()),
        }
        minimum = int(panel.get("min_clearance_px", 8))
        allowed = set(panel.get("allow_touch_edges", []))
        metrics[panel["id"]] = {"clearances_px": clearances, "minimum_px": minimum}
        for edge, clearance in clearances.items():
            if edge not in allowed and clearance < minimum:
                findings.append(Finding(
                    "edge-clearance", "error",
                    f"{edge} clearance {clearance}px is below {minimum}px",
                    panel=panel["id"], metrics={"edge": edge, "clearance": clearance, "minimum": minimum},
                ))
    return CheckResult("clipping", findings, metrics, time.perf_counter() - started)


def check_colors(image: np.ndarray, semantics: list[dict[str, Any]]) -> CheckResult:
    started = time.perf_counter()
    rgb = image[..., :3].astype(float)
    findings: list[Finding] = []
    metrics: dict[str, Any] = {}
    for item in semantics:
        color = item["color"].lstrip("#")
        target = np.array([int(color[index:index + 2], 16) for index in (0, 2, 4)])
        tolerance = float(item.get("tolerance", 45.0))
        count = int((np.linalg.norm(rgb - target, axis=2) <= tolerance).sum())
        minimum = int(item.get("min_pixels", 1))
        metrics[item["id"]] = {"pixels": count, "minimum": minimum, "color": item["color"]}
        if count < minimum:
            findings.append(Finding(
                "semantic-color-presence", "error",
                f"Semantic color {item['color']} has {count} matching pixels; required {minimum}",
                panel=item.get("panel"),
            ))
    return CheckResult("colors", findings, metrics, time.perf_counter() - started)
