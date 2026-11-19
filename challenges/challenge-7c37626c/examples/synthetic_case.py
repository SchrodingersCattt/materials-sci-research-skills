"""Synthetic formula fixture: exact arithmetic, a stated range, a missing bound and a violation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPEC = {
    "schema": "formula-spec/v1",
    "case_note": "Synthetic interface fixture; no formal case content.",
    "steps": [
        {
            "id": "f1",
            "expression": "(m1 * v1 + m2 * v2) / (m1 + m2)",
            "source_locator": "fixture p3 (synthetic momentum balance)",
            "variables": {
                "m1": {"value": "2", "source_locator": "fixture table row 1"},
                "v1": {"value": "3.5", "source_locator": "fixture table row 1"},
                "m2": {"value": "1", "source_locator": "fixture table row 2"},
                "v2": {"value": "-1.5", "source_locator": "fixture table row 2"},
            },
            "domains": {"m1": "> 0", "m2": "> 0"},
            "unit": "m/s",
            "display_places": 4,
        },
        {
            "id": "f2",
            "expression": "pi_r * r^2 * h",
            "source_locator": "fixture p4 (synthetic volume)",
            "variables": {
                "pi_r": {"value": "3.14159265358979323846", "source_locator": "fixture constant"},
                "r": {"value": "2.5", "source_locator": "fixture table row 3"},
                "h": {"value": "10", "source_locator": "fixture table row 3"},
            },
            "domains": {"r": "> 0", "h": "> 0"},
            "unit": "cm^3",
            "declared_range": {"lower": "100", "upper": "300",
                              "source_locator": "fixture p4 states this range"},
            "display_places": 3,
        },
        {
            "id": "f3",
            "expression": "q / (t2 - t1)",
            "source_locator": "fixture p5 (synthetic rate)",
            "variables": {
                "q": {"value": "45", "source_locator": "fixture table row 5"},
                "t2": {"value": "60", "source_locator": "fixture table row 6"},
                "t1": {"value": "60", "source_locator": "fixture table row 6"},
            },
            "unit": "J/s",
        },
        {
            "id": "f4",
            "expression": "n * k * T / V",
            "source_locator": "fixture p6 (synthetic pressure)",
            "variables": {
                "n": {"value": "2", "source_locator": "fixture table row 7"},
                "k": {"value": "1.380649e-23", "source_locator": "fixture constant"},
                "V": {"value": "0.0224", "source_locator": "fixture table row 7"},
            },
            "domains": {"V": "> 0"},
            "unit": "Pa",
            "display_places": 6,
        },
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "formula-spec.json").write_text(json.dumps(SPEC, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    # f4 has no declared temperature; the point of the fixture is that the checker refuses it.
    print(f"synthetic formula fixture written to {out}")
    print("Fixture only: no formal case, no official answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
