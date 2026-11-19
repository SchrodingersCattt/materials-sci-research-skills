"""Synthetic data + sections + quantity plan for the results/discussion self-test."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DATA = """specimen,strength_mpa,unit,n,note
A,31.2,MPa,6,filled
B,24.0,MPa,6,unfilled
"""

RESULTS = """# Results

The filled fixture group reached 31.2 MPa while the unfilled fixture group reached 24.0 MPa, a
difference of 7.2 MPa in the synthetic dataset. Both groups contain six synthetic specimens.

The synthetic caption states that the bars show the standard deviation, and no significance
test is reported in the fixture. [Figure 1]
"""

DISCUSSION = """# Discussion

The synthetic difference of 7.2 MPa is consistent with the direction reported for filled
specimens in the supplied fixture note, although the comparison is limited to a single
synthetic batch. The fixture note reports that the filling was associated with the difference
and that the design cannot establish causation, so no mechanism is asserted here.

No significance test is reported in the fixture, and the long-term stability of the filled
specimens was not evaluated.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "data.csv").write_text(DATA, encoding="utf-8")
    (out / "results.md").write_text(RESULTS, encoding="utf-8")
    (out / "discussion.md").write_text(DISCUSSION, encoding="utf-8")
    (out / "artifacts").mkdir(exist_ok=True)
    # A real 1x1 PNG so the declared figure locator actually exists on disk.
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000d4944415478da63fcffff3f0300050001ff9d5a2f"
        "0000000049454e44ae426082")
    (out / "artifacts" / "fig1.png").write_bytes(png)

    def hash_of(name: str) -> str:
        return hashlib.sha256((out / name).read_bytes()).hexdigest()

    plan = {
        "sections": {"results": "results.md", "discussion": "discussion.md"},
        "quantities": [
            {"id": "qA", "csv": "data.csv", "sha256": hash_of("data.csv"),
             "row_id_column": "specimen", "row_id": "A", "value_column": "strength_mpa",
             "unit_column": "unit"},
            {"id": "qB", "csv": "data.csv", "sha256": hash_of("data.csv"),
             "row_id_column": "specimen", "row_id": "B", "value_column": "strength_mpa",
             "unit_column": "unit"},
        ],
        "claims": [
            {"id": "c1", "section": "results",
             "quote": ("The filled fixture group reached 31.2 MPa while the unfilled fixture "
                       "group reached 24.0 MPa, a\ndifference of 7.2 MPa in the synthetic dataset."),
             "numbers": [
                 {"display": "31.2", "quantity": "qA"},
                 {"display": "24.0", "quantity": "qB"},
                 {"display": "7.2", "calculation": {"op": "difference", "left": "qA", "right": "qB"},
                  "rounding_places": 1},
             ]},
            {"id": "c2", "section": "results",
             "quote": "Both groups contain six synthetic specimens.",
             "numbers": []},
            {"id": "c5", "section": "results",
             "quote": ("The synthetic caption states that the bars show the standard deviation, "
                       "and no significance\ntest is reported in the fixture. [Figure 1]"),
             "numbers": [],
             "references": [{"display": "1", "kind": "figure", "locator": "artifacts/fig1.png"}],
             "required_qualifiers": ["no significance"]},
            {"id": "c3", "section": "discussion",
             "quote": ("The synthetic difference of 7.2 MPa is consistent with the direction "
                       "reported for filled\nspecimens in the supplied fixture note"),
             "numbers": [
                 {"display": "7.2", "calculation": {"op": "difference", "left": "qA", "right": "qB"},
                  "rounding_places": 1},
             ]},
            {"id": "c4", "section": "discussion",
             "quote": "No significance test is reported in the fixture, and the long-term stability of the filled\nspecimens was not evaluated.",
             "numbers": [],
             "required_qualifiers": ["No significance test is reported", "was not evaluated"]},        ],
        "source_quotes": [
            {"path": "data.csv", "sha256": hash_of("data.csv"), "quote": "A,31.2,MPa,6,filled"},
            {"path": "data.csv", "sha256": hash_of("data.csv"), "quote": "B,24.0,MPa,6,unfilled"},
        ],
    }
    (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"synthetic results fixture written to {out}")
    print("Fixture only: no formal case, no official answer, no real measurement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
