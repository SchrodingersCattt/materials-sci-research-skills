"""Scan a deliverable's numbers against the supplied data, with no hand-written plan.

`quantity_audit.py` proves a declared number matches a declared source value, but it needs the agent
to hand-write a plan listing every quote and every number up front - so in practice it either does
not run or runs on a subset. This does the check the other way round: it reads the prose, finds every
number in it, reads every numeric value in the supplied data files, and classifies each prose number
as declared, a declared arithmetic combination, a rounding of a declared value, or undeclared.

Undeclared numbers are the defect list: they are the ones a reviewer cannot trace, and the ones the
rubric's traceability sub-point is about.

    python scripts/number_scan.py --md work/results.md --md work/discussion.md \
        --data material --out work/number-scan.json [--tolerance 0.05]

Exit 0 when every number is traceable, exit 2 when something is not. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

UNIT = (r"(?:%|‰|MPa|kPa|GPa|Pa|N|kN|mN|J|kJ|mJ|W|kW|mW|A|mA|V|mV|K|°C|C|s|ms|µs|us|ns|min|h|"
        r"d|m|cm|mm|µm|um|nm|L|mL|µL|uL|g|mg|µg|ug|kg|mol|mmol|µmol|umol|M|mM|µM|uM|nM|rpm|"
        r"Hz|kHz|MHz|dB|ppm|ppb|wt%|at%|vol%|mol%|eq|arb\.?\s*u\.?|a\.u\.)")
NUMBER = re.compile(rf"(?<![\w.])(\d+(?:[.,]\d+)?)(?:\s*(?:(?:±|\+/-)\s*(\d+(?:[.,]\d+)?)))?"
                    rf"\s*({UNIT})?(?![\w])")
# A sentence splitter would break "34.5" into "34" and "5", so the unit of context is the
# line, which is also what a reviewer reads when locating a claim.
CONTEXT = re.compile(r"[^\n]+")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx", ".pptx", ".xlsx", ".zip", ".pyc"}


def to_float(text: str) -> float | None:
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def declared_values(paths: list) -> tuple:
    """Every numeric value in the supplied data, with where it came from."""
    values: list = []
    seen = set()

    def add(value, source, locator):
        key = (round(value, 9), source)
        if key in seen:
            return
        seen.add(key)
        values.append({"value": value, "source": source, "locator": locator})

    files: list = []
    for path in paths:
        if path.is_dir():
            files.extend(p for p in sorted(path.rglob("*"))
                         if p.is_file() and p.suffix.lower() not in SKIP_EXT)
        elif path.is_file():
            files.append(path)

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = None

            def walk(node, prefix):
                if isinstance(node, dict):
                    for key, value in node.items():
                        walk(value, f"{prefix}.{key}" if prefix else str(key))
                elif isinstance(node, list):
                    for index, value in enumerate(node):
                        walk(value, f"{prefix}[{index}]")
                elif isinstance(node, bool):
                    return
                elif isinstance(node, (int, float)):
                    add(float(node), path.as_posix(), prefix or "value")

            if payload is not None:
                walk(payload, "")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith(("#", "//", ";")):
                continue
            cells = line.split(",") if "," in line else [line]
            for cell_no, cell in enumerate(cells, start=1):
                for match in NUMBER.finditer(cell):
                    value = to_float(match.group(1))
                    if value is None:
                        continue
                    locator = (f"line {line_no}, column {cell_no}" if len(cells) > 1
                               else f"line {line_no}")
                    add(value, path.as_posix(), locator)
    return values, [p.as_posix() for p in files]


def decimals_of(literal: str) -> int:
    return len(literal.replace(",", "").split(".")[1]) if "." in literal else 0


def same_at_precision(value: float, literal: str, entry_value: float) -> bool:
    """True when the declared value rounds to exactly the number written in the prose.

    Matching on the prose's own precision is what makes this check trustworthy: a value written to one
    decimal only matches a declared value that rounds to that same decimal. A percentage-point band
    would accept a wrong number that happens to sit near the right one - which is exactly the defect
    the scan exists to find.
    """
    places = decimals_of(literal)
    if places == 0:
        return abs(entry_value - value) < 0.5
    return f"{entry_value:.{places}f}" == f"{value:.{places}f}"


def classify(value: float, literal: str, pool: list, rel_tolerance: float) -> dict:
    for entry in pool:
        if same_at_precision(value, literal, entry["value"]):
            return {"status": "declared", "match": entry,
                    "how": "the value itself appears in the supplied data at this precision"}
    # A combination of two declared values. The tolerance here is deliberately tight and relative:
    # a loose band turns a fabricated number into a false pass, which is worse than a false alarm.
    best = None
    for index, left in enumerate(pool):
        for right in pool[index + 1:]:
            a, b = left["value"], right["value"]
            for label, result in (("difference", a - b), ("difference", b - a),
                                  ("sum", a + b),
                                  ("ratio-percent", 100 * a / b if b else None),
                                  ("ratio-percent", 100 * b / a if a else None),
                                  ("product", a * b)):
                if result is None:
                    continue
                limit = max(10 ** -max(decimals_of(literal), 0) / 2, rel_tolerance * abs(result))
                delta = abs(result - value)
                if delta <= limit and (best is None or delta < best[0]):
                    best = (delta, label, left, right)
    if best is not None:
        delta, label, left, right = best
        return {"status": "declared_derived",
                "match": {"left": left, "right": right},
                "how": f"{label} of two declared values ({left['value']} and {right['value']}), "
                       f"off by {delta:.6g}; confirm these are the operands you used"}
    return {"status": "undeclared", "match": None,
            "how": "no declared value at this precision and no declared combination of two declared "
                   "values within the relative tolerance"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md", action="append", required=True)
    parser.add_argument("--data", action="append", required=True,
                        help="a file or directory of supplied data")
    parser.add_argument("--out", default="number-scan.json")
    parser.add_argument("--rel-tolerance", type=float, default=0.001,
                        help="relative tolerance for a two-value derived match (default 0.1%%)")
    parser.add_argument("--skip", action="append", default=[],
                        help="a literal number to ignore, e.g. a section number")
    args = parser.parse_args()

    pool, files = declared_values([Path(p) for p in args.data])
    outlines = []
    for literal in args.skip:
        value = to_float(literal)
        if value is not None:
            pool.append({"value": value, "source": "declared skip list", "locator": literal})

    findings = []
    counts = {"declared": 0, "declared_derived": 0, "undeclared": 0}
    for md in args.md:
        path = Path(md)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for sentence in CONTEXT.findall(text):
            stripped = sentence.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for match in NUMBER.finditer(stripped):
                value = to_float(match.group(1))
                if value is None:
                    continue
                verdict = classify(value, match.group(1), pool, args.rel_tolerance)
                counts[verdict["status"]] += 1
                findings.append({
                    "file": path.as_posix(),
                    "number": match.group(1),
                    "unit": match.group(3) or "",
                    "value": value,
                    "sentence": stripped[:280],
                    **verdict,
                })

    report = {
        "schema": "number-scan/v1",
        "markdown_files": [Path(p).as_posix() for p in args.md],
        "data_files_read": files,
        "declared_value_count": len(pool),
        "relative_tolerance": args.rel_tolerance,
        "counts": counts,
        "undeclared": [f for f in findings if f["status"] == "undeclared"],
        "all_findings": findings,
        "limitations": [
            "A number that matches a declared value by coincidence is reported as declared; this "
            "check cannot know which source value the author meant.",
            "Derived values are matched against differences, sums, products and two ratio forms of "
            "two declared values only; a three-term calculation is reported as undeclared.",
            "Section numbers, years, page numbers and figure numbers in the prose are not exempt: "
            "list them with --skip if they are intentional.",
        ],
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({k: report[k] for k in
                      ("markdown_files", "data_files_read", "declared_value_count", "counts")},
                     ensure_ascii=False, indent=2))
    derived = [f for f in findings if f["status"] == "declared_derived"]
    if derived:
        # A sum or difference of two table values can hit any target by arithmetic coincidence, so
        # these are reported for confirmation rather than counted as traced.
        print(f"\n{len(derived)} number(s) matched a two-value calculation - confirm the operands "
              f"are the ones you meant:")
        for item in derived[:20]:
            left = item["match"]["left"]
            right = item["match"]["right"]
            print(f"  {item['number']}{item['unit']} = {item['how'].split('(')[1].split(')')[0]}"
                  f"  [{left['source']} {left['locator']} | {right['source']} {right['locator']}]")
    if report["undeclared"]:
        print(f"\n{len(report['undeclared'])} number(s) with NO declared source:")
        for item in report["undeclared"][:20]:
            print(f"  {item['file']}  {item['number']}{item['unit']}  "
                  f"in: {item['sentence'][:110]}")
        print("\nRepair: either declare the value in the supplied data, replace it with the declared "
              "value, or delete the claim. Never adjust the data to match the prose.")
    else:
        print("\nevery number either is a declared value or matches a declared calculation")
    print(f"\n-> {args.out}")
    return 0 if not report["undeclared"] else 2


if __name__ == "__main__":
    sys.exit(main())
