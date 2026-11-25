#!/usr/bin/env python3
"""Declared source-row / Decimal / prose mapping checks for a results-and-discussion section.

This is the boundary this helper covers: after the agent has actually read the supplied data,
captions, statistics and literature and has written the two editable sections, this script
re-computes every declared number from the declared source row and proves that the number in
the prose is the number the source supports — with the unit next to it, from the declared
baseline. It is not scientific entailment, not significance testing, and not a substitute for
reading the case.

Exit codes: 0 = every declared check passed, 2 = partial (the report says which check failed).

Plan schema (all paths relative to the plan file):

    {
      "sections": {"results": "results.md", "discussion": "discussion.md"},
      "claims": [
        {"id": "c1", "section": "results",
         "quote": "<exact substring of that section file>",
         "numbers": [
            {"display": "7.2",
             "calculation": {"op": "difference", "left": "q1", "right": "q2"},
             "rounding_places": 1}
         ],
         "references": [
            {"display": "1", "kind": "figure", "locator": "artifacts/fig1.png"}
         ],
         "required_qualifiers": ["not reported"]}
      ],
      "quantities": [
        {"id": "q1", "csv": "data.csv", "sha256": "<file hash>", "row_id_column": "specimen",
         "row_id": "A", "value_column": "strength_mpa", "unit_column": "unit"}
      ],
      "source_quotes": [
        {"path": "data.csv", "sha256": "<file hash>", "quote": "<verbatim line>"}
      ]
    }
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import pathlib
import re
import sys
from decimal import Decimal, ROUND_HALF_EVEN

NUM = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
MAX_CLAIMS = 128
MAX_ROWS = 1000


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    plan_file = pathlib.Path(args.plan).resolve()
    out = pathlib.Path(args.outdir).resolve()
    if out.exists():
        parser.error("Use a new output directory; never overwrite a previous report")
    out.mkdir(parents=True)

    report = {
        "status": "partial",
        "checks": [],
        "sources": [],
        "mappings": [],
        "limitations": [
            "Checks declared quantity arithmetic, exact prose values, adjacent units, source "
            "versions and literal qualifiers. It does not check data authenticity, study design, "
            "statistical significance, causality or literature entailment.",
            "No general chart/OCR digitisation and no semantic coverage of undeclared claims.",
            "Only explicit compatible-unit difference and baseline-relative percent, plus exact "
            "values or explicitly declared decimal rounding, are supported.",
        ],
    }

    def check(name, ok, details=None):
        report["checks"].append({"check": name, "passed": bool(ok), "details": details})

    try:
        plan = json.loads(plan_file.read_text(encoding="utf-8"))

        def resolve(relative):
            return (plan_file.parent / relative).resolve()

        quantities = {}
        sections = {key: resolve(value).read_text(encoding="utf-8")
                    for key, value in plan["sections"].items()}
        coverage = {key: [] for key in sections}
        claims = plan["claims"]

        if len(claims) > MAX_CLAIMS:
            raise ValueError(f"More than {MAX_CLAIMS} claims: scope the audit and mark the rest "
                             "unreviewed instead of silently truncating")
        check("unique_claim_ids", len({c["id"] for c in claims}) == len(claims))

        for quantity in plan["quantities"]:
            source = resolve(quantity["csv"])
            check(f"source_version_{quantity['id']}", sha(source) == quantity["sha256"])
            with source.open(newline="", encoding="utf-8") as handle:
                rows = list(itertools.islice(csv.DictReader(handle), MAX_ROWS + 1))
            if len(rows) > MAX_ROWS:
                raise ValueError(f"More than {MAX_ROWS} rows in {source.name}: use a documented "
                                 "scoped source")
            found = [row for row in rows if row[quantity["row_id_column"]] == quantity["row_id"]]
            check(f"source_row_unique_{quantity['id']}", len(found) == 1)
            if len(found) != 1:
                raise ValueError(f"Missing or duplicate source row for {quantity['id']}")
            row = found[0]
            value = Decimal(row[quantity["value_column"]])
            unit = row[quantity["unit_column"]]
            check(f"source_quantity_finite_unit_{quantity['id']}",
                  value.is_finite() and bool(unit.strip()))
            if quantity["id"] in quantities:
                raise ValueError(f"Duplicate quantity id {quantity['id']}")
            quantities[quantity["id"]] = (value, unit)
            report["sources"].append({
                "quantity_id": quantity["id"], "path": str(source), "sha256": sha(source),
                "row": quantity["row_id"], "value_column": quantity["value_column"],
                "actual_value": str(value), "actual_unit": unit,
            })

        for claim in claims:
            claim_id = claim["id"]
            section = claim["section"]
            text = sections[section]
            quote = claim["quote"]
            ok = bool(quote) and text.count(quote) == 1
            check(f"unique_actual_prose_{claim_id}", ok)
            if not ok:
                continue
            start = text.index(quote)
            coverage[section].append((start, start + len(quote)))
            tokens = NUM.findall(quote)
            bindings = claim.get("numbers", [])
            references = claim.get("references", [])
            check(f"every_number_in_declared_quote_bound_{claim_id}",
                  tokens == [b["display"] for b in bindings]
                  + [r["display"] for r in references]
                  or tokens == [b["display"] for b in bindings],
                  {"actual_tokens": tokens,
                   "declared_numbers": [b["display"] for b in bindings],
                   "declared_references": [r["display"] for r in references]})

            for position, binding in enumerate(bindings):
                if "quantity" in binding:
                    value, unit = quantities[binding["quantity"]]
                    provenance = {"quantity": binding["quantity"]}
                else:
                    calculation = binding["calculation"]
                    left, unit = quantities[calculation["left"]]
                    right, right_unit = quantities[calculation["right"]]
                    check(f"compatible_units_{claim_id}_{position}", unit == right_unit)
                    if calculation["op"] == "difference":
                        value = left - right
                    elif calculation["op"] == "relative_percent":
                        value = (left - right) / right * 100
                        unit = "%"
                    else:
                        raise ValueError("Unsupported calculation; this helper does not "
                                         "reconstruct statistical tests")
                    provenance = {"calculation": calculation, "unrounded_value": str(value)}
                if "rounding_places" in binding:
                    value = value.quantize(Decimal(1).scaleb(-int(binding["rounding_places"])),
                                           rounding=ROUND_HALF_EVEN)
                check(f"actual_value_{claim_id}_{position}",
                      Decimal(binding["display"]) == value,
                      {"supported_value": str(value), "display": binding["display"]})
                check(f"actual_unit_adjacent_{claim_id}_{position}",
                      bool(re.search(re.escape(binding["display"]) + r"\s*" + re.escape(unit), quote)),
                      unit)
                report["mappings"].append({
                    "claim": claim_id, "section": section, "char_start": start,
                    "char_end": start + len(quote), "quote": quote,
                    "display": binding["display"], "unit": unit, "provenance": provenance,
                })

            for qualifier in claim.get("required_qualifiers", []):
                check(f"literal_qualifier_{claim_id}", qualifier in quote, qualifier)

            # A figure/table/equation number is not a data value: it must instead be bound to a
            # declared locator, and it is excluded from the numeric-coverage requirement.
            for reference in claim.get("references", []):
                kind = reference.get("kind", "figure")
                display = reference["display"]
                word = {"figure": "Figure", "table": "Table", "equation": "Equation"}.get(kind, kind)
                check(f"reference_marker_{claim_id}_{display}",
                      bool(re.search(re.escape(word) + r"\s*" + re.escape(display), quote)),
                      {"kind": kind, "display": display})
                locator = reference.get("locator")
                exists = bool(locator) and (
                    pathlib.Path(locator).exists() or (plan_file.parent / locator).exists())
                check(f"reference_locator_exists_{claim_id}_{display}", exists,
                      {"kind": kind, "display": display, "locator": locator})
                coverage[section].append((start, start + len(quote)))
                report["mappings"].append({
                    "claim": claim_id, "section": section, "char_start": start,
                    "char_end": start + len(quote), "quote": quote, "display": display,
                    "kind": f"{kind}_reference", "locator": locator,
                    "provenance": {"reference": kind, "locator": locator},
                })

        for section, text in sections.items():
            uncovered = [{"token": match.group(), "char_start": match.start()}
                         for match in NUM.finditer(text)
                         if not any(begin <= match.start() < match.end() <= end
                                    for begin, end in coverage[section])]
            check(f"all_detected_section_numbers_covered_{section}", not uncovered, uncovered)

        for position, source_quote in enumerate(plan.get("source_quotes", [])):
            source = resolve(source_quote["path"])
            check(f"quote_source_version_{position}", sha(source) == source_quote["sha256"])
            check(f"actual_source_quote_{position}",
                  source_quote["quote"] in source.read_text(encoding="utf-8"),
                  {"path": str(source), "quote": source_quote["quote"][:120]})

        report["status"] = ("structural_quantity_checks_passed"
                            if all(item["passed"] for item in report["checks"]) else "partial")

    except Exception as error:  # noqa: BLE001 - the report is the output, so record it
        report["error"] = {"type": type(error).__name__, "message": str(error)}

    finally:
        report["plan_sha256"] = sha(plan_file) if plan_file.is_file() else None
        (out / "quantity-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        failed = [c["check"] for c in report["checks"] if not c["passed"]]
        print(json.dumps({"status": report["status"], "checks": len(report["checks"]),
                          "failed": failed[:10], "report": str(out / "quantity-report.json")},
                         ensure_ascii=False))

    return 2 if report["status"] == "partial" else 0


if __name__ == "__main__":
    sys.exit(main())
