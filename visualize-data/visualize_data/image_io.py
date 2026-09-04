"""Static figure loading and rasterization."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def load_rgb(path: Path, *, dpi: int = 300) -> tuple[np.ndarray, dict[str, object]]:
    path = path.resolve()
    suffix = path.suffix.lower()
    if suffix in RASTER_SUFFIXES:
        image = Image.open(path).convert("RGB")
        return np.asarray(image), {"backend": "Pillow", "source": str(path)}
    if suffix == ".pdf":
        return _rasterize_pdf(path, dpi=dpi)
    if suffix == ".svg":
        return _rasterize_svg(path, dpi=dpi)
    raise ValueError(f"Unsupported static figure format: {suffix}")


def _rasterize_pdf(path: Path, *, dpi: int) -> tuple[np.ndarray, dict[str, object]]:
    executable = shutil.which("pdftoppm")
    if not executable:
        raise RuntimeError("PDF QA requires pdftoppm")
    with tempfile.TemporaryDirectory(prefix="visualize-data-pdf-") as temporary:
        stem = Path(temporary) / "page"
        subprocess.run(
            [executable, "-f", "1", "-singlefile", "-png", "-r", str(dpi), str(path), str(stem)],
            check=True,
            capture_output=True,
            text=True,
        )
        output = stem.with_suffix(".png")
        return np.asarray(Image.open(output).convert("RGB")), {
            "backend": "pdftoppm",
            "dpi": dpi,
            "source": str(path),
        }


def _rasterize_svg(path: Path, *, dpi: int) -> tuple[np.ndarray, dict[str, object]]:
    executable = shutil.which("rsvg-convert")
    if not executable:
        raise RuntimeError("SVG QA requires rsvg-convert")
    with tempfile.TemporaryDirectory(prefix="visualize-data-svg-") as temporary:
        output = Path(temporary) / "image.png"
        subprocess.run(
            [executable, "--dpi-x", str(dpi), "--dpi-y", str(dpi), "-o", str(output), str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return np.asarray(Image.open(output).convert("RGB")), {
            "backend": "rsvg-convert",
            "dpi": dpi,
            "source": str(path),
        }


def save_mask(mask: np.ndarray, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(output)


def crop_background(
    image: np.ndarray,
    *,
    background_threshold: int = 245,
    padding_px: int = 0,
    min_source_clearance_px: int = 1,
) -> tuple[np.ndarray, dict[str, int]]:
    ink = np.any(image[..., :3] < background_threshold, axis=2)
    if not ink.any():
        raise ValueError("Cannot crop an empty image")
    ys, xs = np.where(ink)
    clearances = {
        "left": int(xs.min()),
        "right": int(image.shape[1] - 1 - xs.max()),
        "top": int(ys.min()),
        "bottom": int(image.shape[0] - 1 - ys.max()),
    }
    failures = {edge: value for edge, value in clearances.items() if value < min_source_clearance_px}
    if failures:
        raise ValueError(f"Source content may already be clipped: {failures}")
    x0 = max(0, int(xs.min()) - padding_px)
    x1 = min(image.shape[1], int(xs.max()) + padding_px + 1)
    y0 = max(0, int(ys.min()) - padding_px)
    y1 = min(image.shape[0], int(ys.max()) + padding_px + 1)
    return image[y0:y1, x0:x1], {"x0": x0, "y0": y0, "x1": x1, "y1": y1, **clearances}
