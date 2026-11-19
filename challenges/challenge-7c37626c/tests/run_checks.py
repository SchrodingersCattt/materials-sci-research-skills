"""Self-test for the exact formula checker.

Positive path: three steps that must evaluate exactly (a rational momentum balance, a decimal
volume inside its stated range, and a rate whose denominator is a non-zero difference). Negative
paths: a zero denominator, a domain violation, an undeclared variable and a wrong expected value
must each be reported rather than silently evaluated.
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
CHECKER = CANDIDATE / "scripts" / "formula_check.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


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

    base = json.loads((fixture / "formula-spec.json").read_text(encoding="utf-8"))
    steps = {step["id"]: step for step in base["steps"]}

    # --- positive path: a spec whose steps all evaluate ------------------------
    good = json.loads(json.dumps(base))
    good["steps"] = [steps["f1"], steps["f2"]]
    # f3 is the zero-denominator case: make it well-defined for the positive run
    rate = json.loads(json.dumps(steps["f3"]))
    rate["variables"]["t1"] = {"value": "30", "source_locator": "fixture row 6"}
    rate["expect"] = "1.5"
    good["steps"].append(rate)
    good_spec = work / "good-spec.json"
    good_spec.write_text(json.dumps(good, ensure_ascii=False, indent=2), encoding="utf-8")

    out = work / "out"
    result = run([str(CHECKER), "check", "--spec", str(good_spec), "--outdir", str(out)])
    report = json.loads((out / "formula-report.json").read_text(encoding="utf-8"))
    if result.returncode != 0:
        failures.append(f"positive check did not pass: {report['failing_steps']} "
                        f"{result.stdout} {result.stderr[:200]}")
    by_id = {entry["id"]: entry for entry in report["steps"]}
    # (2 x 3.5 + 1 x -1.5) / (2 + 1) = 5.5 / 3 = 11/6 exactly
    if by_id["f1"].get("exact") != "11/6":
        failures.append(f"the rational momentum balance is not exact: {by_id['f1'].get('exact')}")
    if by_id["f1"].get("display") != "1.8333":
        failures.append(f"the declared display rounding is wrong: {by_id['f1'].get('display')}")
    if by_id["f2"].get("declared_range") is None:
        failures.append("the stated range was not carried through")
    if any(entry.get("declared_range") for entry in report["steps"] if entry["id"] == "f1"):
        failures.append("a range was attached to a quantity that declares none")
    if by_id["f3"].get("matches_expected") is not True:
        failures.append(f"the expected-value comparison failed: {by_id['f3']}")

    verified = run([str(CHECKER), "verify", "--spec", str(good_spec), "--outdir", str(out)])
    if verified.returncode != 0:
        failures.append(f"verification failed: {verified.stdout} {verified.stderr[:200]}")

    # --- negative paths -------------------------------------------------------
    def variant(name: str, mutate) -> dict:
        spec = json.loads(json.dumps(base))
        mutate(spec)
        path = work / f"{name}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        run([str(CHECKER), "check", "--spec", str(path), "--outdir", str(work / f"out-{name}")])
        return json.loads((work / f"out-{name}" / "formula-report.json").read_text(encoding="utf-8"))

    zero_report = variant("zero-denominator", lambda spec: None)
    zero_entry = next(entry for entry in zero_report["steps"] if entry["id"] == "f3")
    if zero_entry["status"] != "unresolved_denominator":
        failures.append(f"a zero denominator was not refused: {zero_entry}")

    domain_report = variant("domain-violation", lambda spec: spec["steps"][0]["domains"].update(
        {"m1": "> 5"}))
    domain_entry = next(entry for entry in domain_report["steps"] if entry["id"] == "f1")
    if domain_entry["status"] != "domain_violation":
        failures.append(f"a domain violation was not reported: {domain_entry}")

    undefined_report = variant("undefined-variable", lambda spec: None)
    undefined_entry = next(entry for entry in undefined_report["steps"] if entry["id"] == "f4")
    if undefined_entry["status"] != "error" or not any("undeclared" in problem
                                                       for problem in undefined_entry["problems"]):
        failures.append(f"an unreported variable was not refused: {undefined_entry}")

    wrong_report = variant("wrong-expected", lambda spec: spec["steps"][0].update(
        {"expect": "1.2499"}))
    wrong_entry = next(entry for entry in wrong_report["steps"] if entry["id"] == "f1")
    if wrong_entry["status"] != "mismatch":
        failures.append(f"a wrong expected value was not caught: {wrong_entry}")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": 4 + len(report["steps"]),
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
