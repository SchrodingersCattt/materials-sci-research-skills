"""Self-test for the reading-contract runtime.

Positive path: the contract lists every requested field and question, and a compliant answer passes
every check. Negative paths: a missing field, an off-vocabulary status, a value attached to a
'not_reported' field, a quotation that is not in the source, a value whose digits are absent from its
quote, and a claim without evidence must each fail.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent
TOOL = CANDIDATE / "scripts" / "reading_contract.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def failed_ids(outdir: Path) -> list:
    report = json.loads((outdir / "reading-check.json").read_text(encoding="utf-8"))
    return [entry["id"] for entry in report["checks"] if entry["status"] == "fail"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    work = Path(args.workdir)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    fixture = work / "fixture"

    failures: list[str] = []
    if run([str(FIXTURE), "--outdir", str(fixture)]).returncode != 0:
        print("fixture build failed")
        return 1
    case = fixture / "case.json"

    contract_path = work / "contract.json"
    built = run([str(TOOL), "contract", "--case", str(case), "--out", str(contract_path)])
    if built.returncode != 0:
        failures.append(f"contract build failed: {built.stderr[:300]}")
    else:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if contract["requested_field_count"] != 5 or contract["requested_question_count"] != 2:
            failures.append(f"the contract did not list every requested item: {contract}")

    good = run([str(TOOL), "check", "--answer", str(fixture / "answer-good.json"),
                "--case", str(case), "--outdir", str(work / "good")])
    if good.returncode != 0:
        failures.append(f"the compliant answer failed: {failed_ids(work / 'good')}")

    verified = run([str(TOOL), "verify", "--answer", str(fixture / "answer-good.json"),
                    "--outdir", str(work / "good")])
    if verified.returncode != 0:
        failures.append(f"verification of the compliant answer failed: {verified.stdout}")

    bad = run([str(TOOL), "check", "--answer", str(fixture / "answer-bad.json"),
               "--case", str(case), "--outdir", str(work / "bad")])
    bad_ids = failed_ids(work / "bad")
    if bad.returncode == 0:
        failures.append("the defective answer was not rejected")
    for expected in ("field_coverage", "status_vocabulary", "no_value_for_unreported",
                     "reported_fields_have_evidence", "quotes_are_verbatim",
                     "values_come_from_the_quote", "question_coverage", "claims_have_evidence"):
        if expected not in bad_ids:
            failures.append(f"the checker did not catch '{expected}': caught={bad_ids}")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": len(json.loads((work / "good" / "reading-check.json")
                                 .read_text(encoding="utf-8"))["checks"]),
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
