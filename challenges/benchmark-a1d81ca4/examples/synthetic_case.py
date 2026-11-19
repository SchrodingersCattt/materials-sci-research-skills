"""Synthetic benchmark fixture: a two-case set, a reference answer set and a weak answer set.

Everything here is invented for interface testing: the material, the expected answers and the
scoring anchors. The material files are written to disk so the validator's resolvable-material
check exercises a real path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MATERIAL_A = """# Synthetic source A (fixture)

Filled specimens reached 31.2 MPa in the synthetic batch, and the fixture caption states that the
bars show the standard deviation. No significance test is reported in the fixture.
"""

MATERIAL_B = """# Synthetic source B (fixture)

The synthetic filling was associated with the strength increase; the fixture states that the design
cannot establish causation. A single synthetic batch was evaluated, with six specimens per group.
"""


def spec() -> dict:
    return {
        "schema": "benchmark-spec/v1",
        "title": "Synthetic reading/writing benchmark (fixture)",
        "purpose": "Interface fixture only: exercise case structure, anchor validation and scoring.",
        "min_cases": 2,
        "scoring_rule": "sum of matched anchor weights minus matched penalties, clipped to max_points",
        "cases": [
            {
                "id": "r01",
                "kind": "reading",
                "title": "Report the fixture values without adding significance",
                "instruction": ("Report the two fixture strength values with their unit and say what "
                                "the error bars represent and whether a significance test is "
                                "reported."),
                "material": [{"path": "material-a.md", "locator": "synthetic source A"}],
                "expected": {
                    "values": "31.2 MPa for the filled group; the fixture reports one group value",
                    "error_bars": "standard deviation (SD) as stated in the caption",
                    "significance": "not reported in the fixture",
                },
                "max_points": 4,
                "anchors": [
                    {"id": "a1", "kind": "required", "points": 1, "text": "31.2",
                     "match_any": ["31.2", "31.2 mpa"]},
                    {"id": "a2", "kind": "required", "points": 1, "text": "unit is MPa",
                     "match_any": ["mpa"]},
                    {"id": "a3", "kind": "required", "points": 1,
                     "text": "error bars are the standard deviation as stated",
                     "match_any": ["standard deviation", "sd as stated"]},
                    {"id": "a4", "kind": "required", "points": 1,
                     "text": "no significance test is reported",
                     "match_any": ["no significance test", "not reported in the fixture"]},
                    {"id": "a5", "kind": "penalty", "points": 2,
                     "text": "claims statistical significance the fixture does not report",
                     "match_any": ["significantly higher", "statistically significant"]},
                ],
            },
            {
                "id": "w01",
                "kind": "writing",
                "title": "State an association as an association",
                "instruction": ("Write one sentence about the filling and the strength increase, "
                                "keeping the evidence strength the fixture reports."),
                "material": [{"path": "material-b.md", "locator": "synthetic source B"}],
                "expected": {
                    "wording": "association, not causation",
                    "scale": "a single synthetic batch with six specimens per group",
                },
                "max_points": 3,
                "anchors": [
                    {"id": "b1", "kind": "required", "points": 1,
                     "text": "uses associational wording",
                     "match_any": ["associated with", "correlat"]},
                    {"id": "b2", "kind": "required", "points": 1,
                     "text": "does not assert causation",
                     "match_any": ["cannot establish causation", "not causal", "no causal"]},
                    {"id": "b3", "kind": "bonus", "points": 1,
                     "text": "notes the single-batch limitation",
                     "match_any": ["single synthetic batch", "one synthetic batch"]},
                    {"id": "b4", "kind": "penalty", "points": 2,
                     "text": "asserts causation the fixture cannot support",
                     "match_any": ["causes", "leads to"]},
                ],
            },
        ],
    }


REFERENCE_ANSWERS = {
    "answers": {
        "r01": {
            "values": "The filled group reached 31.2 MPa; the fixture reports one group value.",
            "error_bars": "The caption states the bars show the standard deviation.",
            "significance": "No significance test is reported in the fixture.",
        },
        "w01": {
            "sentence": ("Filling was associated with the strength increase in the fixture, which "
                         "states the design cannot establish causation; the result comes from a "
                         "single synthetic batch with six specimens per group."),
        },
    }
}

WEAK_ANSWERS = {
    "answers": {
        "r01": {"values": "The filled group was significantly higher than the control.",
                "significance": "The difference is statistically significant."},
        "w01": {"sentence": "Filling causes the strength increase."},
    }
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "material-a.md").write_text(MATERIAL_A, encoding="utf-8")
    (out / "material-b.md").write_text(MATERIAL_B, encoding="utf-8")
    (out / "benchmark-spec.json").write_text(json.dumps(spec(), ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    (out / "answers-reference.json").write_text(
        json.dumps(REFERENCE_ANSWERS, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "answers-weak.json").write_text(json.dumps(WEAK_ANSWERS, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    print(f"synthetic benchmark fixture written to {out}")
    print("Fixture only: no formal case, no official answer, no platform score.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
