"""Self-test for the structural diagnosis skill.

Builds the synthetic manuscript, runs outline/claims/diagnose/plan/apply/verify, and asserts
the contract: findings are located, the plan is executable, the applied deletions remove only
the duplicated paragraph, and every other sentence survives.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent
SCRIPT = CANDIDATE / "scripts" / "structure_audit.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_manuscript.py"

EXPECTED_KINDS = {
    "heading_level_anomaly",
    "missing_objective",
    "causal_without_support",
    "interpretation_in_results",
    "absolute_wording",
    "duplicate_paragraph",
    "result_restated_without_pointer",
    "unsourced_quantity",
}


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    fixture = work / "fixture"
    out = work / "out"

    failures: list[str] = []
    if run([str(FIXTURE), "--outdir", str(fixture)]).returncode != 0:
        print("fixture build failed")
        return 1

    doc = fixture / "manuscript.docx"
    outline, claims, findings, plan = (work / n for n in
                                       ("outline.json", "claims.json", "findings.json", "plan.json"))
    for label, argv in (
        ("outline", ["outline", "--doc", str(doc), "--out", str(outline)]),
        ("claims", ["claims", "--doc", str(doc), "--out", str(claims)]),
        ("diagnose", ["diagnose", "--doc", str(doc), "--out", str(findings)]),
        ("plan", ["plan", "--doc", str(doc), "--out", str(plan)]),
        ("apply", ["apply", "--doc", str(doc), "--plan", str(plan), "--outdir", str(out)]),
        ("verify", ["verify", "--doc", str(doc), "--output", str(out / "restructured.docx"),
                    "--outdir", str(out)]),
    ):
        proc = run([str(SCRIPT), *argv])
        if proc.returncode not in (0,):
            failures.append(f"{label} exited {proc.returncode}: {proc.stdout.strip()} "
                            f"{proc.stderr.strip()[:300]}")

    if not failures:
        findings_data = json.loads(findings.read_text(encoding="utf-8"))
        plan_data = json.loads(plan.read_text(encoding="utf-8"))
        apply_report = json.loads((out / "apply-report.json").read_text(encoding="utf-8"))
        verification = json.loads((out / "verification.json").read_text(encoding="utf-8"))

        kinds = {f["kind"] for f in findings_data["findings"]}
        missing = EXPECTED_KINDS - kinds
        if missing:
            failures.append(f"fixture rules did not fire: {sorted(missing)}")
        for finding in findings_data["findings"]:
            if not finding.get("locator") or not finding.get("suggested_action"):
                failures.append(f"finding without locator/action: {finding['id']}")
            if finding.get("dimension") not in (
                    "研究问题与贡献主张对齐", "章节结构与叙事顺序", "论证链与论据对应",
                    "段落关系与重复内容", "结论边界与表述尺度"):
                failures.append(f"finding with unknown dimension: {finding['id']}")
        if plan_data["executable_count"] != 1:
            failures.append(f"expected exactly 1 executable action, got {plan_data['executable_count']}")
        if apply_report.get("removed_paragraphs") != 1:
            failures.append(f"expected 1 removed paragraph, got {apply_report.get('removed_paragraphs')}")
        if verification.get("failed"):
            failures.append(f"verification failures: "
                            f"{[c['id'] for c in verification['checks'] if c['status'] == 'fail']}")
        if verification.get("status") != "verified":
            failures.append(f"verification status {verification.get('status')}")

        # A second run must be idempotent: the duplicate is gone, so no executable action remains.
        second = run([str(SCRIPT), "plan", "--doc", str(out / "restructured.docx"),
                      "--out", str(work / "plan2.json")])
        if second.returncode != 0:
            failures.append("second plan run failed")
        else:
            plan2 = json.loads((work / "plan2.json").read_text(encoding="utf-8"))
            if plan2["executable_count"] != 0:
                failures.append(f"plan is not idempotent: {plan2['executable_count']} actions remain")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": (verification.get("passed", 0) + verification.get("failed", 0)) if not failures else None,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
