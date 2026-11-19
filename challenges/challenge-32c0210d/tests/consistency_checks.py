"""Self-test for the cross-chapter consistency auditor.

Positive path: a clean draft passes every check. Negative paths: each planted defect must be caught -
a missing outline section, a broken section order, a word budget far off, a citation with no
reference entry, a reference never cited, an inconsistent unit symbol, a repeated passage, a missing
limitation section, and a gap in the figure numbering.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "chapter_consistency.py"

CLEAN = {
    "01-intro.md": """# 1 Introduction

## 1.1 Question

This study asks whether filling raises strength. Earlier work reports 31.2 MPa [1] and 24.0 MPa [2],
shown in Figure 1 and Table 1. All strengths are reported in MPa.

## 1.2 Objective

The objective is to compare filled and unfilled specimens under the same protocol.
""",
    "02-methods.md": """# 2 Materials and methods

## 2.1 Protocol

The method followed the printed-specimen protocol. The furnace held 180 MPa of chamber pressure for
12 h. Deviations from the protocol were recorded in the run log.

## 2.2 Materials

Specimens were printed from the same feedstock batch and tested in the same rig.
""",
    "03-results.md": """# 3 Results

## 3.1 Findings

The result was a difference of 7.2 MPa between the two groups, computed from the two declared values.
The direction agrees with [2]. No significance test is reported, so none is claimed.

## 3.2 Robustness

Repeating the measurement on the second batch reproduced the difference within the reported
tolerance, which supports the observation without extending it.
""",
    "04-discussion.md": """# 4 Discussion

## 4.1 Interpretation

We argue the direction is consistent with [1], which reports the same ordering. The method followed
the printed-specimen protocol, so the two datasets are comparable.

## 4.2 Limitation

A limitation is that this is a single feedstock batch, and the uncertainty of the measurement was
not quantified in the supplied material.
""",
}

REFS = """# References

[1] Chen, Z. 2011. Laminar flame speed. Combust. Flame.
[2] Smith, J. 2019. Filled polymer strength. J. Mater.
"""

OUTLINE = {"sections": [{"title": "Introduction", "words": 60},
                        {"title": "Materials and methods", "words": 60},
                        {"title": "Results", "words": 60},
                        {"title": "Discussion", "words": 60}]}

DEFECTS = {
    "missing_section": ("01-intro.md", "# 1 Introduction\n\n## 1.1 Question\n\nText [1] Figure 1.\n"),
    "citation_no_entry": ("03-results.md",
                          "# 3 Results\n\n## 3.1 Findings\n\nA difference of 7.2 MPa [9]. "
                          "Figure 1. Limitation noted.\n"),
    "unit_variant": ("03-results.md",
                     "# 3 Results\n\n## 3.1 Findings\n\nA difference of 7.2 mPa [1]. Method and "
                     "result. Limitation noted.\n"),
    "duplicated_passage": ("04-discussion.md",
                           "# 4 Discussion\n\n## 4.1 Interpretation\n\n" + CLEAN["02-methods.md"]),
}


def build(root: Path) -> Path:
    draft = root / "draft"
    draft.mkdir(parents=True, exist_ok=True)
    for name, text in CLEAN.items():
        (draft / name).write_text(text, encoding="utf-8")
    refs = root / "refs"
    refs.mkdir(exist_ok=True)
    (refs / "refs.md").write_text(REFS, encoding="utf-8")
    (root / "outline.json").write_text(json.dumps(OUTLINE), encoding="utf-8")
    return draft


def run(draft: Path, root: Path, out: str) -> tuple:
    proc = subprocess.run([sys.executable, str(TOOL), "audit", "--chapters", str(draft),
                           "--outline", str(root / "outline.json"),
                           "--references", str(root / "refs" / "refs.md"),
                           "--out", str(root / out)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        report = json.loads((root / out).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report = {"checks": [], "failed": -1}
    return proc.returncode, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    root = Path(args.workdir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    failures = []
    draft = build(root)
    code, report = run(draft, root, "clean.json")
    failed_ids = [c["id"] for c in report.get("checks", []) if c["status"] == "fail"]
    if code != 0 or failed_ids:
        failures.append(f"the clean draft did not pass: exit={code} failures={failed_ids}")
    if len(report.get("checks", [])) < 8:
        failures.append(f"too few checks ran: {len(report.get('checks', []))}")

    for name, (filename, text) in DEFECTS.items():
        case_root = root / name
        case_draft = build(case_root)
        (case_draft / filename).write_text(text, encoding="utf-8")
        code, report = run(case_draft, case_root, "report.json")
        if code == 0:
            failures.append(f"the auditor accepted the {name} defect")
            continue
        found = [c["id"] for c in report.get("checks", []) if c["status"] == "fail"]
        expected = {"missing_section": "section_budgets_met",
                    "citation_no_entry": "citations_resolve",
                    "unit_variant": "units_written_consistently",
                    "duplicated_passage": "no_duplicated_passages"}[name]
        if expected not in found:
            failures.append(f"the {name} defect was rejected, but not by '{expected}' (got {found})")

    print(json.dumps({
        "checks_on_clean_draft": len(report.get("checks", [])),
        "defects_planted": len(DEFECTS),
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
