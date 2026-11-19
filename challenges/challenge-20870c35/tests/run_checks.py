"""Self-test for the template-aware deck editor.

Positive path: fill one slide's placeholders and add one slide from the layout, then prove the
template parts are byte-identical, the declared content is present, and an independent package
validator accepts the result.

Negative paths (each must be refused or reported, not silently accepted):
  * a plan naming a slide that does not exist
  * a plan naming a placeholder the layout does not have
  * body text too long for its own box (the overflow estimate must fire)
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
EDITOR = CANDIDATE / "scripts" / "edit_slides.py"
VALIDATOR = HERE / "validate_package.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


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
    deck = fixture / "template-deck.pptx"
    plan = json.loads((fixture / "merge-plan.json").read_text(encoding="utf-8"))

    out = work / "out"
    merge = run([str(EDITOR), "merge", "--deck", str(deck), "--plan", str(fixture / "merge-plan.json"),
                 "--outdir", str(out)])
    if merge.returncode != 0:
        failures.append(f"merge failed: {merge.stdout} {merge.stderr[:300]}")
    else:
        report = json.loads((out / "merge-report.json").read_text(encoding="utf-8"))
        if not report["template_parts_unchanged"]:
            failures.append("merge changed a master/layout/theme part")
        if report["placeholders_filled"] != 4:
            failures.append(f"expected 4 filled placeholders, got {report['placeholders_filled']}")
        if report["slides_added"] != 1:
            failures.append(f"expected 1 added slide, got {report['slides_added']}")

        validation = run([str(VALIDATOR), str(out / "edited.pptx")])
        if validation.returncode != 0:
            failures.append(f"independent package validation failed: {validation.stdout[-400:]}")

        check = run([str(EDITOR), "check", "--deck", str(deck), "--output", str(out / "edited.pptx"),
                     "--plan", str(fixture / "merge-plan.json"), "--outdir", str(out)])
        if check.returncode != 0:
            failures.append(f"check failed: {check.stdout} {check.stderr[:300]}")

    # --- negative paths -------------------------------------------------------
    def variant(name: str, mutate) -> tuple:
        directory = work / f"neg-{name}"
        directory.mkdir(parents=True, exist_ok=True)
        altered = json.loads(json.dumps(plan))
        mutate(altered)
        plan_path = directory / "plan.json"
        plan_path.write_text(json.dumps(altered, ensure_ascii=False, indent=2), encoding="utf-8")
        merged = run([str(EDITOR), "merge", "--deck", str(deck), "--plan", str(plan_path),
                      "--outdir", str(directory / "out")])
        merged_report = {}
        report_path = directory / "out" / "merge-report.json"
        if report_path.exists():
            merged_report = json.loads(report_path.read_text(encoding="utf-8"))
        checked = run([str(EDITOR), "check", "--deck", str(deck),
                       "--output", str(directory / "out" / "edited.pptx"),
                       "--plan", str(plan_path), "--outdir", str(directory / "out")])
        checked_report = {}
        check_path = directory / "out" / "slide-check.json"
        if check_path.exists():
            checked_report = json.loads(check_path.read_text(encoding="utf-8"))
        return merged, merged_report, checked, checked_report

    def missing_slide(altered):
        altered["slides"][0]["target_slide"] = 99

    def missing_placeholder(altered):
        altered["slides"][0]["notes"] = {"text": "this placeholder does not exist"}

    def overflowing_body(altered):
        altered["slides"][0]["body"] = {"lines": ["x" * 400] * 60}

    merge_result, merge_report, check_result, check_report = variant("missing-slide", missing_slide)
    statuses = [op.get("status") for op in merge_report.get("operations", [])]
    if "missing_target" not in statuses:
        failures.append(f"a plan naming a missing slide was not reported: {statuses}")

    merge_result, merge_report, check_result, check_report = variant("missing-placeholder",
                                                                    missing_placeholder)
    missing = [placeholder for op in merge_report.get("operations", [])
               for placeholder in op.get("missing_placeholders", [])]
    if "notes" not in missing:
        failures.append(f"an absent placeholder was not reported: {missing}")

    merge_result, merge_report, check_result, check_report = variant("overflow", overflowing_body)
    overflow = check_report.get("overflow_estimates") or []
    if check_result.returncode == 0:
        failures.append("an overflowing frame was not reported by the checker")
    if not overflow:
        failures.append("the overflow estimate did not fire for a 60-line body")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": 8,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic deck only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
