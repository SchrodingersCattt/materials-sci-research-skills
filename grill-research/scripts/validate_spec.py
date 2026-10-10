#!/usr/bin/env python3
"""Validate a grill-research benchmark contract and its freeze gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "benchmark-spec.schema.json"


def load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("YAML validation requires PyYAML; use JSON instead") from exc
        value = yaml.safe_load(text)
    else:
        value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("benchmark specification must be an object")
    return value


def schema_errors(document: dict[str, Any]) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:  # pragma: no cover - schema validation is optional at runtime
        return []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(document), key=str)]


def static_errors(document: dict[str, Any]) -> list[str]:
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
        signoff = decisions.get("reviewer_signoff", []) if isinstance(decisions, dict) else []
        if not signoff:
            errors.append("frozen specifications require reviewer sign-off")
        evidence = document.get("freeze_evidence")
        if not isinstance(evidence, dict) or any(not str(evidence.get(key, "")).strip() for key in ("schema_check", "static_check", "threat_challenge", "example_check")):
            errors.append("frozen specifications require complete freeze evidence")
        validation = document.get("validation")
        if not isinstance(validation, dict) or any(not str(validation.get(key, "")).strip() for key in ("schema", "static", "examples", "threats")):
            errors.append("frozen specifications require schema, static, example, and threat test evidence")
        examples = document.get("examples", {})
        if not isinstance(examples, dict) or len(examples.get("domains", [])) < 2 or len(examples.get("scoring_walkthroughs", [])) < 3:
            errors.append("frozen specifications require two domains and three scoring walkthroughs")
    return errors


def validate(path: Path) -> list[str]:
    try:
        document = load_document(path)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        return [str(exc)]
    return schema_errors(document) + static_errors(document)


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
