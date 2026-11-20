"""Zero-install visualize-data command-line interface."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from .checks.pixels import audit_whitespace, check_boundaries, check_clipping, check_colors
from .checks.workflow import check_integrity, check_outputs, check_print, check_review, check_strict_policy, file_hash
from .image_io import crop_background, load_rgb, save_mask
from .manifest import load_manifest, primary_output, resolve_path
from .models import CheckResult, ExitCode, Finding
from .reports import print_report, write_json


ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = {
    "contract": "contract check",
    "static-input": "input rasterize",
    "mask": "mask build|distance",
    "whitespace": "whitespace audit",
    "source-clipping": "clipping source",
    "composite-clipping": "clipping composite",
    "panel-boundaries": "boundary check",
    "labels": "labels place|check|contain",
    "geometry": "geometry check",
    "raster-integrity": "raster crop|compose|check",
    "print-scale": "print check",
    "semantic-colors": "colors check",
    "cross-panel-consistency": "consistency check",
    "quantitative-disclosure": "quantitative check",
    "scientific-integrity": "integrity check",
    "output-discipline": "outputs check",
    "five-problem-review": "review init|check",
    "deviations": "deviations check",
    "strict-gate": "qa run",
}
CAPABILITY_TOP_LEVEL = {
    "contract": "contract",
    "static-input": "input",
    "mask": "mask",
    "whitespace": "whitespace",
    "source-clipping": "clipping",
    "composite-clipping": "clipping",
    "panel-boundaries": "boundary",
    "labels": "labels",
    "geometry": "geometry",
    "raster-integrity": "raster",
    "print-scale": "print",
    "semantic-colors": "colors",
    "cross-panel-consistency": "consistency",
    "quantitative-disclosure": "quantitative",
    "scientific-integrity": "integrity",
    "output-discipline": "outputs",
    "five-problem-review": "review",
    "deviations": "deviations",
    "strict-gate": "qa",
}


def _report_and_exit(results: list[CheckResult], json_path: Path | None) -> int:
    report = print_report(results)
    write_json(report, json_path)
    return ExitCode.PASS if report["passed"] else ExitCode.QA_FAILED


def _config_from_manifest(manifest: dict[str, Any], check: str) -> dict[str, Any]:
    return dict(manifest.get("checks", {}).get(check, {}))


def command_doctor(args: argparse.Namespace) -> int:
    checks = {
        "numpy": importlib.util.find_spec("numpy") is not None,
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "scipy": importlib.util.find_spec("scipy") is not None,
        "jsonschema": importlib.util.find_spec("jsonschema") is not None,
        "pdftoppm": shutil.which("pdftoppm") is not None,
        "rsvg-convert": shutil.which("rsvg-convert") is not None,
    }
    print(json.dumps(checks, indent=2))
    required = ("numpy", "Pillow", "scipy")
    return ExitCode.PASS if all(checks[name] for name in required) else ExitCode.INPUT_ERROR


def command_capabilities(args: argparse.Namespace) -> int:
    print(json.dumps(CAPABILITIES, indent=2))
    return ExitCode.PASS


def command_contract_check(args: argparse.Namespace) -> int:
    load_manifest(args.manifest)
    print(f"PASS: {args.manifest}")
    return ExitCode.PASS


def command_init(args: argparse.Namespace) -> int:
    destination = args.directory.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    files = {
        "figure_contract.md": ROOT / "templates" / "figure_contract.md",
        "figure.manifest.json": ROOT / "templates" / "figure.manifest.json",
        "self_review.md": ROOT / "templates" / "self_review.md",
    }
    for name, source in files.items():
        target = destination / name
        if target.exists() and not args.force:
            raise ValueError(f"Refusing to overwrite {target}; use --force")
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (destination / "_qa").mkdir(exist_ok=True)
    print(json.dumps({"created": [str(destination / name) for name in files]}, indent=2))
    return ExitCode.PASS


def command_input_rasterize(args: argparse.Namespace) -> int:
    image, metadata = load_rgb(args.input, dpi=args.dpi)
    from PIL import Image
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(args.output)
    print(json.dumps({**metadata, "output": str(args.output), "shape": list(image.shape)}, indent=2))
    return ExitCode.PASS


def command_mask_build(args: argparse.Namespace) -> int:
    from .checks.pixels import build_ink_mask
    image, _ = load_rgb(args.image, dpi=args.dpi)
    mask = build_ink_mask(image, background_threshold=args.background_threshold, dilate_px=args.dilate_px)
    save_mask(mask, args.output)
    print(json.dumps({"ink_fraction": float(mask.mean()), "output": str(args.output)}, indent=2))
    return ExitCode.PASS


def command_mask_distance(args: argparse.Namespace) -> int:
    from PIL import Image
    from scipy import ndimage as ndi
    from .checks.pixels import build_ink_mask
    image, _ = load_rgb(args.image, dpi=args.dpi)
    mask = build_ink_mask(image, background_threshold=args.background_threshold)
    distance = ndi.distance_transform_edt(~mask)
    normalized = np.clip(distance / max(float(distance.max()), 1.0), 0, 1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((normalized * 65535).astype("uint16"), mode="I;16").save(args.output)
    print(json.dumps({"max_distance_px": float(distance.max()), "output": str(args.output)}, indent=2))
    return ExitCode.PASS


def command_raster_crop(args: argparse.Namespace) -> int:
    from PIL import Image
    image, _ = load_rgb(args.input, dpi=args.dpi)
    cropped, transform = crop_background(
        image,
        background_threshold=args.background_threshold,
        padding_px=args.padding_px,
        min_source_clearance_px=args.min_source_clearance_px,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(cropped).save(args.output)
    report = {"input": str(args.input), "output": str(args.output), "shape": list(cropped.shape), "crop": transform}
    print(json.dumps(report, indent=2))
    write_json(report, args.json_report)
    return ExitCode.PASS


def command_raster_compose(args: argparse.Namespace) -> int:
    from PIL import Image
    manifest = load_manifest(args.manifest)
    output_record = manifest["outputs"][0]
    output = resolve_path(manifest, output_record["path"] if isinstance(output_record, dict) else output_record)
    width = int(manifest["target"]["canvas_px"][0])
    height = int(manifest["target"]["canvas_px"][1])
    canvas = Image.new("RGB", (width, height), "white")
    transforms = []
    for panel in manifest["panels"]:
        source = Image.fromarray(load_rgb(resolve_path(manifest, panel["source"]))[0])
        x0, y0, x1, y1 = panel["slot"]
        left, top, right, bottom = int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)
        slot_width, slot_height = right - left, bottom - top
        scale = min(slot_width / source.width, slot_height / source.height)
        size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
        resized = source.resize(size, Image.Resampling.LANCZOS)
        paste = (left + (slot_width - size[0]) // 2, top + (slot_height - size[1]) // 2)
        canvas.paste(resized, paste)
        transforms.append({"panel": panel["id"], "scale_x": scale, "scale_y": scale, "paste": paste, "size": size})
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    report = {"output": str(output), "transforms": transforms}
    print(json.dumps(report, indent=2))
    write_json(report, args.json_report)
    return ExitCode.PASS


def command_raster_check(args: argparse.Namespace) -> int:
    data = json.loads(args.transform.read_text(encoding="utf-8"))
    findings = []
    for item in data.get("transforms", []):
        if abs(float(item["scale_x"]) - float(item["scale_y"])) > args.tolerance:
            findings.append(Finding("anisotropic-scaling", "error", f"scale_x != scale_y for {item.get('panel')}", panel=item.get("panel")))
    return _report_and_exit([CheckResult("raster", findings, data)], args.json_report)


def _load_image_and_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], Any, Path]:
    manifest = load_manifest(args.manifest)
    image_path = args.image.resolve() if getattr(args, "image", None) else primary_output(manifest)
    image, _ = load_rgb(image_path, dpi=int(manifest["target"].get("qa_dpi", 300)))
    return manifest, image, image_path


def command_whitespace(args: argparse.Namespace) -> int:
    manifest, image, _ = _load_image_and_manifest(args)
    config = _config_from_manifest(manifest, "whitespace")
    config.setdefault("panels", [{"id": panel["id"], "rect": panel["slot"]} for panel in manifest["panels"]])
    return _report_and_exit([audit_whitespace(image, config)], args.json_report)


def command_clipping(args: argparse.Namespace) -> int:
    manifest, composite, _ = _load_image_and_manifest(args)
    if args.stage == "composite":
        panels = [
            {
                "id": panel["id"],
                "rect": panel["slot"],
                "min_clearance_px": panel.get("min_clearance_px", 8),
                "allow_touch_edges": panel.get("allow_touch_edges", []),
            }
            for panel in manifest["panels"]
        ]
        results = [check_clipping(composite, panels)]
    else:
        results = []
        for panel in manifest["panels"]:
            source, _ = load_rgb(resolve_path(manifest, panel["source"]), dpi=int(manifest["target"].get("qa_dpi", 300)))
            results.append(check_clipping(source, [{
                "id": panel["id"], "rect": [0, 0, 1, 1],
                "min_clearance_px": panel.get("source_min_clearance_px", 8),
                "allow_touch_edges": panel.get("source_allow_touch_edges", []),
            }]))
    return _report_and_exit(results, args.json_report)


def command_boundary(args: argparse.Namespace) -> int:
    manifest, image, _ = _load_image_and_manifest(args)
    bands = _config_from_manifest(manifest, "boundaries").get("bands", [])
    return _report_and_exit([check_boundaries(image, bands)], args.json_report)


def command_colors(args: argparse.Namespace) -> int:
    manifest, image, _ = _load_image_and_manifest(args)
    semantics = _config_from_manifest(manifest, "colors").get("semantics", [])
    return _report_and_exit([check_colors(image, semantics)], args.json_report)


def command_outputs(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    return _report_and_exit([check_outputs(manifest)], args.json_report)


def command_print(args: argparse.Namespace) -> int:
    manifest, image, _ = _load_image_and_manifest(args)
    return _report_and_exit([check_print(image.shape[:2], manifest["target"])], args.json_report)


def command_integrity(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    return _report_and_exit([check_integrity(manifest)], args.json_report)


def command_review_check(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    output = primary_output(manifest)
    return _report_and_exit([check_review(manifest, file_hash(output))], args.json_report)


def command_review_init(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    output = primary_output(manifest)
    manifest["review"] = {
        "render_sha256": file_hash(output),
        "problems": {
            "scientific_expression": "",
            "geometry": "",
            "annotations": "",
            "readability": "",
            "submission_quality": "",
        },
        "action": "",
        "stop_condition": "fixed",
    }
    manifest.pop("_manifest_path", None)
    manifest.pop("_base_dir", None)
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Initialized review for {output}")
    return ExitCode.PASS


def _load_qa_helpers():
    module_path = ROOT / "qa" / "qa_helpers.py"
    spec = importlib.util.spec_from_file_location("visualize_data_legacy_qa", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load QA helpers: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def command_labels_place(args: argparse.Namespace) -> int:
    helpers = _load_qa_helpers()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    image, _ = load_rgb(Path(spec["image"]))
    records = helpers.whitespace_label_placement(
        image=image,
        items=[(item["id"], tuple(item["target_xy_px"])) for item in spec["items"]],
        cluster_center_px=tuple(spec["cluster_center_px"]),
        fontsize_pt=float(spec["fontsize_pt"]),
        forbidden_rects_px=[tuple(rect) for rect in spec.get("forbidden_rects_px", [])],
        min_data_clearance_px=float(spec.get("min_data_clearance_px", 8.0)),
        min_label_edge_distance_factor=float(spec.get("min_label_edge_distance_factor", 0.4)),
        dpi=float(spec.get("dpi", 220.0)),
    )
    payload = {
        "records": [
            {"id": record.label, "target_xy_px": record.target_xy_px, "text_xy_px": record.text_xy_px, "fontsize_pt": record.fontsize_pt}
            for record in records
        ]
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return ExitCode.PASS


def command_labels_check(args: argparse.Namespace) -> int:
    helpers = _load_qa_helpers()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    image, _ = load_rgb(Path(spec["image"]))
    records = [helpers.LabelRecord(
        label=item["id"], target_xy_px=tuple(item["target_xy_px"]),
        text_xy_px=tuple(item["text_xy_px"]), fontsize_pt=float(item["fontsize_pt"]),
    ) for item in spec["records"]]
    errors = helpers.validate_label_panel(
        panel=spec.get("panel", "labels"), image=image, records=records,
        cluster_center_px=tuple(spec["cluster_center_px"]),
        min_data_clearance_px=float(spec.get("min_data_clearance_px", 8.0)),
        min_label_edge_distance_factor=float(spec.get("min_label_edge_distance_factor", 0.4)),
        dpi=float(spec.get("dpi", 220.0)),
    )
    findings = [Finding(error.rule, "error", error.detail, panel=error.panel) for error in errors]
    return _report_and_exit([CheckResult("labels", findings)], args.json_report)


def _text_containment_result(spec: dict[str, Any]) -> CheckResult:
    helpers = _load_qa_helpers()
    records = [helpers.ContainedTextRecord(
        label=item["id"],
        text_bbox_px=tuple(item["text_bbox_px"]),
        container_bbox_px=tuple(item["container_bbox_px"]),
        min_padding_px=float(item.get("min_padding_px", spec.get("min_padding_px", 2.0))),
    ) for item in spec.get("records", [])]
    errors = helpers.validate_text_containment(
        panel=spec.get("panel", "text-containment"),
        records=records,
        tolerance_px=float(spec.get("tolerance_px", 0.25)),
    )
    findings = [Finding(error.rule, "error", error.detail, panel=error.panel) for error in errors]
    return CheckResult("text-containment", findings, {"record_count": len(records)})


def command_labels_contain(args: argparse.Namespace) -> int:
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    return _report_and_exit([_text_containment_result(spec)], args.json_report)


def text_containment_manifest_result(manifest: dict[str, Any]) -> CheckResult:
    config = _config_from_manifest(manifest, "text_containment")
    applicable = config.get("applicable")
    if applicable is False:
        reason = str(config.get("reason", "")).strip()
        findings = [] if reason else [Finding(
            "text-containment-declaration", "error",
            "checks.text_containment.reason is required when applicable is false",
        )]
        return CheckResult("text-containment", findings, {"applicable": False, "reason": reason})
    if applicable is not True:
        return CheckResult("text-containment", [Finding(
            "text-containment-declaration", "error",
            "Declare checks.text_containment.applicable as true or false",
        )])
    spec_value = config.get("spec")
    if not spec_value:
        return CheckResult("text-containment", [Finding(
            "text-containment-declaration", "error",
            "checks.text_containment.spec is required when applicable is true",
        )])
    spec_path = resolve_path(manifest, str(spec_value))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if not spec.get("records"):
        return CheckResult("text-containment", [Finding(
            "text-containment-declaration", "error",
            f"No renderer-measured records in {spec_path}",
        )])
    return _text_containment_result(spec)


def command_declaration_check(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    result = declaration_result(manifest, args.section, args.required_fields)
    return _report_and_exit([result], args.json_report)


def declaration_result(manifest: dict[str, Any], section_name: str, required_fields: list[str]) -> CheckResult:
    section = manifest.get(section_name)
    findings = []
    if section is None:
        findings.append(Finding(f"{section_name}-declaration", "error", f"Manifest section {section_name!r} is missing"))
    elif isinstance(section, dict):
        for field in required_fields:
            if field not in section:
                findings.append(Finding(f"{section_name}-field", "error", f"Missing {section_name}.{field}"))
    return CheckResult(section_name, findings, {"declaration": section})


def command_geometry_check(args: argparse.Namespace) -> int:
    data = json.loads(args.metadata.read_text(encoding="utf-8"))
    findings = []
    for transform in data.get("transforms", []):
        scales = [float(transform[key]) for key in ("scale_x", "scale_y") if key in transform]
        if len(scales) == 2 and abs(scales[0] - scales[1]) > args.tolerance:
            findings.append(Finding("isotropic-transform", "error", "scale_x and scale_y differ", panel=transform.get("panel")))
    for endpoint in data.get("endpoints", []):
        distance = float(endpoint["distance_px"])
        tolerance = float(endpoint.get("tolerance_px", args.endpoint_tolerance_px))
        if distance > tolerance:
            findings.append(Finding("annotation-endpoint", "error", f"Endpoint error {distance}px exceeds {tolerance}px", panel=endpoint.get("panel")))
    return _report_and_exit([CheckResult("geometry", findings, data)], args.json_report)


def command_qa_run(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    manifest, image, output = _load_image_and_manifest(args)
    whitespace = _config_from_manifest(manifest, "whitespace")
    whitespace.setdefault("panels", [{"id": panel["id"], "rect": panel["slot"]} for panel in manifest["panels"]])
    composite_panels = [{
        "id": panel["id"], "rect": panel["slot"],
        "min_clearance_px": panel.get("min_clearance_px", 8),
        "allow_touch_edges": panel.get("allow_touch_edges", []),
    } for panel in manifest["panels"]]
    results = [
        check_outputs(manifest),
        check_print(image.shape[:2], manifest["target"]),
        audit_whitespace(image, whitespace),
        check_clipping(image, composite_panels),
        check_boundaries(image, _config_from_manifest(manifest, "boundaries").get("bands", [])),
        check_colors(image, _config_from_manifest(manifest, "colors").get("semantics", [])),
        check_integrity(manifest),
    ]
    for panel in manifest["panels"]:
        source, _ = load_rgb(resolve_path(manifest, panel["source"]), dpi=int(manifest["target"].get("qa_dpi", 300)))
        results.append(check_clipping(source, [{
            "id": panel["id"], "rect": [0, 0, 1, 1],
            "min_clearance_px": panel.get("source_min_clearance_px", 8),
            "allow_touch_edges": panel.get("source_allow_touch_edges", []),
        }]))
    if args.strict:
        results.extend([
            check_strict_policy(manifest),
            declaration_result(manifest, "consistency", ["constraints", "evidence"]),
            declaration_result(manifest, "quantitative", ["transformations", "units"]),
            declaration_result(manifest, "deviations", ["records"]),
            text_containment_manifest_result(manifest),
        ])
        results.append(check_review(manifest, file_hash(output)))
    report = print_report(results)
    report["wall_seconds"] = time.perf_counter() - started
    write_json(report, args.json_report)
    print(f"Wall time: {report['wall_seconds']:.3f}s")
    return ExitCode.PASS if report["passed"] else ExitCode.QA_FAILED


def command_placeholder(args: argparse.Namespace) -> int:
    result = CheckResult(args.command_name, [Finding(
        "not-implemented", "error", "This capability is reserved by the CLI contract but not implemented yet",
    )])
    return _report_and_exit([result], getattr(args, "json_report", None))


def command_skill_check(args: argparse.Namespace) -> int:
    findings: list[Finding] = []
    skill = ROOT / "SKILL.md"
    lines = skill.read_text(encoding="utf-8").splitlines()
    if len(lines) > 100:
        findings.append(Finding("skill-line-count", "error", f"SKILL.md has {len(lines)} lines; maximum is 100"))
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "name: visualize-data" not in text:
        findings.append(Finding("skill-frontmatter", "error", "Missing valid visualize-data frontmatter"))
    pycache = list(ROOT.rglob("__pycache__"))
    if pycache:
        findings.append(Finding("generated-artifacts", "error", f"Found __pycache__: {[str(path) for path in pycache]}"))
    parser = build_parser()
    top_level: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            top_level.update(action.choices)
    test_map_path = ROOT / "tests" / "capability_tests.json"
    if not test_map_path.exists():
        findings.append(Finding("capability-test-map", "error", "tests/capability_tests.json is missing"))
        test_map = {}
    else:
        test_map = json.loads(test_map_path.read_text(encoding="utf-8"))
    for capability, command in CAPABILITY_TOP_LEVEL.items():
        if command not in top_level:
            findings.append(Finding("capability-command", "error", f"{capability} has no parser command {command!r}"))
        if capability not in test_map or not test_map[capability]:
            findings.append(Finding("capability-test", "error", f"{capability} has no declared tests"))
    result = CheckResult("skill", findings, {"line_count": len(lines), "capabilities": CAPABILITIES})
    return _report_and_exit([result], args.json_report)


def add_manifest_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--json-report", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="visualize-data", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities").set_defaults(func=command_capabilities)
    sub.add_parser("doctor").set_defaults(func=command_doctor)
    initialize = sub.add_parser("init"); initialize.add_argument("directory", type=Path); initialize.add_argument("--force", action="store_true"); initialize.set_defaults(func=command_init)

    contract = sub.add_parser("contract").add_subparsers(dest="action", required=True)
    check = contract.add_parser("check"); check.add_argument("--manifest", type=Path, required=True); check.set_defaults(func=command_contract_check)

    input_group = sub.add_parser("input").add_subparsers(dest="action", required=True)
    rasterize = input_group.add_parser("rasterize"); rasterize.add_argument("input", type=Path); rasterize.add_argument("output", type=Path); rasterize.add_argument("--dpi", type=int, default=300); rasterize.set_defaults(func=command_input_rasterize)

    mask = sub.add_parser("mask").add_subparsers(dest="action", required=True)
    build = mask.add_parser("build"); build.add_argument("image", type=Path); build.add_argument("output", type=Path); build.add_argument("--dpi", type=int, default=300); build.add_argument("--background-threshold", type=int, default=245); build.add_argument("--dilate-px", type=int, default=0); build.set_defaults(func=command_mask_build)
    distance = mask.add_parser("distance"); distance.add_argument("image", type=Path); distance.add_argument("output", type=Path); distance.add_argument("--dpi", type=int, default=300); distance.add_argument("--background-threshold", type=int, default=245); distance.set_defaults(func=command_mask_distance)

    whitespace = sub.add_parser("whitespace").add_subparsers(dest="action", required=True)
    audit = whitespace.add_parser("audit"); add_manifest_arguments(audit); audit.set_defaults(func=command_whitespace)

    clipping = sub.add_parser("clipping").add_subparsers(dest="stage", required=True)
    for stage in ("source", "composite"):
        item = clipping.add_parser(stage); add_manifest_arguments(item); item.set_defaults(func=command_clipping)

    boundary = sub.add_parser("boundary").add_subparsers(dest="action", required=True)
    check = boundary.add_parser("check"); add_manifest_arguments(check); check.set_defaults(func=command_boundary)
    colors = sub.add_parser("colors").add_subparsers(dest="action", required=True)
    check = colors.add_parser("check"); add_manifest_arguments(check); check.set_defaults(func=command_colors)
    outputs = sub.add_parser("outputs").add_subparsers(dest="action", required=True)
    check = outputs.add_parser("check"); add_manifest_arguments(check); check.set_defaults(func=command_outputs)
    printing = sub.add_parser("print").add_subparsers(dest="action", required=True)
    check = printing.add_parser("check"); add_manifest_arguments(check); check.set_defaults(func=command_print)
    integrity = sub.add_parser("integrity").add_subparsers(dest="action", required=True)
    check = integrity.add_parser("check"); add_manifest_arguments(check); check.set_defaults(func=command_integrity)
    review = sub.add_parser("review").add_subparsers(dest="action", required=True)
    initialize = review.add_parser("init"); add_manifest_arguments(initialize); initialize.set_defaults(func=command_review_init)
    check = review.add_parser("check"); add_manifest_arguments(check); check.set_defaults(func=command_review_check)

    qa = sub.add_parser("qa").add_subparsers(dest="action", required=True)
    run = qa.add_parser("run"); add_manifest_arguments(run); run.add_argument("--strict", action="store_true"); run.set_defaults(func=command_qa_run)

    skill = sub.add_parser("skill").add_subparsers(dest="action", required=True)
    check = skill.add_parser("check"); check.add_argument("--json-report", type=Path); check.set_defaults(func=command_skill_check)

    raster = sub.add_parser("raster").add_subparsers(dest="action", required=True)
    crop = raster.add_parser("crop"); crop.add_argument("input", type=Path); crop.add_argument("output", type=Path); crop.add_argument("--dpi", type=int, default=300); crop.add_argument("--background-threshold", type=int, default=245); crop.add_argument("--padding-px", type=int, default=8); crop.add_argument("--min-source-clearance-px", type=int, default=1); crop.add_argument("--json-report", type=Path); crop.set_defaults(func=command_raster_crop)
    compose = raster.add_parser("compose"); compose.add_argument("--manifest", type=Path, required=True); compose.add_argument("--json-report", type=Path); compose.set_defaults(func=command_raster_compose)
    check = raster.add_parser("check"); check.add_argument("--transform", type=Path, required=True); check.add_argument("--tolerance", type=float, default=1e-6); check.add_argument("--json-report", type=Path); check.set_defaults(func=command_raster_check)

    labels = sub.add_parser("labels").add_subparsers(dest="action", required=True)
    place = labels.add_parser("place"); place.add_argument("--spec", type=Path, required=True); place.add_argument("--output", type=Path, required=True); place.set_defaults(func=command_labels_place)
    check = labels.add_parser("check"); check.add_argument("--spec", type=Path, required=True); check.add_argument("--json-report", type=Path); check.set_defaults(func=command_labels_check)
    contain = labels.add_parser("contain"); contain.add_argument("--spec", type=Path, required=True); contain.add_argument("--json-report", type=Path); contain.set_defaults(func=command_labels_contain)

    geometry = sub.add_parser("geometry").add_subparsers(dest="action", required=True)
    check = geometry.add_parser("check"); check.add_argument("--metadata", type=Path, required=True); check.add_argument("--tolerance", type=float, default=1e-6); check.add_argument("--endpoint-tolerance-px", type=float, default=2.0); check.add_argument("--json-report", type=Path); check.set_defaults(func=command_geometry_check)

    declarations = {
        "consistency": ("consistency", ["constraints", "evidence"]),
        "quantitative": ("quantitative", ["transformations", "units"]),
        "deviations": ("deviations", ["records"]),
    }
    for name, (section, required) in declarations.items():
        group = sub.add_parser(name).add_subparsers(dest="action", required=True)
        item = group.add_parser("check"); item.add_argument("--manifest", type=Path, required=True); item.add_argument("--json-report", type=Path); item.set_defaults(func=command_declaration_check, section=section, required_fields=required)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, FileNotFoundError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return int(ExitCode.INPUT_ERROR)
    except Exception as exc:  # pragma: no cover - last-resort CLI boundary
        print(f"INTERNAL ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return int(ExitCode.INTERNAL_ERROR)
