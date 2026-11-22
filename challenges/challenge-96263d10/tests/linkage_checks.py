"""Self-test for the caption / cross-reference / reference-list apparatus audit.

Two controls, on a manuscript the size of a real one (about forty paragraphs, three figures,
two tables, an equation and a twelve-entry reference list):

  true positive   the defective variant must be reported as ``needs_work`` and the planted
                  defects must be named by kind and by locator
  true negative   the clean variant must be reported as ``consistent`` with no defect and no
                  observation, and its caption inventory must match what was planted

The linked renumber is checked the same way: after it runs, no caption may still be out of
sequence and no in-text reference that pointed at an existing caption may be left dangling.

Every value here is invented for interface testing. Nothing in this file is a formal case
result, an official answer or a score.
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
FIXTURE = CANDIDATE / "examples" / "linkage_case.py"

PLANTED_DEFECTS = {"caption_number_out_of_sequence", "cross_reference_dangling",
                   "reference_entry_duplicated", "reference_numbering_not_monotonic"}


def run(args: list) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    fixture = work / "fixture"
    failures: list[str] = []

    proc = run([str(FIXTURE), "--outdir", str(fixture)])
    if proc.returncode != 0:
        print("fixture build failed:", proc.stdout, proc.stderr)
        return 1

    defective = fixture / "manuscript-defective.docx"
    clean = fixture / "manuscript-clean.docx"
    defective_out = work / "audit-defective"
    clean_out = work / "audit-clean"

    # ---- true positive: the planted defects are found -------------------------------------
    proc = run([str(SCRIPT), "linkage", "--source", str(defective), "--outdir", str(defective_out)])
    bad_report = defective_out / "linkage-report.json"
    if not bad_report.exists():
        print("no linkage report for the defective manuscript:", proc.stdout, proc.stderr)
        return 1
    report = read(bad_report)
    if report.get("status") != "needs_work":
        failures.append(f"defective manuscript reported as {report.get('status')!r}, not needs_work")
    kinds = {defect["kind"] for defect in report.get("defects") or []}
    missing_kinds = PLANTED_DEFECTS - kinds
    if missing_kinds:
        failures.append(f"planted defects not reported: {sorted(missing_kinds)} (reported {sorted(kinds)})")
    if (report.get("caption_families") or {}) != {"figure": 3, "table": 2, "equation": 1}:
        failures.append(f"caption inventory wrong: {report.get('caption_families')}")
    if not all(defect.get("locator") for defect in report.get("defects") or []):
        failures.append("a reported defect carries no locator")
    for defect in report.get("defects") or []:
        if defect["kind"] != "caption_number_out_of_sequence":
            continue
        named = [label for label in ("Figure 2", "Figure 3", "Figure 5")
                 if label in defect["detail"]]
        if not named:
            failures.append(f"out-of-sequence caption not named precisely: {defect['detail']}")

    # ---- true negative: the clean variant is not flagged ----------------------------------
    proc = run([str(SCRIPT), "linkage", "--source", str(clean), "--outdir", str(clean_out)])
    clean_report_path = clean_out / "linkage-report.json"
    if not clean_report_path.exists():
        print("no linkage report for the clean manuscript:", proc.stdout, proc.stderr)
        return 1
    clean_report = read(clean_report_path)
    if clean_report.get("status") != "consistent":
        failures.append(f"clean manuscript reported as {clean_report.get('status')!r} "
                        f"with defects {[d['kind'] for d in clean_report.get('defects') or []]}")
    if clean_report.get("observations"):
        failures.append(f"clean manuscript produced observations: "
                        f"{[o['kind'] for o in clean_report['observations']]}")
    if (clean_report.get("counts") or {}).get("cross_references_dangling"):
        failures.append("clean manuscript reported dangling cross-references")
    if (clean_report.get("reference_list") or {}).get("entry_count") != 12:
        failures.append(f"reference list entry count wrong: "
                        f"{(clean_report.get('reference_list') or {}).get('entry_count')}")
    if (clean_report.get("counts") or {}).get("captions") != 6:
        failures.append(f"clean caption count wrong: {(clean_report.get('counts') or {}).get('captions')}")
    if proc.returncode != 0:
        failures.append(f"linkage exited {proc.returncode} on a consistent manuscript")

    # ---- the linked renumber fixes what can be fixed --------------------------------------
    renumbered_out = work / "renumber"
    proc = run([str(SCRIPT), "linkage", "--source", str(defective), "--output", str(defective),
                "--outdir", str(renumbered_out), "--renumber"])
    renumber_report_path = renumbered_out / "linkage-report.json"
    if not renumber_report_path.exists():
        failures.append(f"no renumber report: {proc.stdout} {proc.stderr}")
    else:
        renumber = read(renumber_report_path)
        result = renumber.get("renumbered") or {}
        destination = Path(result.get("path") or "")
        if not destination.exists():
            failures.append(f"renumber wrote no document (status {renumber.get('status')!r})")
        else:
            post_out = work / "audit-renumbered"
            audit_after = run([str(SCRIPT), "linkage", "--source", str(destination),
                               "--outdir", str(post_out)])
            post = read(post_out / "linkage-report.json")
            out_of_sequence = [record for record in post.get("captions") or []
                               if record.get("number_consistent") is False]
            if out_of_sequence:
                failures.append(f"renumber left captions out of sequence: "
                                f"{[r['declared_number'] for r in out_of_sequence]}")
            if (post.get("reference_list") or {}).get("entry_count") != 12:
                failures.append("renumber changed the reference list")
            if (post.get("counts") or {}).get("captions") != 6:
                failures.append("renumber lost a caption")
            resolvable = {entry["number"] for entry in (renumber.get("cross_references") or [])
                          if entry["status"] == "resolved"}
            new_dangling = [entry for entry in (post.get("cross_references") or [])
                            if entry["status"] == "dangling"
                            and entry["number"] in resolvable]
            if new_dangling:
                failures.append(f"renumber orphaned a reference that used to resolve: "
                                f"{[(e['family'], e['number']) for e in new_dangling]}")
            if len(post.get("defects") or []) >= len(renumber.get("defects") or []):
                failures.append("renumber removed no defect")
            if not (result.get("cross_reference_edits") or []):
                failures.append("renumber did not follow the caption change into the in-text "
                                f"references (mapping {result.get('mapping')})")
            if audit_after.returncode not in (0, 3):
                failures.append(f"audit of the renumbered document exited {audit_after.returncode}")

    # ---- the same audit must work on the shipped synthetic fixture ------------------------
    synthetic = work / "synthetic"
    proc = run([str(CANDIDATE / "examples" / "synthetic_case.py"), "--outdir", str(synthetic)])
    if proc.returncode != 0:
        failures.append(f"synthetic fixture build failed: {proc.stderr[:200]}")
    else:
        proc = run([str(SCRIPT), "linkage", "--source", str(synthetic / "manuscript.docx"),
                    "--outdir", str(work / "audit-synthetic")])
        if proc.returncode != 0:
            failures.append(f"linkage exited {proc.returncode} on the shipped synthetic fixture: "
                            f"{proc.stdout.strip()[:300]}")

    # ---- a mapping target must exist in the output package even when style names collide ----
    # The synthetic template names its caption style 'Caption' under id 'FigureCaption'; the
    # realistic manuscript already has a different style also named 'Caption'. Importing by name
    # alone used to skip the template definition and leave the output with a dangling pStyle, so
    # the template's caption formatting was silently lost.
    synthetic_template = synthetic / "template.docx"
    collide = work / "collide"
    if synthetic_template.exists():
        collide_spec = collide / "spec.json"
        collide.mkdir(parents=True, exist_ok=True)
        proc = run([str(SCRIPT), "specify", "--template", str(synthetic_template),
                    "--source", str(defective), "--out", str(collide_spec)])
        if proc.returncode != 0:
            failures.append(f"specify failed on the name-collision fixture: {proc.stderr[:200]}")
        proc = run([str(SCRIPT), "apply", "--source", str(defective),
                    "--template", str(synthetic_template), "--spec", str(collide_spec),
                    "--outdir", str(collide)])
        apply_report = collide / "apply-report.json"
        if not apply_report.exists():
            failures.append(f"apply failed on the name-collision fixture: {proc.stdout} {proc.stderr}")
        else:
            report_data = read(apply_report)
            imported = {entry["imported_style_id"] for entry in report_data.get("imported_styles") or []}
            if "FigureCaption" not in imported:
                failures.append(f"the mapping target style was not imported: {sorted(imported)}")
            if report_data.get("unmapped_styles"):
                failures.append(f"unmapped styles after apply: {report_data['unmapped_styles']}")
            proc = run([str(SCRIPT), "verify", "--source", str(defective),
                        "--output", str(collide / "adapted.docx"), "--spec", str(collide_spec),
                        "--outdir", str(collide)])
            verification_path = collide / "verification.json"
            if not verification_path.exists():
                failures.append(f"verify wrote no report on the name-collision fixture: "
                                f"{proc.stderr[:200]}")
            else:
                verification = read(verification_path)
                failing = [c["id"] for c in verification["checks"] if c["status"] == "fail"]
                if failing:
                    failures.append(f"verify still fails on the name-collision fixture: {failing}")
                caption_checks = [c for c in verification["checks"]
                                  if c["id"].startswith("style_applied_")]
                if not caption_checks:
                    failures.append("no style-application check was recorded")
                elif not any(c["id"] == "style_applied_Caption" for c in caption_checks):
                    failures.append("the caption style mapping was not checked: "
                                    f"{[c['id'] for c in caption_checks]}")

    print(json.dumps({
        "defective_status": report.get("status") if bad_report.exists() else None,
        "defective_defect_kinds": sorted(kinds),
        "clean_status": clean_report.get("status") if clean_report_path.exists() else None,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
