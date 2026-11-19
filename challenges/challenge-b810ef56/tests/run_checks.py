"""Self-test for the evidence-ledger skill.

Builds the synthetic manuscript/source pack and asserts the contract: every planted problem is
detected (causal upgrade, consensus on a single small study, absolute wording against a hedged
source, phantom citation, unused reference, duplicate DOI), the ledger is reproducible, and the
verification re-reads the named files and matches their hashes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent
SCRIPT = CANDIDATE / "scripts" / "evidence_ledger.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    fixture = work / "fixture"

    failures: list[str] = []
    if run([str(FIXTURE), "--outdir", str(fixture)]).returncode != 0:
        print("fixture build failed")
        return 1

    doc = fixture / "manuscript.docx"
    sources = fixture / "sources"
    ledger = work / "ledger.json"
    audit = work / "audit.json"
    verify = work / "verify.json"
    report = work / "report"

    for label, argv in (
        ("extract", ["extract", "--doc", str(doc), "--sources", str(sources), "--out", str(ledger)]),
        ("audit", ["audit", "--ledger", str(ledger), "--out", str(audit)]),
        ("report", ["report", "--ledger", str(ledger), "--out", str(report)]),
        ("verify", ["verify", "--ledger", str(ledger), "--sources", str(sources), "--out", str(verify)]),
    ):
        proc = run([str(SCRIPT), *argv])
        if proc.returncode != 0:
            failures.append(f"{label} exited {proc.returncode}: {proc.stdout.strip()} "
                            f"{proc.stderr.strip()[:300]}")

    if not failures:
        ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
        audit_data = json.loads(audit.read_text(encoding="utf-8"))
        verify_data = json.loads(verify.read_text(encoding="utf-8"))

        verdicts = {c["claim_id"]: c["judgement"]["verdict"] for c in ledger_data["claims"]}
        verdict_values = list(verdicts.values())
        if verdict_values.count("claim_stronger_than_source") < 3:
            failures.append(f"expected at least 3 strength upgrades, got {verdicts}")
        if "supported" not in verdict_values:
            failures.append(f"the supported fixture claim was not recognised: {verdicts}")
        for claim in ledger_data["claims"]:
            if not claim["judgement"]["reasons"]:
                failures.append(f"claim {claim['claim_id']} has no reason")
            if not claim["judgement"].get("suggestion"):
                failures.append(f"claim {claim['claim_id']} has no suggestion")
            if not claim["locator"]:
                failures.append(f"claim {claim['claim_id']} has no locator")

        kinds = {f["kind"] for f in audit_data["findings"]}
        for expected in ("citation_without_entry", "reference_never_cited", "duplicate_reference"):
            if expected not in kinds:
                failures.append(f"audit missed {expected}: {sorted(kinds)}")

        if verify_data["failed"]:
            failures.append(f"verification failures: "
                            f"{[c['id'] for c in verify_data['checks'] if c['status'] == 'fail']}")
        if verify_data["status"] != "verified":
            failures.append(f"verification status {verify_data['status']}")

        # Determinism: a second extraction must produce the same verdicts and claim ids.
        second = work / "ledger2.json"
        if run([str(SCRIPT), "extract", "--doc", str(doc), "--sources", str(sources),
                "--out", str(second)]).returncode == 0:
            again = json.loads(second.read_text(encoding="utf-8"))
            if [c["claim_id"] for c in again["claims"]] != [c["claim_id"] for c in ledger_data["claims"]] \
                    or again["verdict_summary"] != ledger_data["verdict_summary"]:
                failures.append("ledger is not reproducible across runs")
        else:
            failures.append("second extraction failed")
        if not (report / "EVIDENCE_LEDGER.md").exists():
            failures.append("human-readable ledger was not written")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": (verify_data.get("passed", 0) + verify_data.get("failed", 0)) if not failures else None,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
