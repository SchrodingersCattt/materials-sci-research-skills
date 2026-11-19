"""Synthetic mind-map fixture: a four-branch tree whose leaves carry evidence locators."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPEC = {
    "title": "Synthetic knowledge map (fixture)",
    "width": 1100,
    "height": 760,
    "caption": "Figure 1. Synthetic fixture map; not a case result.",
    "root": {
        "id": "root",
        "label": "Synthetic study",
        "evidence": "fixture p1",
        "children": [
            {"id": "q", "label": "Question", "edge": "asks", "evidence": "fixture p2",
             "children": [
                 {"id": "q1", "label": "Does filling raise strength?", "evidence": "fixture p2"},
                 {"id": "q2", "label": "Which conditions matter?", "evidence": "fixture p3"},
             ]},
            {"id": "m", "label": "Method", "edge": "uses", "evidence": "fixture p4",
             "children": [
                 {"id": "m1", "label": "Printed specimens", "evidence": "fixture p4"},
                 {"id": "m2", "label": "Tensile test at 25 C", "evidence": "fixture p5"},
                 {"id": "m3", "label": "Six specimens per group", "evidence": "fixture p5"},
             ]},
            {"id": "r", "label": "Results", "edge": "reports", "evidence": "fixture p6",
             "children": [
                 {"id": "r1", "label": "31.2 MPa filled", "evidence": "fixture p6"},
                 {"id": "r2", "label": "24.0 MPa unfilled", "evidence": "fixture p6"},
             ]},
            {"id": "l", "label": "Limits", "edge": "bounded by", "evidence": "fixture p7",
             "children": [
                 {"id": "l1", "label": "No significance test", "evidence": "fixture p7"},
                 {"id": "l2", "label": "Single batch", "evidence": "fixture p7"},
             ]},
        ],
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "mindmap-spec.json").write_text(json.dumps(SPEC, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    print(f"synthetic mind-map fixture written to {out}")
    print("Fixture only: no formal case, no official answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
