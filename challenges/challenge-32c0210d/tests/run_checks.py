"""Self-test for the results/discussion delivery candidate.

Positive path : synthetic data + two sections + a quantity plan, built to DOCX and verified.
Negative paths: a wrong number in the prose, a wrong unit, a reworded quote, a tampered source
and an undeclared number must each make the audit fail rather than pass.
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
AUDIT = CANDIDATE / "scripts" / "quantity_audit.py"
DELIVER = CANDIDATE / "scripts" / "deliver.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8")


def audit_status(plan: Path, outdir: Path) -> tuple:
    proc = run([str(AUDIT), "--plan", str(plan), "--outdir", str(outdir)])
    report = json.loads((outdir / "quantity-report.json").read_text(encoding="utf-8"))
    failed = [c["check"] for c in report["checks"] if not c["passed"]]
    return report["status"], failed, proc.returncode


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

    # --- positive path -------------------------------------------------------
    status, failed, code = audit_status(fixture / "plan.json", work / "audit-ok")
    if status != "structural_quantity_checks_passed" or code != 0:
        failures.append(f"positive audit did not pass: {status} failed={failed}")

    docx = work / "out" / "deliverable.docx"
    build = run([str(DELIVER), "build-docx", "--md", str(fixture / "results.md"),
                 "--md", str(fixture / "discussion.md"), "--out", str(docx)])
    if build.returncode != 0:
        failures.append(f"docx build failed: {build.stdout} {build.stderr[:200]}")
    else:
        verify = run([str(DELIVER), "verify", "--out-file", str(docx),
                      "--md", str(fixture / "results.md"), "--md", str(fixture / "discussion.md"),
                      "--outdir", str(work / "out")])
        if verify.returncode != 0:
            failures.append(f"docx verify failed: {verify.stdout}")

    # --- negative paths ------------------------------------------------------
    plan = json.loads((fixture / "plan.json").read_text(encoding="utf-8"))

    def mutate(name: str, change) -> tuple:
        directory = work / f"neg-{name}"
        directory.mkdir(parents=True, exist_ok=True)
        for item in ("data.csv", "results.md", "discussion.md"):
            shutil.copy(fixture / item, directory / item)
        (directory / "artifacts").mkdir(exist_ok=True)
        shutil.copy(fixture / "artifacts" / "fig1.png", directory / "artifacts" / "fig1.png")
        altered = json.loads(json.dumps(plan))
        change(altered, directory)
        plan_path = directory / "plan.json"
        plan_path.write_text(json.dumps(altered, ensure_ascii=False, indent=2), encoding="utf-8")
        return audit_status(plan_path, work / f"neg-out-{name}")

    def wrong_value(altered, directory):
        text = (directory / "results.md").read_text(encoding="utf-8")
        (directory / "results.md").write_text(text.replace("31.2 MPa", "32.1 MPa"), encoding="utf-8")

    def wrong_unit(altered, directory):
        for claim in altered["claims"]:
            if claim["id"] == "c1":
                claim["quote"] = claim["quote"].replace("31.2 MPa", "31.2 kPa")

    def reworded_quote(altered, directory):
        for claim in altered["claims"]:
            if claim["id"] == "c2":
                claim["quote"] = "Both groups contain seven synthetic specimens."

    def tampered_source(altered, directory):
        (directory / "data.csv").write_text(
            (directory / "data.csv").read_text(encoding="utf-8").replace("31.2", "31.9"),
            encoding="utf-8")

    def undeclared_number(altered, directory):
        text = (directory / "results.md").read_text(encoding="utf-8")
        (directory / "results.md").write_text(
            text.replace("Both groups contain six synthetic specimens.",
                         "Both groups contain six synthetic specimens and 99 outliers."),
            encoding="utf-8")

    for name, change in (("wrong-value", wrong_value), ("wrong-unit", wrong_unit),
                         ("reworded-quote", reworded_quote), ("tampered-source", tampered_source),
                         ("undeclared-number", undeclared_number)):
        status, failed, code = mutate(name, change)
        if status == "structural_quantity_checks_passed" or code == 0:
            failures.append(f"negative case '{name}' was not rejected (status={status})")
        elif name == "reworded-quote" and failed == []:
            failures.append(f"negative case '{name}' produced no failing check")

    print(json.dumps({
        "fixture": str(fixture),
        "positive_checks": len(json.loads((work / "audit-ok" / "quantity-report.json")
                                          .read_text(encoding="utf-8"))["checks"]),
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
