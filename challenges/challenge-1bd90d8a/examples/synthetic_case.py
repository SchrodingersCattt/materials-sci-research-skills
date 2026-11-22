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
    "title": "Synthetic signalling schematic (fixture)",
    "width": 960,
    "height": 460,
    "caption": "Figure 1. Synthetic fixture diagram; not a case result.",
    "legend": {
        "compound": "entity (declared compound)",
        "process": "entity (declared protein)",
        "assay": "medium (declared compartment)",
        "output": "readout (declared measurement)",
    },
    "relation_key": {
        "activate": "activation",
        "inhibit": "inhibition",
        "translocate": "translocation",
    },
    "nodes": [
        {"id": "ligand", "x": 40, "y": 60, "w": 180, "h": 62, "label": "ligand A",
         "class": "entity", "position": "compound", "subfigure": "(a)",
         "source": "fixture/case.md", "locator": "line 12"},
        {"id": "receptor", "x": 300, "y": 60, "w": 200, "h": 62, "label": "receptor R",
         "class": "entity", "position": "process", "subfigure": "(a)",
         "source": "fixture/case.md", "locator": "line 14"},
        {"id": "kinase", "x": 600, "y": 60, "w": 220, "h": 62, "label": "kinase K",
         "class": "entity", "position": "process",
         "source": "fixture/case.md", "locator": "line 15"},
        {"id": "cytoplasm", "x": 300, "y": 200, "w": 200, "h": 62, "label": "cytoplasm",
         "class": "medium", "position": "assay",
         "source": "fixture/case.md", "locator": "line 18"},
        {"id": "readout", "x": 600, "y": 200, "w": 220, "h": 62, "label": "K activity",
         "class": "readout", "position": "output", "value": 2.4, "unit": "fold",
         "subfigure": "(b)", "source": "fixture/data.csv", "locator": "row 3, fold_change"},
        {"id": "blocker", "x": 40, "y": 200, "w": 180, "h": 62, "label": "blocker B",
         "class": "entity", "position": "compound",
         "source": "fixture/case.md", "locator": "line 22"},
    ],
    "edges": [
        {"from": "ligand", "to": "receptor", "polarity": "activate", "label": "binds",
         "class": "relation", "source": "fixture/case.md", "locator": "line 30"},
        {"from": "blocker", "to": "receptor", "polarity": "inhibit", "label": "blocks",
         "class": "relation", "source": "fixture/case.md", "locator": "line 31"},
        {"from": "receptor", "to": "kinase", "polarity": "activate",
         "class": "relation", "source": "fixture/case.md", "locator": "line 32"},
        {"from": "kinase", "to": "cytoplasm", "polarity": "translocate",
         "class": "relation", "source": "fixture/case.md", "locator": "line 34"},
        {"from": "cytoplasm", "to": "readout", "polarity": "activate", "label": "measured",
         "class": "relation", "source": "fixture/data.csv", "locator": "row 3"},
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
