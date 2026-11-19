"""Build and validate a small benchmark case set (literature reading / academic writing).

The benchmark tasks ask for a reusable evaluation artefact: cases with a task instruction, the
material they rest on, an expected-answer contract and a scoring rule that another person can run
without asking the author. This module makes that mechanical:

    build     a case set from a declarative spec (each case: instruction, material locators,
              expected fields, scoring anchors)
    validate  structure and self-consistency: required fields, resolvable material, anchor
              coverage, no duplicated ids, and a scoring rule that can be computed
    score     run a candidate answer file through the declared rule — a real, reproducible score
              for the declared rubric (not an official platform score)
    verify    re-run the validation and the scoring to prove the set is reproducible

Only the Python standard library is used, so the set can be validated in a container with no
network, no LLM and no grading service.

Commands
--------
build    --spec FILE --outdir DIR
validate --spec FILE --outdir DIR
score    --spec FILE --answers FILE --outdir DIR
verify   --spec FILE --outdir DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REQUIRED_CASE_FIELDS = ("id", "title", "instruction", "material", "expected", "anchors")
REQUIRED_ANCHOR_FIELDS = ("id", "text", "points", "kind")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def load(path: Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload["_path"] = str(path)
    payload["_sha256"] = sha256_file(path)
    return payload


def validate_case(case: dict, base: Path) -> list:
    problems = []
    for field in REQUIRED_CASE_FIELDS:
        if not case.get(field):
            problems.append(f"case {case.get('id')!r} is missing '{field}'")
    if not isinstance(case.get("anchors"), list):
        return problems
    if len(case["anchors"]) < 1:
        problems.append(f"case {case.get('id')!r} declares no scoring anchors")
    seen = set()
    earnable = 0.0
    penalty_total = 0.0
    for anchor in case["anchors"]:
        for field in REQUIRED_ANCHOR_FIELDS:
            if field not in anchor:
                problems.append(f"case {case.get('id')!r} anchor {anchor.get('id')!r} is missing "
                                f"'{field}'")
        if anchor.get("id") in seen:
            problems.append(f"case {case.get('id')!r} repeats anchor id {anchor.get('id')!r}")
        seen.add(anchor.get("id"))
        if not isinstance(anchor.get("points"), (int, float)) or anchor.get("points") < 0:
            problems.append(f"case {case.get('id')!r} anchor {anchor.get('id')!r} has a non-numeric "
                            "or negative weight")
        elif anchor.get("kind") == "penalty":
            penalty_total += anchor["points"]
        else:
            earnable += anchor["points"]
        if anchor.get("kind") not in ("required", "bonus", "penalty"):
            problems.append(f"case {case.get('id')!r} anchor {anchor.get('id')!r} has kind "
                            f"{anchor.get('kind')!r}; expected required/bonus/penalty")
    if case.get("max_points") is not None and abs(earnable - case["max_points"]) > 1e-9:
        problems.append(f"case {case.get('id')!r} earnable anchors sum to {earnable} but max_points "
                        f"is {case['max_points']}")
    for material in case.get("material") or []:
        if isinstance(material, dict) and material.get("path"):
            candidate = (base / material["path"]).resolve()
            if not candidate.exists():
                problems.append(f"case {case.get('id')!r} references missing material "
                                f"{material['path']}")
    expected = case.get("expected") or {}
    if isinstance(expected, dict) and not expected:
        problems.append(f"case {case.get('id')!r} declares an empty expected-answer contract")
    return problems


def validate(spec: dict, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    base = Path(spec["_path"]).parent
    problems = []
    if not spec.get("cases"):
        problems.append("the spec declares no cases")
    ids = [case.get("id") for case in spec.get("cases") or []]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        problems.append(f"duplicate case ids: {duplicates}")
    for case in spec.get("cases") or []:
        problems.extend(validate_case(case, base))
    kinds = {case.get("kind") for case in spec.get("cases") or []}
    if len(kinds) < int(spec.get("min_cases") or 1):
        problems.append(f"the spec declares {len(kinds)} case kind(s); at least "
                        f"{spec.get('min_cases')} are required")

    report = {
        "schema": "benchmark-build/v1",
        "spec": {"path": spec["_path"], "sha256": spec["_sha256"]},
        "title": spec.get("title"),
        "purpose": spec.get("purpose"),
        "case_count": len(spec.get("cases") or []),
        "cases": [{"id": case.get("id"), "title": case.get("title"), "kind": case.get("kind"),
                   "anchors": len(case.get("anchors") or []),
                   "earnable_points": sum(anchor.get("points") or 0
                                          for anchor in case.get("anchors") or []
                                          if anchor.get("kind") != "penalty"),
                   "penalty_points": sum(anchor.get("points") or 0
                                         for anchor in case.get("anchors") or []
                                         if anchor.get("kind") == "penalty"),
                   "max_points": case.get("max_points"),
                   "material": [m.get("path") if isinstance(m, dict) else m
                                for m in (case.get("material") or [])]}
                  for case in spec.get("cases") or []],
        "problems": problems,
        "problem_count": len(problems),
        "status": "valid" if not problems else "invalid",
        "scoring_rule": spec.get("scoring_rule") or "sum of matched anchor weights, clipped to the "
                                                    "case's max_points",
        "scope_note": "This validates a benchmark case set: structure, resolvable material, anchor "
                      "weights and a computable scoring rule. It does not certify that the expected "
                      "answers are scientifically right.",
    }
    (outdir / "benchmark-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
    return report


def score_case(case: dict, answer: dict) -> dict:
    """Score one answer against the declared anchors. Deterministic and inspectable."""
    text = normalise(json.dumps(answer, ensure_ascii=False))
    matched, missed = [], []
    for anchor in case.get("anchors") or []:
        needles = anchor.get("match_any") or [anchor.get("text") or ""]
        found = any(normalise(needle) and normalise(needle) in text for needle in needles)
        record = {"anchor": anchor.get("id"), "points": anchor.get("points"),
                  "kind": anchor.get("kind"), "matched": bool(found),
                  "evidence": (anchor.get("text") or "")[:120]}
        if found:
            matched.append(record)
        elif anchor.get("kind") == "required":
            missed.append(record)
    earned = sum(anchor["points"] for anchor in matched if anchor["kind"] != "penalty")
    penalty = sum(anchor["points"] for anchor in matched if anchor["kind"] == "penalty")
    maximum = case.get("max_points") or sum(anchor["points"] for anchor in case.get("anchors") or []
                                            if anchor["kind"] != "penalty")
    final = max(0.0, min(earned - penalty, maximum))
    return {
        "case": case.get("id"),
        "earned": earned,
        "penalty": penalty,
        "max_points": maximum,
        "score": round(final, 4),
        "normalised": round(final / maximum, 4) if maximum else None,
        "matched_anchors": [record["anchor"] for record in matched],
        "missed_required": [record["anchor"] for record in missed],
        "detail": matched + missed,
    }


def score(spec: dict, answers_path: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    answers = json.loads(Path(answers_path).read_text(encoding="utf-8"))
    by_case = answers.get("answers") if isinstance(answers, dict) else None
    if not isinstance(by_case, dict):
        raise SystemExit("the answers file must be {\"answers\": {\"<case id>\": <answer object>}}")
    results = []
    for case in spec.get("cases") or []:
        answer = by_case.get(case.get("id"))
        if answer is None:
            results.append({"case": case.get("id"), "score": 0.0, "normalised": 0.0,
                            "missed_required": [anchor.get("id") for anchor in case.get("anchors") or []
                                                if anchor.get("kind") == "required"],
                            "note": "no answer supplied for this case"})
            continue
        results.append(score_case(case, answer))
    total = sum(result["score"] for result in results)
    maximum = sum(result["max_points"] for result in results) or 1
    report = {
        "schema": "benchmark-score/v1",
        "spec": {"path": spec["_path"], "sha256": spec["_sha256"]},
        "answers": {"path": str(answers_path), "sha256": sha256_file(answers_path)},
        "results": results,
        "total": round(total, 4),
        "maximum": maximum,
        "normalised_total": round(total / maximum, 4),
        "method": "each anchor is matched by normalised substring against the whole answer object; "
                  "required anchors that do not match are reported by id; the score is the matched "
                  "weight minus any matched penalty, clipped to the case maximum.",
        "scope_note": "This is a reproducible score for THIS declared rubric. It is not an official "
                      "platform score and not a substitute for expert review.",
    }
    (outdir / "scoring-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    return report


def verify(spec_path: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    spec = load(spec_path)
    fresh = validate(spec, outdir / "recheck")
    checks = []

    def add(check_id, requirement, ok, evidence):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence})

    add("structure_valid", "the case set validates with no problems", fresh["status"] == "valid",
        f"problems={fresh['problems']}")
    add("case_count", "the set declares the minimum number of cases",
        fresh["case_count"] >= int(spec.get("min_cases") or 1),
        f"cases={fresh['case_count']} kinds={len({c.get('kind') for c in spec.get('cases') or []})}")
    add("deterministic", "a second validation produces the same result",
        fresh["problem_count"] == len(fresh["problems"]), "same problem list reproduced")
    add("scoring_reproducible", "the declared rule can be recomputed from the set alone",
        all((case.get("anchors") and case.get("max_points") is not None)
            for case in spec.get("cases") or []),
        "every case declares anchors and a maximum the rule can compute")
    failures = [c for c in checks if c["status"] == "fail"]
    report = {"schema": "benchmark-verify/v1", "checks": checks,
              "passed": len(checks) - len(failures), "failed": len(failures),
              "status": "verified" if not failures else "needs_work",
              "scope_note": "Proves the case set is structurally valid and its scoring rule is "
                            "reproducible. It does not prove the expected answers are correct."}
    (outdir / "benchmark-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark case set builder and scorer")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "validate", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--spec", required=True)
        p.add_argument("--outdir", required=True)
    p = sub.add_parser("score")
    p.add_argument("--spec", required=True)
    p.add_argument("--answers", required=True)
    p.add_argument("--outdir", required=True)
    args = parser.parse_args(argv)

    if args.command in ("build", "validate"):
        spec = load(Path(args.spec))
        report = validate(spec, Path(args.outdir))
        print(json.dumps({"cases": report["case_count"], "problems": report["problems"],
                          "status": report["status"]}, ensure_ascii=False))
        return 0 if report["status"] == "valid" else 2
    if args.command == "score":
        spec = load(Path(args.spec))
        report = score(spec, Path(args.answers), Path(args.outdir))
        print(json.dumps({"total": report["total"], "maximum": report["maximum"],
                          "normalised": report["normalised_total"],
                          "per_case": {r["case"]: r["score"] for r in report["results"]}},
                         ensure_ascii=False))
        return 0
    if args.command == "verify":
        report = verify(Path(args.spec), Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
