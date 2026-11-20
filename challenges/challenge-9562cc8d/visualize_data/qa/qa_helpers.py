"""Reference figure-QA helpers for the visualize-data skill.

These helpers are intentionally renderer-agnostic. They operate on exported
image buffers and simple pixel-space records, so they can validate figures
made with vector plotting libraries, raster renderers, image compositors, or
mixed pipelines.

The rules encoded here mirror ``FIGURE_QA.md``:
* decorations and panel gaps must occupy real background whitespace;
* labels must not overlap data, sibling labels, leaders, or non-target data;
* text owned by a card, node, legend, or callout must remain inside its
  renderer-measured container bbox with declared inner padding;
* label placement should prefer adjacent readable slots, not far-away empty
  corners;
* failures should be reported as structured errors and fixed in the plotting
  algorithm rather than hidden by relaxed thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Error reporting
# ---------------------------------------------------------------------------


@dataclass
class QAError:
    """A single programmatic QA violation."""

    rule: str
    panel: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.panel}] {self.rule}: {self.detail}"


@dataclass
class LabelRecord:
    """One label or annotation slated for pixel-space QA validation."""

    label: str
    target_xy_px: tuple[float, float]
    text_xy_px: tuple[float, float]
    fontsize_pt: float

    def bbox(self, dpi: float = 220.0) -> tuple[float, float, float, float]:
        return estimate_text_bbox_px(
            self.label,
            self.fontsize_pt,
            self.text_xy_px,
            dpi=dpi,
        )


@dataclass
class ContainedTextRecord:
    """One renderer-measured text bbox and the box that visually owns it."""

    label: str
    text_bbox_px: tuple[float, float, float, float]
    container_bbox_px: tuple[float, float, float, float]
    min_padding_px: float = 2.0


# ---------------------------------------------------------------------------
# Image / mask helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_str: str) -> np.ndarray:
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {hex_str!r}")
    return np.array([int(hex_str[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.int32)


def build_data_mask(
    image: np.ndarray,
    target_color_hexes: Sequence[str] | None = None,
    *,
    color_tol: float = 70.0,
    dilate_px: int = 1,
    background_threshold: int = 235,
) -> np.ndarray:
    """Return a boolean mask for data ink in an RGB/RGBA image.

    If ``target_color_hexes`` is provided, pixels close to any target color are
    treated as data. This is useful for label QA on selected object classes such
    as atoms, markers, or highlighted traces. If it is omitted, every opaque
    non-near-white pixel is treated as data, which is the right default for
    checking whether a decoration or label sits on top of the rendered figure.

    A small binary dilation closes anti-aliased one-pixel gaps around rendered
    objects so near-misses are still caught.
    """
    if image.ndim != 3 or image.shape[-1] not in (3, 4):
        raise ValueError("image must be HxWx3 or HxWx4")

    rgb = image[..., :3].astype(np.int32)
    if image.shape[-1] == 4:
        alpha = image[..., 3]
    else:
        alpha = np.full(image.shape[:2], 255, dtype=np.uint8)

    if target_color_hexes:
        masks = []
        for hex_str in target_color_hexes:
            target = _hex_to_rgb(hex_str)
            diff = np.linalg.norm(rgb - target, axis=2)
            masks.append(diff < float(color_tol))
        mask = np.logical_or.reduce(masks)
    else:
        near_background = (rgb >= int(background_threshold)).all(axis=2)
        mask = (alpha > 200) & (~near_background)

    if dilate_px > 0:
        try:
            from scipy import ndimage as ndi

            mask = ndi.binary_dilation(mask, iterations=int(dilate_px))
        except Exception:
            # Keep the helper usable in lightweight environments; callers that
            # require exact dilation should add scipy as an explicit dependency.
            pass
    return mask.astype(bool)


def whitespace_distance_map(data_mask: np.ndarray) -> np.ndarray:
    """Pixel-wise Euclidean distance to the nearest data pixel."""
    try:
        from scipy import ndimage as ndi
    except Exception as exc:  # pragma: no cover - scipy is expected for placement
        raise RuntimeError("scipy.ndimage is required for whitespace QA") from exc
    return ndi.distance_transform_edt(~data_mask).astype(np.float32)


# ---------------------------------------------------------------------------
# Bounding-box utilities
# ---------------------------------------------------------------------------


def estimate_text_bbox_px(
    text: str,
    fontsize_pt: float,
    center_xy: tuple[float, float],
    *,
    dpi: float = 220.0,
    char_width_factor: float = 0.55,
    pad_factor: float = 0.06,
) -> tuple[float, float, float, float]:
    """Cheap matplotlib-free estimate of a horizontal text bbox in pixels."""
    h_pt = float(fontsize_pt)
    w_pt = h_pt * char_width_factor * max(len(text), 1)
    h_px = h_pt * dpi / 72.0
    w_px = w_pt * dpi / 72.0
    h_px *= 1.0 + pad_factor
    w_px *= 1.0 + pad_factor
    cx, cy = center_xy
    return (cx - w_px / 2.0, cy - h_px / 2.0, cx + w_px / 2.0, cy + h_px / 2.0)


def bbox_intersects_mask(bbox: tuple[float, float, float, float], mask: np.ndarray) -> int:
    """Return number of mask pixels overlapped by ``bbox``; zero means clean."""
    height, width = mask.shape
    x0 = int(max(0, np.floor(bbox[0])))
    y0 = int(max(0, np.floor(bbox[1])))
    x1 = int(min(width, np.ceil(bbox[2])))
    y1 = int(min(height, np.ceil(bbox[3])))
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(mask[y0:y1, x0:x1].sum())


def bboxes_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def bbox_edge_distance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return float(np.hypot(dx, dy))


def bbox_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return (0.5 * (bbox[0] + bbox[2]), 0.5 * (bbox[1] + bbox[3]))


def validate_text_containment(
    *,
    panel: str,
    records: Sequence[ContainedTextRecord],
    tolerance_px: float = 0.25,
) -> list[QAError]:
    """Require every final-render text bbox to stay inside its owning box.

    Both bboxes must come from the final renderer after layout is complete and
    use the same pixel coordinate system.
    """
    errors: list[QAError] = []
    for rec in records:
        text_box = tuple(float(v) for v in rec.text_bbox_px)
        container_box = tuple(float(v) for v in rec.container_bbox_px)
        padding = float(rec.min_padding_px)
        if len(text_box) != 4 or len(container_box) != 4:
            errors.append(QAError(
                rule="invalid-containment-bbox",
                panel=panel,
                detail=f"{rec.label}: bboxes must contain four coordinates",
            ))
            continue
        if not np.isfinite(text_box + container_box).all() or padding < 0:
            errors.append(QAError(
                rule="invalid-containment-bbox",
                panel=panel,
                detail=f"{rec.label}: bboxes must be finite and padding non-negative",
            ))
            continue

        tx0, ty0, tx1, ty1 = text_box
        cx0, cy0, cx1, cy1 = container_box
        if tx1 <= tx0 or ty1 <= ty0 or cx1 <= cx0 or cy1 <= cy0:
            errors.append(QAError(
                rule="invalid-containment-bbox",
                panel=panel,
                detail=f"{rec.label}: bbox coordinates are not ordered",
            ))
            continue

        inner = (cx0 + padding, cy0 + padding, cx1 - padding, cy1 - padding)
        if inner[2] <= inner[0] or inner[3] <= inner[1]:
            errors.append(QAError(
                rule="invalid-containment-bbox",
                panel=panel,
                detail=f"{rec.label}: {padding:.1f}px padding collapses the container",
            ))
            continue

        overflow = {
            "min-x": max(0.0, inner[0] - tx0),
            "min-y": max(0.0, inner[1] - ty0),
            "max-x": max(0.0, tx1 - inner[2]),
            "max-y": max(0.0, ty1 - inner[3]),
        }
        failed = {edge: value for edge, value in overflow.items() if value > tolerance_px}
        if failed:
            detail = ", ".join(f"{edge} {value:.1f}px" for edge, value in failed.items())
            errors.append(QAError(
                rule="text-outside-container",
                panel=panel,
                detail=(
                    f"{rec.label}: exceeds the {padding:.1f}px padded container on {detail}; "
                    f"text={text_box}, container={container_box}"
                ),
            ))
    return errors


# ---------------------------------------------------------------------------
# Segment and geometry checks
# ---------------------------------------------------------------------------


def arrow_is_uturn(
    target_xy: tuple[float, float],
    label_center: tuple[float, float],
    cluster_center: tuple[float, float],
    *,
    min_cosine: float = -0.3,
) -> bool:
    """Return True if a leader pulls the target back across the cluster.

    The rule is deliberately relaxed. Tangential or slightly inward placements
    are allowed; only clear u-turns are rejected.
    """
    a = np.asarray(target_xy, dtype=float) - np.asarray(cluster_center, dtype=float)
    b = np.asarray(label_center, dtype=float) - np.asarray(target_xy, dtype=float)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-6 or nb < 1e-6:
        return False
    cos_ab = float(np.dot(a, b) / (na * nb))
    return cos_ab < float(min_cosine)


def segments_intersect(p1, p2, p3, p4) -> bool:
    """Strict intersection between two open line segments."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    p3 = np.asarray(p3, dtype=float)
    p4 = np.asarray(p4, dtype=float)
    d1 = p2 - p1
    d2 = p4 - p3
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denom) < 1e-9:
        return False
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / denom
    s = ((p3[0] - p1[0]) * d1[1] - (p3[1] - p1[1]) * d1[0]) / denom
    eps = 1e-3
    return (eps < t < 1.0 - eps) and (eps < s < 1.0 - eps)


def segment_enters_bbox(
    p1: tuple[float, float],
    p2: tuple[float, float],
    bbox: tuple[float, float, float, float],
    *,
    margin: float = 0.0,
) -> bool:
    """Return True if open segment ``p1``-``p2`` crosses a bbox edge."""
    x0, y0, x1, y1 = bbox
    if margin > 0.0:
        x0 += margin
        y0 += margin
        x1 -= margin
        y1 -= margin
    if x1 <= x0 or y1 <= y0:
        return False
    if max(p1[0], p2[0]) < x0 or min(p1[0], p2[0]) > x1:
        return False
    if max(p1[1], p2[1]) < y0 or min(p1[1], p2[1]) > y1:
        return False
    edges = (
        ((x0, y0), (x1, y0)),
        ((x1, y0), (x1, y1)),
        ((x1, y1), (x0, y1)),
        ((x0, y1), (x0, y0)),
    )
    return any(segments_intersect(p1, p2, a, b) for a, b in edges)


def segment_through_mask(
    target_xy: tuple[float, float],
    label_xy: tuple[float, float],
    mask: np.ndarray,
    *,
    target_radius_px: float = 14.0,
    label_radius_px: float = 10.0,
    sample_step_px: float = 1.5,
) -> int:
    """Count mask pixels crossed by the open leader segment.

    The target endpoint and the label endpoint are skipped. Any remaining hit is
    a non-target object that would make the leader ambiguous.
    """
    p0 = np.asarray(target_xy, dtype=float)
    p1 = np.asarray(label_xy, dtype=float)
    length = float(np.linalg.norm(p1 - p0))
    if length < 1e-6:
        return 0
    n = max(2, int(np.ceil(length / sample_step_px)))
    ts = np.linspace(0.0, 1.0, n + 1)
    pts = p0[None, :] * (1 - ts[:, None]) + p1[None, :] * ts[:, None]
    height, width = mask.shape
    hits = 0
    for x, y in pts:
        if np.hypot(x - p0[0], y - p0[1]) < target_radius_px:
            continue
        if np.hypot(x - p1[0], y - p1[1]) < label_radius_px:
            continue
        ix = int(round(float(x)))
        iy = int(round(float(y)))
        if 0 <= ix < width and 0 <= iy < height and mask[iy, ix]:
            hits += 1
    return hits


# ---------------------------------------------------------------------------
# Top-level validators
# ---------------------------------------------------------------------------


def validate_panel_boundary(
    *,
    panel: str,
    figure_image: np.ndarray,
    rect_px: tuple[float, float, float, float],
    background_threshold: int = 235,
    max_data_pixels: int = 0,
) -> list[QAError]:
    """Verify a no-data zone, such as a row gap or reserved legend strip.

    The rectangle is in figure-image pixel coordinates. Anything below the
    background threshold counts as ink and therefore as content invading the
    safety band.
    """
    if figure_image.ndim != 3 or figure_image.shape[-1] not in (3, 4):
        raise ValueError("figure_image must be HxWx3 or HxWx4")
    height, width = figure_image.shape[:2]
    x0_f, y0_f, x1_f, y1_f = rect_px
    x0 = int(max(0, np.floor(x0_f)))
    y0 = int(max(0, np.floor(y0_f)))
    x1 = int(min(width, np.ceil(x1_f)))
    y1 = int(min(height, np.ceil(y1_f)))
    if x1 <= x0 or y1 <= y0:
        return []
    region = figure_image[y0:y1, x0:x1, :3].astype(np.int32)
    is_data = ~(region >= int(background_threshold)).all(axis=2)
    n_invading = int(is_data.sum())
    if n_invading > int(max_data_pixels):
        return [QAError(
            rule="panel-boundary-clearance",
            panel=panel,
            detail=(
                f"safety band ({x0},{y0})-({x1},{y1}) has "
                f"{n_invading} non-background pixels "
                f"(allowed {int(max_data_pixels)})"
            ),
        )]
    return []


def validate_leader_clearance(
    *,
    panel: str,
    image: np.ndarray,
    target_xy_px: tuple[float, float],
    label_xy_px: tuple[float, float],
    target_color_hexes: Sequence[str] | None = None,
    background_threshold: int = 235,
    color_tol: float = 70.0,
    dilate_px: int = 1,
    target_radius_px: float = 14.0,
    label_radius_px: float = 18.0,
) -> list[QAError]:
    """Fail when an annotation leader traverses non-target data ink.

    Use this for any callout whose leader must connect an object to nearby
    whitespace. The target and label endpoint neighborhoods are excluded; every
    other data-mask hit is blocking. This makes the common anti-pattern of
    routing a long leader diagonally across a scatter cloud programmatically
    detectable.
    """
    data_mask = build_data_mask(
        image,
        target_color_hexes=target_color_hexes,
        color_tol=color_tol,
        dilate_px=dilate_px,
        background_threshold=background_threshold,
    )
    hits = segment_through_mask(
        target_xy_px,
        label_xy_px,
        data_mask,
        target_radius_px=target_radius_px,
        label_radius_px=label_radius_px,
    )
    if hits:
        return [QAError(
            rule="leader-through-data",
            panel=panel,
            detail=f"leader crosses {hits} non-target data-mask samples",
        )]
    return []


def validate_label_panel(
    *,
    panel: str,
    image: np.ndarray,
    records: Sequence[LabelRecord],
    cluster_center_px: tuple[float, float],
    target_color_hexes: Sequence[str] | None = None,
    min_data_clearance_px: float = 8.0,
    min_label_edge_distance_factor: float = 1.0,
    dpi: float = 220.0,
    color_tol: float = 70.0,
    dilate_px: int = 1,
    check_uturn: bool = True,
    max_arrow_factor: float | None = 4.0,
    target_radius_px: float = 14.0,
) -> list[QAError]:
    """Run the label/leader checklist for one panel.

    Enforced rules:
    * label bbox must not intersect data ink;
    * sibling labels must not overlap and must keep a minimum edge distance;
    * label center must have minimum clearance to the data mask;
    * leaders must not u-turn, cross other leaders, enter sibling labels, or
      pass through non-target data;
    * leaders must not become so long that the label is visually detached.
    """
    errors: list[QAError] = []
    data_mask = build_data_mask(
        image,
        target_color_hexes=target_color_hexes,
        color_tol=color_tol,
        dilate_px=dilate_px,
    )
    distmap = whitespace_distance_map(data_mask)
    height, width = data_mask.shape
    bboxes = [rec.bbox(dpi=dpi) for rec in records]

    for rec, bb in zip(records, bboxes):
        hits = bbox_intersects_mask(bb, data_mask)
        if hits > 0:
            errors.append(QAError(
                rule="label-bbox-on-data",
                panel=panel,
                detail=(
                    f"{rec.label}: bbox covers {hits} data pixels at "
                    f"({rec.text_xy_px[0]:.0f},{rec.text_xy_px[1]:.0f})"
                ),
            ))

    for rec, bb in zip(records, bboxes):
        cx, cy = bbox_center(bb)
        ix = int(np.clip(round(cx), 0, width - 1))
        iy = int(np.clip(round(cy), 0, height - 1))
        d = float(distmap[iy, ix])
        if d < min_data_clearance_px:
            errors.append(QAError(
                rule="label-too-close-to-data",
                panel=panel,
                detail=(
                    f"{rec.label}: bbox center {d:.1f}px from nearest data "
                    f"(min {min_data_clearance_px:.1f})"
                ),
            ))

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            ri, rj = records[i], records[j]
            bi, bj = bboxes[i], bboxes[j]
            if bboxes_overlap(bi, bj):
                errors.append(QAError(
                    rule="label-bbox-overlap",
                    panel=panel,
                    detail=f"{ri.label} and {rj.label} bboxes overlap",
                ))
                continue
            edge_d = bbox_edge_distance(bi, bj)
            text_h_px = ri.fontsize_pt * dpi / 72.0
            min_edge = min_label_edge_distance_factor * text_h_px
            if edge_d < min_edge:
                errors.append(QAError(
                    rule="label-bbox-too-close",
                    panel=panel,
                    detail=(
                        f"{ri.label} and {rj.label} edge-to-edge {edge_d:.1f}px "
                        f"< min {min_edge:.1f}"
                    ),
                ))

    if check_uturn:
        for rec, bb in zip(records, bboxes):
            if arrow_is_uturn(rec.target_xy_px, bbox_center(bb), cluster_center_px):
                errors.append(QAError(
                    rule="leader-u-turn",
                    panel=panel,
                    detail=f"{rec.label}: label sits on the inward side of the cluster",
                ))

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            ri, rj = records[i], records[j]
            if ri.target_xy_px == rj.target_xy_px:
                continue
            ci = bbox_center(bboxes[i])
            cj = bbox_center(bboxes[j])
            if segments_intersect(ri.target_xy_px, ci, rj.target_xy_px, cj):
                errors.append(QAError(
                    rule="leader-crossing",
                    panel=panel,
                    detail=f"{ri.label} leader crosses {rj.label} leader",
                ))

    for i, ri in enumerate(records):
        leader = (ri.target_xy_px, bbox_center(bboxes[i]))
        for j, rj in enumerate(records):
            if i == j:
                continue
            if segment_enters_bbox(leader[0], leader[1], bboxes[j], margin=1.0):
                errors.append(QAError(
                    rule="leader-crosses-label",
                    panel=panel,
                    detail=f"{ri.label} leader passes through {rj.label}'s bbox",
                ))

    for rec, bb in zip(records, bboxes):
        bw = float(bb[2] - bb[0])
        bh = float(bb[3] - bb[1])
        label_skip_px = 0.5 * float(np.hypot(bw, bh)) + 2.0
        hits = segment_through_mask(
            rec.target_xy_px,
            bbox_center(bb),
            data_mask,
            target_radius_px=target_radius_px,
            label_radius_px=label_skip_px,
        )
        if hits > 0:
            errors.append(QAError(
                rule="leader-through-data",
                panel=panel,
                detail=f"{rec.label}: leader passes through {hits} non-target data px",
            ))

    if max_arrow_factor is not None:
        for rec, bb in zip(records, bboxes):
            text_h_px = rec.fontsize_pt * dpi / 72.0
            cx, cy = bbox_center(bb)
            leader_len = float(np.hypot(cx - rec.target_xy_px[0], cy - rec.target_xy_px[1]))
            max_leader = float(max_arrow_factor) * text_h_px
            if leader_len > max_leader:
                errors.append(QAError(
                    rule="leader-too-long",
                    panel=panel,
                    detail=(
                        f"{rec.label}: leader {leader_len:.0f}px > max {max_leader:.0f}px "
                        f"(={max_arrow_factor:.1f} x text height)"
                    ),
                ))

    return errors


# ---------------------------------------------------------------------------
# Whitespace-aware label placement
# ---------------------------------------------------------------------------


def whitespace_label_placement(
    *,
    image: np.ndarray,
    items: Sequence[tuple[str, tuple[float, float]]],
    cluster_center_px: tuple[float, float],
    fontsize_pt: float,
    forbidden_rects_px: Sequence[tuple[float, float, float, float]] = (),
    target_color_hexes: Sequence[str] | None = None,
    min_data_clearance_px: float = 6.0,
    min_label_edge_distance_factor: float = 0.4,
    dpi: float = 220.0,
    radius_search_factors: Sequence[float] = (0.10, 0.14, 0.18, 0.23, 0.28, 0.34, 0.42, 0.52),
    angle_step_deg: float = 9.0,
    color_tol: float = 70.0,
    max_arrow_factor: float = 4.0,
    target_radius_px: float = 14.0,
) -> list[LabelRecord]:
    """Greedy placement that keeps labels adjacent and collision-free.

    Candidates are filtered by the same hard rules as ``validate_label_panel``.
    Among surviving candidates, the shortest leader wins; whitespace clearance
    is a hard floor and a small tie-breaker, not the primary objective.
    """
    height, width = image.shape[:2]
    data_mask = build_data_mask(
        image,
        target_color_hexes=target_color_hexes,
        color_tol=color_tol,
        dilate_px=1,
    )
    distmap = whitespace_distance_map(data_mask)
    cx_c, cy_c = cluster_center_px
    text_h_px = fontsize_pt * dpi / 72.0
    min_edge = min_label_edge_distance_factor * text_h_px
    max_leader_px = float(max_arrow_factor) * text_h_px
    base_radius = max(60.0, 0.30 * min(width, height))

    placed: list[LabelRecord] = []
    placed_bboxes: list[tuple[float, float, float, float]] = []
    placed_leaders: list[tuple[tuple[float, float], tuple[float, float]]] = []

    order = sorted(
        range(len(items)),
        key=lambda i: -float(np.hypot(items[i][1][0] - cx_c, items[i][1][1] - cy_c)),
    )

    for i in order:
        label, target_xy = items[i]
        tx0, ty0 = float(target_xy[0]), float(target_xy[1])
        radial = np.array([tx0 - cx_c, ty0 - cy_c], dtype=float)
        norm = float(np.linalg.norm(radial))
        if norm < 1e-3:
            radial = np.array([0.0, -1.0])
            norm = 1.0
        radial /= norm

        candidates: list[tuple[float, tuple[float, float]]] = []
        reject_counts = {
            "data_mask": 0,
            "forbidden": 0,
            "sibling_bbox_overlap": 0,
            "sibling_bbox_too_close": 0,
            "uturn": 0,
            "leader_crossing": 0,
            "leader_into_sibling_bbox": 0,
            "leader_through_data": 0,
            "leader_too_long": 0,
            "low_clearance": 0,
        }

        for r_mul in radius_search_factors:
            r = base_radius * float(r_mul)
            for step in range(0, int(360.0 / angle_step_deg) + 1):
                sign = 1 if step % 2 == 0 else -1
                ang = np.deg2rad(angle_step_deg * (step // 2) * sign)
                cos_a, sin_a = np.cos(ang), np.sin(ang)
                rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
                direction = rot @ radial
                x = float(np.clip(tx0 + direction[0] * r, 12.0, width - 12.0))
                y = float(np.clip(ty0 + direction[1] * r, 12.0, height - 12.0))
                bb = estimate_text_bbox_px(label, fontsize_pt, (x, y), dpi=dpi)

                if bbox_intersects_mask(bb, data_mask) > 0:
                    reject_counts["data_mask"] += 1
                    continue
                if any(bboxes_overlap(bb, rect) for rect in forbidden_rects_px):
                    reject_counts["forbidden"] += 1
                    continue
                if any(bboxes_overlap(bb, prev) for prev in placed_bboxes):
                    reject_counts["sibling_bbox_overlap"] += 1
                    continue
                if any(bbox_edge_distance(bb, prev) < min_edge for prev in placed_bboxes):
                    reject_counts["sibling_bbox_too_close"] += 1
                    continue
                center = bbox_center(bb)
                if arrow_is_uturn((tx0, ty0), center, (cx_c, cy_c)):
                    reject_counts["uturn"] += 1
                    continue
                if any(segments_intersect((tx0, ty0), center, a, b) for a, b in placed_leaders):
                    reject_counts["leader_crossing"] += 1
                    continue
                if any(segment_enters_bbox((tx0, ty0), center, prev, margin=1.0) for prev in placed_bboxes):
                    reject_counts["leader_into_sibling_bbox"] += 1
                    continue

                bw = float(bb[2] - bb[0])
                bh = float(bb[3] - bb[1])
                label_skip_px = 0.5 * float(np.hypot(bw, bh)) + 2.0
                if segment_through_mask(
                    (tx0, ty0),
                    center,
                    data_mask,
                    target_radius_px=target_radius_px,
                    label_radius_px=label_skip_px,
                ) > 0:
                    reject_counts["leader_through_data"] += 1
                    continue

                leader_len = float(np.hypot(x - tx0, y - ty0))
                if leader_len > max_leader_px:
                    reject_counts["leader_too_long"] += 1
                    continue

                cx, cy = center
                ix = int(np.clip(round(cx), 0, width - 1))
                iy = int(np.clip(round(cy), 0, height - 1))
                clearance = float(distmap[iy, ix])
                if clearance < min_data_clearance_px:
                    reject_counts["low_clearance"] += 1
                    continue

                score = -leader_len + 0.02 * (clearance - min_data_clearance_px)
                candidates.append((score, (x, y)))

        if not candidates:
            top_rejects = sorted(reject_counts.items(), key=lambda kv: -kv[1])
            top_str = ", ".join(f"{k}={v}" for k, v in top_rejects if v)
            raise RuntimeError(
                f"whitespace_label_placement: no valid slot for label {label!r} "
                f"at target ({tx0:.0f},{ty0:.0f}); enlarge the tile, drop "
                f"nonessential labels, or change the design instead of silently "
                f"violating QA. Rejection breakdown: {top_str}"
            )

        candidates.sort(key=lambda item: -item[0])
        _, (x, y) = candidates[0]
        rec = LabelRecord(label=label, target_xy_px=(tx0, ty0), text_xy_px=(x, y), fontsize_pt=fontsize_pt)
        placed.append(rec)
        bb = rec.bbox(dpi=dpi)
        placed_bboxes.append(bb)
        placed_leaders.append(((tx0, ty0), bbox_center(bb)))

    by_label = {rec.label: rec for rec in placed}
    return [by_label[label] for label, _ in items]
