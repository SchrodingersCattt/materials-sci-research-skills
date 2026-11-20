"""Figure-manifest loading, path resolution, and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {"version", "figure", "outputs", "target", "panels", "checks"}


def load_manifest(path: Path) -> dict[str, Any]:
    path = path.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "figure-manifest.schema.json"
    try:
        import jsonschema
    except ImportError:
        jsonschema = None
    if jsonschema is not None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        raise ValueError(f"Manifest missing top-level keys: {', '.join(missing)}")
    if data["version"] != 1:
        raise ValueError(f"Unsupported manifest version: {data['version']!r}")
    if not isinstance(data["panels"], list) or not data["panels"]:
        raise ValueError("Manifest panels must be a non-empty list")
    for panel in data["panels"]:
        if not {"id", "source", "slot"} <= panel.keys():
            raise ValueError("Each panel requires id, source, and slot")
    data["_manifest_path"] = str(path)
    data["_base_dir"] = str(path.parent)
    return data


def resolve_path(manifest: dict[str, Any], value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path(manifest["_base_dir"]) / path
    return path.resolve()


def primary_output(manifest: dict[str, Any]) -> Path:
    outputs = manifest["outputs"]
    if not outputs:
        raise ValueError("Manifest outputs cannot be empty")
    first = outputs[0]
    value = first["path"] if isinstance(first, dict) else first
    return resolve_path(manifest, value)
