#!/usr/bin/env python3
"""Validate a grill-research benchmark contract and its freeze gate."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "benchmark-spec.schema.json"
VALIDATOR_NAME = "grill-research/scripts/validate_spec.py"


def load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency check is tested via JSON
            raise RuntimeError("PyYAML is required for YAML specs; install -r grill-research/requirements.txt") from exc
        value = yaml.safe_load(text)
    else:
        value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("benchmark specification must be an object")
    return value


def schema_errors(document: dict[str, Any]) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError as exc:
        raise RuntimeError("jsonschema is required for validation; install -r grill-research/requirements.txt") from exc
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(document), key=str)]


def _canonical_input(document: dict[str, Any]) -> str:
    payload = copy.deepcopy(document)
    payload.pop("validation", None)
    payload.pop("freeze_evidence", None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _input_sha256(document: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_input(document).encode("utf-8")).hexdigest()


def _path_and_digest(base: Path, relative: Any, expected: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{label} must name an evidence artifact")
        return None
    if not isinstance(expected, str) or len(expected) != 64:
        errors.append(f"{label} must include a 64-character SHA-256 digest")
        return None
    path = (base / relative).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        errors.append(f"{label} points outside the specification directory")
        return None
    if not path.is_file():
        errors.append(f"{label} artifact does not exist: {relative}")
        return None
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        errors.append(f"{label} artifact digest does not match: {relative}")
        return None
    return path


def _frozen_content_errors(document: dict[str, Any], base: Path) -> list[str]:
    errors: list[str] = []
    required_strings = (
        ("provenance", "question"), ("benchmark", "name"), ("benchmark", "claim"),
        ("benchmark", "scope"), ("benchmark", "progress_signal"), ("research_question",),
        ("task_interface", "unit"), ("task_interface", "distribution"),
        ("task_interface", "generation_or_sourcing"), ("task_interface", "release"),
        ("task_interface", "observability"), ("evaluation", "aggregation"),
        ("evaluation", "budgets"), ("evaluation", "ranking_and_ties"),
        ("evaluation", "uncertainty_reporting"), ("scientific_validity", "evidence"),
        ("scientific_validity", "oracle"), ("scientific_validity", "uncertainty"),
        ("scientific_validity", "failure_and_abstention"), ("sustainability", "fresh_hidden_tasks"),
        ("sustainability", "independent_audit"), ("sustainability", "reproducibility"),
        ("sustainability", "versioning"),
    )
    for path in required_strings:
        value: Any = document
        for part in path:
            value = value.get(part) if isinstance(value, dict) else None
        if not isinstance(value, str) or not value.strip():
            errors.append(f"frozen specifications require {'.'.join(path)}")

    topology = document.get("topology", {})
    if not isinstance(topology, dict) or topology.get("model") == "undecided":
        errors.append("frozen specifications require a selected benchmark topology")
    if not isinstance(topology, dict) or not topology.get("tracks") or topology.get("overall_ranking") is None:
        errors.append("frozen specifications require tracks and an explicit overall-ranking decision")
    task = document.get("task_interface", {})
    resources = task.get("allowed_resources", {}) if isinstance(task, dict) else {}
    submission = task.get("submission", {}) if isinstance(task, dict) else {}
    for label, value in (("allowed resources", resources), ("submission", submission)):
        if not isinstance(value, dict) or any(not str(item).strip() and item != [] for item in value.values()):
            errors.append(f"frozen specifications require complete {label}")
    validity = document.get("scientific_validity", {})
    if not isinstance(validity, dict) or not validity.get("constraints"):
        errors.append("frozen specifications require scientific constraints")
    evaluation = document.get("evaluation", {})
    if not isinstance(evaluation, dict) or not evaluation.get("eligibility_gates") or not evaluation.get("baselines"):
        errors.append("frozen specifications require eligibility gates and baselines")
    metrics = evaluation.get("metrics", []) if isinstance(evaluation, dict) else []
    if not metrics or any(not isinstance(metric, dict) or any(not str(metric.get(key, "")).strip() for key in ("name", "formula", "unit", "direction", "role")) for metric in metrics):
        errors.append("frozen specifications require complete metric formulas")
    threats = document.get("threat_model", {})
    if not isinstance(threats, dict) or not threats.get("threats"):
        errors.append("frozen specifications require concrete metric threats and defenses")

    validation = document.get("validation")
    expected_input = _input_sha256(document)
    if not isinstance(validation, dict):
        errors.append("frozen specifications require machine-generated validation records")
    else:
        for name in ("schema", "static", "examples", "threats"):
            entry = validation.get(name)
            if not isinstance(entry, dict) or entry.get("status") != "pass":
                errors.append(f"validation.{name} must be a machine-generated pass record")
                continue
            if entry.get("generated_by") != VALIDATOR_NAME or entry.get("input_sha256") != expected_input:
                errors.append(f"validation.{name} is not bound to this specification and validator")
            report = _path_and_digest(base, entry.get("report_path"), entry.get("report_sha256"), f"validation.{name}", errors)
            if report:
                try:
                    report_data = json.loads(report.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    errors.append(f"validation.{name} report is not JSON")
                else:
                    if report_data.get("status") != "pass" or report_data.get("input_sha256") != expected_input:
                        errors.append(f"validation.{name} report is not a matching pass result")

    evidence = document.get("freeze_evidence")
    if not isinstance(evidence, dict):
        errors.append("frozen specifications require machine-verifiable freeze evidence")
    else:
        for name in ("schema_check", "static_check", "threat_challenge", "example_check"):
            item = evidence.get(name)
            if not isinstance(item, dict) or item.get("status") != "pass":
                errors.append(f"freeze_evidence.{name} must be a verified pass record")
                continue
            _path_and_digest(base, item.get("artifact_path"), item.get("artifact_sha256"), f"freeze_evidence.{name}", errors)

    signoff = document.get("decisions", {}).get("reviewer_signoff", []) if isinstance(document.get("decisions"), dict) else []
    if not signoff:
        errors.append("frozen specifications require reviewer sign-off")
    for item in signoff:
        if not isinstance(item, dict) or item.get("outcome") != "accepted":
            errors.append("frozen reviewer sign-off must include an accepted evidence record")
            continue
        _path_and_digest(base, item.get("evidence_path"), item.get("evidence_sha256"), "reviewer sign-off", errors)
    return errors


def static_errors(document: dict[str, Any], base: Path | None = None) -> list[str]:
    errors: list[str] = []
    if document.get("status") not in {"draft", "review", "frozen"}:
        errors.append("status must be draft, review, or frozen")
    decisions = document.get("decisions", {})
    records = decisions.get("records", []) if isinstance(decisions, dict) else []
    unresolved = document.get("unresolved", [])
    if not isinstance(records, list):
        errors.append("decisions.records must be a list")
        records = []
    if not isinstance(unresolved, list):
        errors.append("unresolved must be a list")
        unresolved = []
    if document.get("status") == "frozen":
        if unresolved:
            errors.append("frozen specifications cannot contain unresolved questions")
        states = {record.get("state") for record in records if isinstance(record, dict)}
        if not records or states != {"decided"}:
            errors.append("frozen specifications require at least one decided decision and no other states")
        reviews = document.get("reviews", [])
        if not reviews or not any(item.get("outcome") == "accepted" for item in reviews if isinstance(item, dict)):
            errors.append("frozen specifications require an accepted substantive review")
        if base is None:
            errors.append("frozen validation requires the specification file directory")
        else:
            errors.extend(_frozen_content_errors(document, base))
    return errors


def validate(path: Path) -> list[str]:
    try:
        document = load_document(path)
        schema = schema_errors(document)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        return [str(exc)]
    return schema + static_errors(document, path.resolve().parent)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    errors = validate(args.spec)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"PASS: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
