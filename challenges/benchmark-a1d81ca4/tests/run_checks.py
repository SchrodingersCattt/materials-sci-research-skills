"""Self-test for the benchmark builder.

Positive path: the synthetic set validates, the reference answers score the declared maximum, and a
weak answer set is penalised for the anchors it misses and the claims it overstates.

Negative paths: a case missing a required field, a case referencing missing material, anchors that
do not sum to the declared maximum, and a duplicate case id must each make validation fail.
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
TOOL = CANDIDATE / "scripts" / "benchmark_build.py"
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

    spec_path = fixture / "benchmark-spec.json"
    out = work / "out"

    validated = run([str(TOOL), "validate", "--spec", str(spec_path), "--outdir", str(out)])
    report = json.loads((out / "benchmark-report.json").read_text(encoding="utf-8"))
    if validated.returncode != 0:
        failures.append(f"the fixture set did not validate: {report['problems']}")
    if report["case_count"] != 2:
        failures.append(f"expected 2 cases, got {report['case_count']}")

    scored = run([str(TOOL), "score", "--spec", str(spec_path),
                  "--answers", str(fixture / "answers-reference.json"), "--outdir", str(out)])
    scoring = json.loads((out / "scoring-report.json").read_text(encoding="utf-8"))
    if scored.returncode != 0:
        failures.append(f"scoring the reference answers failed: {scored.stderr[:200]}")
    if scoring["normalised_total"] != 1.0:
        failures.append(f"the reference answers did not reach the maximum: "
                        f"{scoring['total']}/{scoring['maximum']}")

    weak = run([str(TOOL), "score", "--spec", str(spec_path),
                "--answers", str(fixture / "answers-weak.json"), "--outdir", str(out / "weak")])
    weak_report = json.loads((out / "weak" / "scoring-report.json").read_text(encoding="utf-8"))
    if weak.returncode != 0:
        failures.append("scoring the weak answers failed")
    if weak_report["normalised_total"] >= scoring["normalised_total"]:
        failures.append("the weak answer set was not scored strictly lower than the reference")
    penalties = sum(1 for result in weak_report["results"] for entry in result.get("detail", [])
                    if entry["kind"] == "penalty" and entry["matched"])
    if penalties < 2:
        failures.append(f"the overstated claims did not trigger both penalties (got {penalties})")

    verified = run([str(TOOL), "verify", "--spec", str(spec_path), "--outdir", str(out)])
    if verified.returncode != 0:
        failures.append(f"verification failed: {verified.stdout} {verified.stderr[:200]}")

    # --- negative paths -------------------------------------------------------
    base = json.loads(spec_path.read_text(encoding="utf-8"))

    def variant(name: str, mutate) -> list:
        spec = json.loads(json.dumps(base))
        mutate(spec)
        path = work / f"{name}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        result = run([str(TOOL), "validate", "--spec", str(path), "--outdir", str(work / f"out-{name}")])
        payload = json.loads((work / f"out-{name}" / "benchmark-report.json").read_text(encoding="utf-8"))
        return payload["problems"]

    problems = variant("missing-field", lambda spec: spec["cases"][0].pop("instruction"))
    if not any("instruction" in problem for problem in problems):
        failures.append(f"a case missing a required field was accepted: {problems}")

    problems = variant("missing-material", lambda spec: spec["cases"][0].update(
        {"material": [{"path": "does-not-exist.md"}]}))
    if not any("missing material" in problem for problem in problems):
        failures.append(f"a case with unresolvable material was accepted: {problems}")

    problems = variant("weight-mismatch", lambda spec: spec["cases"][0].update({"max_points": 99}))
    if not any("anchors sum" in problem for problem in problems):
        failures.append(f"a weight/max mismatch was accepted: {problems}")

    problems = variant("duplicate-id", lambda spec: spec["cases"][1].update(
        {"id": spec["cases"][0]["id"]}))
    if not any("duplicate case ids" in problem for problem in problems):
        failures.append(f"a duplicate case id was accepted: {problems}")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": len(report["cases"]) + 5,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
