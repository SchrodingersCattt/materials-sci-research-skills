"""Controls for the benchmark scorer: an anchor must be earned by an answer, not by the answer's shape.

Anchors are matched by normalised substring. Matching against the serialised JSON document - the
older behaviour - means a needle that only ever appears as a **key** or as part of the envelope is
counted as present, so a case can be scored without the answer saying anything. This test plants that
defect: one anchor whose needle appears only as a key, and one anchor that is genuinely answered.

    python tests/bench_score_checks.py [--engine PATH] [--workdir DIR]

Point --engine at a copy of an older scorer to see the same fixture fail, which is what makes this a
control rather than an assertion.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "benchmark_build.py"

# A needle that never occurs in an answer's text, only as an object key: the defect this guards.
KEY_ONLY_NEEDLE = "keyonlyneedle-9f2c"
VALUE_NEEDLE = "the control specimen reached 286 MPa at room temperature"


def build_spec(work: Path) -> dict:
    material = work / "material" / "paper.md"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_text("# paper\n\n" + VALUE_NEEDLE + "\n", encoding="utf-8")
    cases = []
    for index, (case_id, points) in enumerate((("C1", 10), ("C2", 10)), start=1):
        cases.append({
            "id": case_id,
            "kind": "reading",
            "title": f"case {index}",
            "instruction": "answer the anchor from the supplied material",
            "max_points": points + 10,
            "material": [{"path": "material/paper.md", "locator": "body paragraph 1"}],
            "expected": {"answer": "an object with one entry per requested item"},
            "anchors": [
                {"id": f"{case_id}-A1", "kind": "required", "points": points,
                 "text": KEY_ONLY_NEEDLE, "match_any": [KEY_ONLY_NEEDLE]},
                {"id": f"{case_id}-A2", "kind": "required", "points": 10,
                 "text": VALUE_NEEDLE, "match_any": [VALUE_NEEDLE]},
            ],
        })
    return {"id": "bench-fixture", "version": "v1", "min_cases": len(cases),
            "cases": cases, "material": [], "material_version": "v3"}


def answers_payload() -> dict:
    """The needle is a key inside each per-case answer, never a value.

    Serialising the answer object and matching against that text - the older behaviour - finds it.
    Matching inside the values does not, which is the point: the case must not be scored by the shape
    of the answer object. The real answer sits in a value and must score either way.
    """
    return {
        "case_id": "bench-fixture",
        "answers": {
            "C1": {KEY_ONLY_NEEDLE: "x", "item": VALUE_NEEDLE},
            "C2": {KEY_ONLY_NEEDLE: "x", "item": VALUE_NEEDLE},
        },
    }


def run(engine: Path, args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(engine), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(cwd))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default=str(ENGINE))
    parser.add_argument("--workdir", default=str(ROOT / "work" / "bench-checks"))
    args = parser.parse_args()
    engine = Path(args.engine).resolve()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    spec_path = work / "benchmark-spec.json"
    spec_path.write_text(json.dumps(build_spec(work), ensure_ascii=False, indent=1), encoding="utf-8")
    answers_path = work / "answers.json"
    answers_path.write_text(json.dumps(answers_payload(), ensure_ascii=False, indent=1),
                            encoding="utf-8")

    failures: list[str] = []
    checks: list[dict] = []

    def record(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"id": check_id, "result": "pass" if ok else "fail", "detail": detail})
        if not ok:
            failures.append(f"{check_id}: {detail}")

    validation = run(engine, ["validate", "--spec", str(spec_path), "--outdir", str(work / "validate")],
                     work)
    validation_report = json.loads((work / "validate" / "benchmark-report.json").read_text(
        encoding="utf-8")) if (work / "validate" / "benchmark-report.json").exists() else {}
    record("fixture.is_valid", validation.returncode == 0 and not validation_report.get("problems"),
           f"rc={validation.returncode} problems={validation_report.get('problems')}")
    record("fixture.min_cases_counts_cases", validation.returncode == 0,
           "two cases of the same kind satisfy min_cases=2 (it counts cases, not kinds)")

    scoring = run(engine, ["score", "--spec", str(spec_path), "--answers", str(answers_path),
                           "--outdir", str(work / "score")], work)
    report_path = work / "score" / "scoring-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    matched = {row["anchor"] for case in report.get("results", []) for row in case.get("detail", [])
               if row.get("matched")}
    missed = {row["anchor"] for case in report.get("results", [])
              for row in case.get("detail", []) if not row.get("matched")}
    record("scorer.runs", scoring.returncode == 0, f"rc={scoring.returncode} {scoring.stderr[-200:]}")
    record("positive.key_only_needle_not_matched",
           not any(anchor.endswith("-A1") for anchor in matched),
           f"a needle present only as a key was counted as present: matched={sorted(matched)}")
    record("positive.key_only_needle_reported_missing",
           all(f"C{index}-A1" in missed for index in (1, 2)),
           f"both key-only anchors must be reported missing: missed={sorted(missed)}")
    record("negative.value_needle_matched",
           all(f"C{index}-A2" in matched for index in (1, 2)),
           f"a needle inside an answer value must score: matched={sorted(matched)}")

    broken = build_spec(work)
    del broken["cases"][0]["material"]
    broken_path = work / "benchmark-broken.json"
    broken_path.write_text(json.dumps(broken, ensure_ascii=False, indent=1), encoding="utf-8")
    broken_run = run(engine, ["score", "--spec", str(broken_path), "--answers", str(answers_path),
                              "--outdir", str(work / "broken")], work)
    record("positive.invalid_benchmark_refused",
           broken_run.returncode != 0 and not (work / "broken" / "scoring-report.json").exists(),
           f"rc={broken_run.returncode}; an invalid benchmark must not produce a score")

    payload = {"verdict": "pass" if not failures else "fail", "engine": str(engine),
               "checks": checks, "failures": failures}
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
