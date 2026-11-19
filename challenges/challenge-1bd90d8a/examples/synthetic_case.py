"""Synthetic data and specs for the figure-builder self-test."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DATA = """specimen,group,strength_mpa,unit,sd,n,condition
A,filled,31.2,MPa,1.4,6,25 C
B,unfilled,24.0,MPa,1.1,6,25 C
"""

FIGURE_SPEC = {
    "kind": "bar",
    "title": "Synthetic strength comparison (fixture)",
    "data": "data.csv",
    "x": "specimen",
    "value": "strength_mpa",
    "series": "group",
    "error_low": "sd",
    "error_high": "sd",
    "unit": "MPa",
    "x_label": "specimen",
    "y_label": "strength (MPa)",
    "error_meaning": "SD as declared in the fixture data column 'sd'",
    "note": "fixture values only; no significance test is reported",
    "source": "synthetic fixture (not a formal case)",
    "width": 900,
    "height": 560,
}

DIAGRAM_SPEC = {
    "title": "Synthetic assay flow (fixture)",
    "width": 960,
    "height": 420,
    "caption": "Figure 1. Synthetic fixture diagram; not a case result.",
    "legend": {"input": "supplied data", "process": "declared processing", "output": "deliverable"},
    "nodes": [
        {"id": "in", "x": 40, "y": 150, "w": 180, "h": 62, "label": "supplied data",
         "position": "input"},
        {"id": "norm", "x": 300, "y": 60, "w": 200, "h": 62, "label": "normalise units",
         "detail": "declared factors only", "position": "process"},
        {"id": "check", "x": 300, "y": 220, "w": 200, "h": 62, "label": "conflict check",
         "position": "decision"},
        {"id": "out", "x": 600, "y": 150, "w": 200, "h": 62, "label": "cleaned table",
         "position": "output"},
    ],
    "edges": [
        {"from": "in", "to": "norm"},
        {"from": "norm", "to": "check", "label": "review"},
        {"from": "check", "to": "out", "label": "pass"},
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "data.csv").write_text(DATA, encoding="utf-8")
    (out / "chart-spec.json").write_text(json.dumps(FIGURE_SPEC, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    (out / "diagram-spec.json").write_text(json.dumps(DIAGRAM_SPEC, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    print(f"synthetic figure fixture written to {out}")
    print("Fixture only: no formal case, no official answer, no real measurement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
