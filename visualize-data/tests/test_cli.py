from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "visualize_data.py"


def run_cli(*args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_image(path: Path, *, clipped: bool = False) -> None:
    image = np.full((300, 500, 3), 255, dtype=np.uint8)
    image[80:220, 80:220] = (213, 94, 0)
    image[100:200, 280:420] = (0, 114, 178)
    if clipped:
        image[0:30, 250:300] = (0, 114, 178)
    Image.fromarray(image).save(path)


def make_manifest(directory: Path, *, clipped_source: bool = False) -> Path:
    final = directory / "figure.png"
    source_a = directory / "_panel_a.png"
    source_b = directory / "_panel_b.png"
    make_image(final)
    make_image(source_a, clipped=clipped_source)
    make_image(source_b)
    manifest = {
        "version": 1,
        "figure": {"canonical_stem": "figure"},
        "outputs": [{"path": "figure.png"}],
        "target": {"width_mm": 180, "qa_dpi": 300, "min_dpi": 70, "max_dpi": 1000},
        "panels": [
            {"id": "a", "source": "_panel_a.png", "source_stage": "raw-render", "slot": [0, 0, 0.48, 1], "source_min_clearance_px": 8, "min_clearance_px": 8},
            {"id": "b", "source": "_panel_b.png", "source_stage": "raw-render", "slot": [0.52, 0, 1, 1], "source_min_clearance_px": 8, "min_clearance_px": 8},
        ],
        "checks": {
            "whitespace": {"min_ink_fraction": 0.01, "min_panel_bbox_fill": 0.05},
            "boundaries": {"bands": [{"id": "column-gap", "rect": [0.48, 0, 0.52, 1], "max_ink_pixels": 0}]},
            "text_containment": {"applicable": False, "reason": "Synthetic test has no boxed text"},
            "annotations": {"applicable": False, "reason": "Synthetic test has no annotations"},
            "geometry": {"applicable": False, "reason": "Synthetic test has no geometry-bearing annotations"},
            "colors": {"semantics": [
                {"id": "positive", "color": "#D55E00", "min_pixels": 10},
                {"id": "negative", "color": "#0072B2", "min_pixels": 10},
            ]},
        },
        "integrity": {"required_content": [], "evidence": {}, "scientific_changes": []},
        "consistency": {"constraints": [], "evidence": {}},
        "quantitative": {"transformations": [], "units": {}},
        "deviations": {"records": []},
        "review": {
            "render_sha256": sha256(final),
            "reviewer": "automated-test-fixture",
            "inspection": {"image": "figure.png", "physical_width_mm": 180},
            "visual_status": "agent-inspected",
            "problems": {
                "scientific_expression": "Synthetic fixture content matches its declared two-color test contract.",
                "geometry": "Synthetic rectangles retain their declared pixel geometry without transformations.",
                "annotations": "Synthetic fixture contains no annotations or leaders requiring placement review.",
                "readability": "Synthetic blocks remain visibly separated at the declared physical width.",
                "submission_quality": "Canonical filename and output location follow the fixture contract.",
            },
            "action": "Inspected the generated fixture and accepted it for automated regression testing.",
            "stop_condition": "fixed",
        },
    }
    path = directory / "figure.manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_help_and_capabilities() -> None:
    run_cli("--help")
    result = run_cli("capabilities")
    assert "source-clipping" in result.stdout
    assert "strict-gate" in result.stdout


def test_contract_and_strict_qa_pass(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    run_cli("contract", "check", "--manifest", str(manifest))
    result = run_cli("qa", "run", "--manifest", str(manifest), "--strict")
    assert "Overall: PASS" in result.stdout


def test_source_clipping_fails(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, clipped_source=True)
    result = run_cli("clipping", "source", "--manifest", str(manifest), expected=1)
    assert "top clearance 0px" in result.stdout


def test_whitespace_failure(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    data = json.loads(manifest.read_text())
    data["checks"]["whitespace"]["min_ink_fraction"] = 0.9
    manifest.write_text(json.dumps(data))
    result = run_cli("whitespace", "audit", "--manifest", str(manifest), expected=1)
    assert "global-ink-fraction" in result.stdout


def test_raster_crop_rejects_clipped_source(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    output = tmp_path / "cropped.png"
    make_image(source, clipped=True)
    result = run_cli("raster", "crop", str(source), str(output), expected=2)
    assert "already be clipped" in result.stderr


def test_skill_line_limit() -> None:
    assert len((ROOT / "SKILL.md").read_text().splitlines()) <= 100


def test_text_containment_pass_and_fail(tmp_path: Path) -> None:
    spec = tmp_path / "containment.json"
    spec.write_text(json.dumps({
        "panel": "a",
        "records": [{
            "id": "inside",
            "text_bbox_px": [20, 20, 80, 40],
            "container_bbox_px": [10, 10, 90, 50],
            "min_padding_px": 2,
        }],
    }))
    run_cli("labels", "contain", "--spec", str(spec))

    spec.write_text(json.dumps({
        "panel": "a",
        "records": [{
            "id": "overflow",
            "text_bbox_px": [20, 20, 94, 40],
            "container_bbox_px": [10, 10, 90, 50],
            "min_padding_px": 2,
        }],
    }))
    result = run_cli("labels", "contain", "--spec", str(spec), expected=1)
    assert "text-outside-container" in result.stdout


def test_strict_qa_rejects_vacuous_manifest(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    data = json.loads(manifest.read_text())
    data["outputs"] = [{"path": "_qa/figure.png"}]
    (tmp_path / "_qa").mkdir()
    (tmp_path / "_qa" / "figure.png").write_bytes((tmp_path / "figure.png").read_bytes())
    data["panels"][0]["min_clearance_px"] = 0
    data["panels"][0]["allow_touch_edges"] = ["left", "right", "top", "bottom"]
    data["panels"][0]["source_stage"] = "padded-derivative"
    data["checks"]["boundaries"]["bands"] = []
    data["review"]["problems"] = {key: "checked" for key in data["review"]["problems"]}
    data["review"]["action"] = "accepted"
    data["review"]["reviewer"] = ""
    data["review"]["inspection"] = {}
    data["review"]["visual_status"] = ""
    data["review"]["render_sha256"] = sha256(tmp_path / "_qa" / "figure.png")
    manifest.write_text(json.dumps(data))

    result = run_cli("qa", "run", "--manifest", str(manifest), "--strict", expected=1)
    for rule in (
        "canonical-output-location",
        "composite-clearance-policy",
        "edge-exception-policy",
        "source-provenance",
        "boundary-policy",
        "review-substantive-category",
        "review-reviewer",
        "review-inspection",
        "review-visual-status",
    ):
        assert rule in result.stdout
