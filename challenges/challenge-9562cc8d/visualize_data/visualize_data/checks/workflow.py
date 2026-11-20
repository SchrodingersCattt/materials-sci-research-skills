"""Manifest-driven print, outputs, integrity, and review gates."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from ..manifest import resolve_path
from ..models import CheckResult, Finding


BAD_FINAL_SUFFIXES = ("_new", "_final", "_v2", "_test")
REVIEW_CATEGORIES = {
    "scientific_expression",
    "geometry",
    "annotations",
    "readability",
    "submission_quality",
}
PLACEHOLDER_REVIEW_VALUES = {"", "checked", "none", "n/a", "na", "ok", "pass", "passed"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_outputs(manifest: dict[str, Any]) -> CheckResult:
    started = time.perf_counter()
    findings: list[Finding] = []
    metrics: dict[str, Any] = {}
    canonical = manifest["figure"]["canonical_stem"]
    for record in manifest["outputs"]:
        value = record["path"] if isinstance(record, dict) else record
        path = resolve_path(manifest, value)
        if not path.exists():
            findings.append(Finding("required-output", "error", f"Missing output: {path}"))
            continue
        if path.stem != canonical:
            findings.append(Finding("canonical-stem", "error", f"Expected stem {canonical!r}, got {path.stem!r}"))
        if any(path.stem.endswith(suffix) for suffix in BAD_FINAL_SUFFIXES):
            findings.append(Finding("bad-final-suffix", "error", f"Forbidden final suffix: {path.name}"))
        metrics[str(path)] = {"bytes": path.stat().st_size, "sha256": file_hash(path)}
    return CheckResult("outputs", findings, metrics, time.perf_counter() - started)


def check_print(image_shape: tuple[int, int], target: dict[str, Any]) -> CheckResult:
    started = time.perf_counter()
    height, width = image_shape
    width_mm = float(target["width_mm"])
    effective_dpi = width / (width_mm / 25.4)
    minimum = float(target.get("min_dpi", 200))
    maximum = float(target.get("max_dpi", 600))
    findings: list[Finding] = []
    if effective_dpi < minimum:
        findings.append(Finding("effective-dpi", "error", f"DPI {effective_dpi:.1f} is below {minimum:.1f}"))
    if effective_dpi > maximum:
        findings.append(Finding("effective-dpi", "warning", f"DPI {effective_dpi:.1f} exceeds {maximum:.1f}"))
    return CheckResult(
        "print", findings,
        {"width_px": width, "height_px": height, "width_mm": width_mm, "effective_dpi": effective_dpi},
        time.perf_counter() - started,
    )


def check_integrity(manifest: dict[str, Any]) -> CheckResult:
    started = time.perf_counter()
    integrity = manifest.get("integrity", {})
    findings: list[Finding] = []
    required = integrity.get("required_content", [])
    evidence = integrity.get("evidence", {})
    for item in required:
        if item not in evidence:
            findings.append(Finding("required-content-evidence", "error", f"Missing evidence for required content: {item}"))
    for change in integrity.get("scientific_changes", []):
        if not change.get("approved", False):
            findings.append(Finding("unapproved-scientific-change", "error", f"Unapproved change: {change.get('description', '<missing>')}"))
    return CheckResult("integrity", findings, {"required_content": required}, time.perf_counter() - started)


def check_review(manifest: dict[str, Any], output_hash: str) -> CheckResult:
    started = time.perf_counter()
    findings: list[Finding] = []
    review = manifest.get("review")
    if not review:
        findings.append(Finding("review-present", "error", "Strict QA requires a review record"))
        return CheckResult("review", findings, duration_seconds=time.perf_counter() - started)
    categories = set(review.get("problems", {}).keys())
    if categories != REVIEW_CATEGORIES:
        findings.append(Finding(
            "review-five-categories", "error",
            f"Review categories must be {sorted(REVIEW_CATEGORIES)}, got {sorted(categories)}",
        ))
    if review.get("render_sha256") != output_hash:
        findings.append(Finding("review-render-hash", "error", "Review is stale for the current render"))
    problems = review.get("problems", {})
    for category in REVIEW_CATEGORIES:
        value = str(problems.get(category, "")).strip()
        if value.lower() in PLACEHOLDER_REVIEW_VALUES or len(value) < 20:
            findings.append(Finding(
                "review-substantive-category", "error",
                f"Review category {category!r} must contain a concrete finding and disposition, not {value!r}",
            ))
    action = str(review.get("action", "")).strip()
    if not action:
        findings.append(Finding("review-action", "error", "Review action is missing"))
    if len(action) < 20:
        findings.append(Finding("review-action", "error", "Review action must describe the actual correction or acceptance basis"))
    if not str(review.get("reviewer", "")).strip():
        findings.append(Finding("review-reviewer", "error", "Review must identify who inspected the rendered image"))
    inspection = review.get("inspection", {})
    if not isinstance(inspection, dict) or not inspection.get("image") or not inspection.get("physical_width_mm"):
        findings.append(Finding(
            "review-inspection", "error",
            "Review must record the inspected image and physical_width_mm",
        ))
    if review.get("visual_status") not in {"agent-inspected", "user-accepted"}:
        findings.append(Finding(
            "review-visual-status", "error",
            "visual_status must be 'agent-inspected' or 'user-accepted'; automated checks alone are insufficient",
        ))
    if review.get("stop_condition") not in {"fixed", "scientific-decision", "ambiguous-source", "user-accepted"}:
        findings.append(Finding("review-stop-condition", "error", "Review stop condition is missing or invalid"))
    return CheckResult("review", findings, duration_seconds=time.perf_counter() - started)


def check_strict_policy(manifest: dict[str, Any]) -> CheckResult:
    """Reject configurations that make strict QA vacuous or self-fulfilling."""
    started = time.perf_counter()
    findings: list[Finding] = []
    panels = manifest.get("panels", [])
    checks = manifest.get("checks", {})
    output_paths = [
        resolve_path(manifest, item["path"] if isinstance(item, dict) else item)
        for item in manifest.get("outputs", [])
    ]
    for output in output_paths:
        if "_qa" in output.parts:
            findings.append(Finding(
                "canonical-output-location", "error",
                f"Canonical output must be the deliverable, not a QA copy under _qa: {output}",
            ))
    for panel in panels:
        panel_id = panel.get("id")
        if int(panel.get("source_min_clearance_px", 0)) < 8:
            findings.append(Finding(
                "source-clearance-policy", "error",
                "source_min_clearance_px must be at least 8 in strict QA", panel=panel_id,
            ))
        if int(panel.get("min_clearance_px", 0)) < 8:
            findings.append(Finding(
                "composite-clearance-policy", "error",
                "min_clearance_px must be at least 8 in strict QA", panel=panel_id,
            ))
        for key in ("allow_touch_edges", "source_allow_touch_edges"):
            if panel.get(key):
                findings.append(Finding(
                    "edge-exception-policy", "error",
                    f"{key} is non-empty; strict QA requires an approved deviation instead of a silent edge exception",
                    panel=panel_id,
                ))
        if panel.get("source_stage") != "raw-render":
            findings.append(Finding(
                "source-provenance", "error",
                "Each panel must declare source_stage='raw-render'; padded/cropped QA derivatives are not source evidence",
                panel=panel_id,
            ))
    boundaries = checks.get("boundaries", {})
    if len(panels) > 1 and not boundaries.get("bands"):
        findings.append(Finding(
            "boundary-policy", "error",
            "Multi-panel strict QA requires at least one declared row/column safety band",
        ))
    for section in ("annotations", "geometry"):
        config = checks.get(section)
        if not isinstance(config, dict) or config.get("applicable") not in {True, False}:
            findings.append(Finding(
                f"{section}-policy", "error",
                f"checks.{section}.applicable must be explicitly true or false",
            ))
        elif config.get("applicable") is False and not str(config.get("reason", "")).strip():
            findings.append(Finding(
                f"{section}-policy", "error",
                f"checks.{section}.reason is required when the check is inapplicable",
            ))
        elif config.get("applicable") is True and not str(config.get("spec" if section == "annotations" else "metadata", "")).strip():
            required = "spec" if section == "annotations" else "metadata"
            findings.append(Finding(
                f"{section}-policy", "error",
                f"checks.{section}.{required} is required when applicable is true",
            ))
    return CheckResult("strict-policy", findings, duration_seconds=time.perf_counter() - started)
