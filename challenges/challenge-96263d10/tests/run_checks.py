"""Self-test: run the adaptation pipeline on a synthetic pair and assert the contract.

Every fixture value here is invented for interface testing. Nothing in this file is a
formal case result, an official answer or a score.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent
SCRIPT = CANDIDATE / "scripts" / "adapt_template.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    fixture = work / "fixture"
    out = work / "out"

    failures = []

    proc = run([str(FIXTURE), "--outdir", str(fixture)])
    if proc.returncode != 0:
        print("fixture build failed:", proc.stdout, proc.stderr)
        return 1

    spec = work / "spec.json"
    for label, argv in (
        ("specify", ["specify", "--template", str(fixture / "template.docx"),
                     "--source", str(fixture / "manuscript.docx"), "--out", str(spec)]),
        ("apply", ["apply", "--source", str(fixture / "manuscript.docx"),
                   "--template", str(fixture / "template.docx"), "--spec", str(spec),
                   "--outdir", str(out)]),
        ("verify", ["verify", "--source", str(fixture / "manuscript.docx"),
                    "--output", str(out / "adapted.docx"), "--spec", str(spec),
                    "--outdir", str(out)]),
    ):
        proc = run([str(SCRIPT), *argv])
        if proc.returncode != 0:
            failures.append(f"{label} exited {proc.returncode}: {proc.stdout.strip()} {proc.stderr.strip()[:400]}")

    if not failures:
        spec_data = json.loads(spec.read_text(encoding="utf-8"))
        apply_report = json.loads((out / "apply-report.json").read_text(encoding="utf-8"))
        verification = json.loads((out / "verification.json").read_text(encoding="utf-8"))

        if spec_data["unmapped_source_styles"]:
            failures.append("fixture left source styles unmapped: "
                            + json.dumps(spec_data["unmapped_source_styles"], ensure_ascii=False))
        if not apply_report.get("content_stream_preserved"):
            failures.append("apply did not preserve the manuscript text stream")
        if apply_report.get("unmapped_styles"):
            failures.append(f"unmapped styles after apply: {apply_report['unmapped_styles']}")
        if verification.get("failed"):
            bad = [c["id"] for c in verification["checks"] if c["status"] == "fail"]
            failures.append(f"verification failures: {bad}")
        if verification.get("status") != "verified":
            failures.append(f"verification status {verification.get('status')}")

        # The non-DOCX refusal path must refuse rather than guess.
        refusal = run([str(SCRIPT), "apply", "--source", str(fixture / "manuscript.docx"),
                       "--template", str(spec), "--spec", str(spec), "--outdir", str(work / "refuse")])
        if refusal.returncode != 2:
            failures.append(f"non-DOCX template was not refused (exit {refusal.returncode})")
        else:
            report = json.loads((work / "refuse" / "apply-report.json").read_text(encoding="utf-8"))
            if report.get("applied") or "not DOCX" not in str(report.get("reason")):
                failures.append(f"refusal reason is unclear: {report.get('reason')}")

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
