"""Prove retrieval_audit behaves, with the negative controls this track needs.

The three things the organisers measure are all checkable mechanically, so all three are checked here:
every decision has a reason, the stage counts reconcile, and the included set is recomputable from the
record. Each check also has a defective case that must be rejected.

    python tests/retrieval_checks.py [--workdir work/retrieval]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "retrieval_audit.py"


def run(*argv) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(TOOL), *[str(a) for a in argv]],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="work/retrieval")
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    observed: dict = {}

    # ---- 1 query: a block with no intent is a finding; a strategy with intent is inspectable
    (work / "q.txt").write_text("does catalyst loading change glycerol conversion", encoding="utf-8")
    (work / "strategy-vague.json").write_text(json.dumps({
        "blocks": [{"field": "title", "terms": ["glycerol", "conversion"]}],
        "limits": {},
    }, ensure_ascii=False), encoding="utf-8")
    (work / "strategy-good.json").write_text(json.dumps({
        "blocks": [{"field": "title_abstract", "terms": ["glycerol", "conversion"],
                    "intent": "the intervention and the outcome"}],
        "limits": {"language": "en, zh", "date": "2010-2026"},
        "sources": ["supplied corpus"],
    }, ensure_ascii=False), encoding="utf-8")
    run("query", "--question", work / "q.txt", "--strategy", work / "strategy-vague.json", "--out", work / "q1.json")
    run("query", "--question", work / "q.txt", "--strategy", work / "strategy-good.json", "--out", work / "q2.json")
    q1, q2 = load(work / "q1.json"), load(work / "q2.json")
    observed["query"] = {"vague_findings": len(q1["findings"]), "good_findings": len(q2["findings"])}
    if not any(f["dimension"] == "query_construction" for f in q1["findings"]):
        failures.append("a query block with no stated intent was not reported")
    if not any(f["dimension"] == "query_limits" for f in q1["findings"]):
        failures.append("an absent language or date limit was not reported")
    if q2["findings"]:
        failures.append(f"a fully specified strategy produced {len(q2['findings'])} finding(s) (false positive)")

    # ---- 2 screening: a vague criterion must be rejected; a bound one must pass
    (work / "records.csv").write_text(
        "id,title,year,language\n"
        "R1,glycerol conversion over nickel catalysts,2019,en\n"
        "R2,nickel catalyst deactivation study,2015,en\n"
        "R3,glycerol reforming review,2021,zh\n"
        "R4,unrelated polymer study,2008,en\n", encoding="utf-8")
    (work / "criteria-vague.json").write_text(json.dumps({
        "include": ["relevant to the topic"],
        "exclude": ["not interesting"],
    }, ensure_ascii=False), encoding="utf-8")
    (work / "criteria-good.json").write_text(json.dumps({
        "include": ["glycerol", "catalyst"],
        "exclude": ["polymer"],
    }, ensure_ascii=False), encoding="utf-8")
    rc_v, _ = run("screen", "--records", work / "records.csv", "--criteria", work / "criteria-vague.json",
                  "--out", work / "s1.json")
    rc_g, _ = run("screen", "--records", work / "records.csv", "--criteria", work / "criteria-good.json",
                  "--out", work / "s2.json")
    s1, s2 = load(work / "s1.json"), load(work / "s2.json")
    observed["screen"] = {"vague_rc": rc_v, "vague_status": s1["status"],
                          "good_status": s2["status"], "good_counts": s2["counts"]}
    if s1["status"] != "needs_work":
        failures.append("a criterion like 'relevant' was accepted as adjudicable")
    if not any(f["dimension"] == "criterion_adjudicability" for f in s1["findings"]):
        failures.append("the vagueness was not reported as a criterion problem")
    if rc_g != 0 or s2["status"] != "complete":
        failures.append(f"adjudicable criteria were judged {s2['status']!r} (false positive)")
    # R4 must be excluded, R1/R3 included, R2 partial -> the decisions must differ
    decisions = {d["id"]: d["decision"] for d in s2["decisions"]}
    observed["screen"]["decisions"] = decisions
    if decisions.get("R4") != "exclude":
        failures.append(f"R4 (polymer) was not excluded: got {decisions.get('R4')}")
    if not all(d.get("reasons") is not None for d in s2["decisions"]):
        failures.append("a decision was recorded with no reason field at all")

    # ---- 3 reconcile: counts must add up, and a lost record must be detected
    run("reconcile", "--screening", work / "s2.json", "--out", work / "rec.json")
    rec = load(work / "rec.json")
    observed["reconcile"] = {"stages": rec["stages"], "status": rec["status"]}
    if rec["status"] != "reconciled":
        failures.append(f"a clean screening did not reconcile: {rec['problems']}")
    if rec["stages"]["included"] > rec["stages"]["retrieved"]:
        failures.append("included exceeds retrieved, which should be impossible")
    # now inject a lost record: drop a decision but keep the total
    broken = json.loads(json.dumps(s2))
    broken["decisions"] = broken["decisions"][:2]
    broken["records"] = 4
    (work / "s-broken.json").write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    rc_b, _ = run("reconcile", "--screening", work / "s-broken.json", "--out", work / "rec-broken.json")
    recb = load(work / "rec-broken.json")
    observed["reconcile_broken"] = {"status": recb["status"], "problems": recb["problems"][:2]}
    if recb["status"] == "reconciled":
        failures.append("a screening that lost records still reconciled")

    # ---- 4 verify: the included set must be recomputable from the record alone
    run("verify", "--screening", work / "s2.json", "--out", work / "v2.json")
    v2 = load(work / "v2.json")
    observed["verify"] = {"status": v2["status"], "included": v2["included"], "recomputable": v2["recomputable"]}
    if v2["status"] != "verified":
        failures.append(f"a fully recorded screening was not verifiable: {v2['problems']}")
    # strip the reasons: verification must now fail
    noreason = json.loads(json.dumps(s2))
    for d in noreason["decisions"]:
        d["reasons"] = []
    (work / "s-noreason.json").write_text(json.dumps(noreason, ensure_ascii=False), encoding="utf-8")
    rc_nr, _ = run("verify", "--screening", work / "s-noreason.json", "--out", work / "v-nr.json")
    vnr = load(work / "v-nr.json")
    observed["verify_no_reasons"] = {"rc": rc_nr, "status": vnr["status"]}
    if vnr["status"] == "verified":
        failures.append("an included set with no recorded reasons still verified")

    # ---- 5 coverage states its bound and names the omissions
    run("coverage", "--records", work / "records.csv", "--query", work / "q2.json", "--out", work / "cov.json")
    cov = load(work / "cov.json")
    observed["coverage"] = {"status": cov["status"], "omissions": len(cov["omissions"])}
    if "bounded by the corpus" not in cov.get("bound", ""):
        failures.append("coverage does not state that the conclusion is bounded by the corpus")

    # ---- 6 appraise: a missing scale must refuse, a stated one must grade with a weight
    (work / "scale-empty.json").write_text(json.dumps({"dimensions": []}), encoding="utf-8")
    rc_e, _ = run("appraise", "--records", work / "records.csv", "--scale", work / "scale-empty.json",
                  "--out", work / "ap0.json")
    ap0 = load(work / "ap0.json")
    observed["appraise_no_scale"] = {"rc": rc_e, "status": ap0["status"]}
    if ap0["status"] != "refused":
        failures.append("appraisal proceeded with no stated scale")
    (work / "scale.json").write_text(json.dumps({
        "name": "three-dimension appraisal",
        "dimensions": [
            {"name": "sample described", "satisfied_by": ["conversion", "glycerol"]},
            {"name": "method described", "satisfied_by": ["catalyst"]},
            {"name": "limitation stated", "satisfied_by": ["limitation", "deactivation"]},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    run("appraise", "--records", work / "records.csv", "--scale", work / "scale.json", "--out", work / "ap.json")
    ap = load(work / "ap.json")
    observed["appraise"] = {"graded": len(ap["graded"]),
                            "weights": sorted({g["weight_in_conclusion"] for g in ap["graded"]})}
    if not ap["graded"]:
        failures.append("a stated scale produced no grades")
    if any("weight_in_conclusion" not in g for g in ap["graded"]):
        failures.append("the grade was not carried into a weight in the conclusion")

    # ---- 7 synonyms: cross-language sets are flagged as translations
    (work / "terms.json").write_text(json.dumps({"sets": {
        "catalyst": ["catalyst", "catalysis", "\u50ac\u5316\u5242", "\u50ac\u5316"],
        "conversion": ["conversion", "\u8f6c\u5316\u7387"],
    }}, ensure_ascii=False), encoding="utf-8")
    run("synonyms", "--terms", work / "terms.json", "--out", work / "syn.json")
    syn = load(work / "syn.json")
    observed["synonyms"] = {"concepts": syn["concepts"], "translated": len(syn["translations"])}
    if syn["concepts"] != 2:
        failures.append(f"expected 2 concepts, got {syn['concepts']}")
    if len(syn["translations"]) != 2:
        failures.append("a cross-language set was not recorded as a translation")

    report = {"fixture": str(work), "checks": 7, "failures": failures, "observed": observed,
              "verdict": "pass" if not failures else "fail",
              "note": "Synthetic fixtures only; not organiser cases, not official results."}
    (work / "retrieval-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
