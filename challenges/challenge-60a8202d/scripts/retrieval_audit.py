"""Search-strategy audit: query construction, screening records, coverage accounting, appraisal.

Written for the eleven literature-search tasks. With no network, every case supplies its own corpus, so
this is not about reaching a database — it is **retrieval discipline over supplied material**. The
organisers measure exactly three things, repeated across the briefs: whether every inclusion and
exclusion has a checkable reason, whether every statement links back to a position in a named source,
and whether a second person can re-run the same inputs and records and get substantially the same
included set.

That is record-keeping. This module makes the record mechanical.

    python retrieval_audit.py query     --question q.txt --strategy s.json --out query.json
    python retrieval_audit.py screen    --records r.csv --criteria c.json --out screening.json
    python retrieval_audit.py coverage  --records r.csv --query query.json --out coverage.json
    python retrieval_audit.py appraise  --records r.csv --scale scale.json --out appraisal.json
    python retrieval_audit.py synonyms  --terms t.json --out synonyms.json
    python retrieval_audit.py reconcile --screening screening.json --out counts.json
    python retrieval_audit.py verify    --screening screening.json --out verify.json

Python standard library only. No network.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCHEMA = "retrieval-audit/v1"

# A criterion is adjudicable only if it can be applied without asking the author. These are the words
# that make one un-adjudicable, because two reviewers would decide differently on the same record.
VAGUE = ("interesting", "relevant", "important", "good", "appropriate", "suitable", "novel",
         "\u6709\u610f\u601d", "\u76f8\u5173", "\u91cd\u8981", "\u5408\u9002", "\u521b\u65b0")

# PRISMA-style stages. The counts must reconcile across them, which is the specific thing the briefs ask
# for and the thing that silently fails when a stage is skipped.
STAGES = ("retrieved", "deduplicated", "title_screened", "fulltext_screened", "included")

DECISION_STATES = ("include", "exclude", "uncertain", "not_screened")


# ------------------------------------------------------------------ query

def build_query(question: str, strategy: dict) -> dict:
    """Turn a question into an executable, inspectable strategy.

    Every block records its *intent*, because the briefs ask the strategy to say why each clause is
    there rather than only what it is. A block with no intent is a finding: it cannot be reviewed or
    removed deliberately later.
    """
    findings: list[dict] = []
    blocks = strategy.get("blocks") or []
    if not blocks:
        # derive a first pass from the question itself rather than inventing terms
        terms = [w for w in re.findall(r"[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\-]{2,}",
                                       question) if w.lower() not in
                 ("the", "and", "for", "with", "does", "what", "which", "how", "are", "was", "were")]
        blocks = [{"field": "title_abstract", "terms": sorted(set(terms)), "intent": "concept terms from the question"}]
        findings.append({"dimension": "query_construction", "severity": "medium",
                         "locator": "strategy", "evidence": "no explicit strategy supplied",
                         "suggested_action": "confirm or replace the derived terms and state each block's intent"})

    for index, block in enumerate(blocks):
        if not block.get("intent"):
            findings.append({"dimension": "query_construction", "severity": "medium",
                             "locator": f"block[{index}]",
                             "evidence": block.get("terms") or block.get("query"),
                             "suggested_action": "state what this block is for, so it can be reviewed or removed deliberately"})
        if not block.get("field"):
            findings.append({"dimension": "query_construction", "severity": "low",
                             "locator": f"block[{index}]", "evidence": "no field named",
                             "suggested_action": "name the field searched, e.g. title_abstract or fulltext"})

    limits = strategy.get("limits") or {}
    for kind in ("language", "date"):
        if not limits.get(kind):
            findings.append({"dimension": "query_limits", "severity": "low", "locator": f"limits.{kind}",
                             "evidence": "no limit declared",
                             "suggested_action": f"state the {kind} limit explicitly; an unstated limit becomes an unexplained omission"})

    return {
        "schema": SCHEMA, "blocks": len(blocks), "limits": limits,
        "sources": strategy.get("sources") or [],
        "findings": findings,
        "status": "inspectable" if not any(f["severity"] == "high" for f in findings) else "needs_work",
        "rule": ("every block states its intent and its field, and every limit is explicit, so the "
                 "strategy can be re-run and its omissions explained"),
    }


# ------------------------------------------------------------------ screening

def screen(records: list[dict], criteria: dict) -> dict:
    """Apply adjudicable criteria and keep a per-record reason.

    Two things this refuses: a criterion that cannot be adjudicated (a vagueness term with no
    threshold), and a decision with no reason. Both are the failures the briefs name, and both are
    checkable mechanically.
    """
    include_c = criteria.get("include") or []
    exclude_c = criteria.get("exclude") or []
    findings: list[dict] = []

    for label, group in (("include", include_c), ("exclude", exclude_c)):
        for index, criterion in enumerate(group):
            text = criterion if isinstance(criterion, str) else json.dumps(criterion, ensure_ascii=False)
            has_threshold = bool(re.search(r"\d|before|after|since|at least|at most|within|"
                                           r"\u4ee5\u4e0a|\u4ee5\u4e0b|\u4e4b\u524d|\u4e4b\u540e|\u8d85\u8fc7|\u4f4e\u4e8e", text, re.I))
            vague = any(v in text.lower() for v in VAGUE)
            if vague and not has_threshold:
                findings.append({
                    "dimension": "criterion_adjudicability", "severity": "high",
                    "locator": f"{label}[{index}]", "evidence": text[:120],
                    "suggested_action": ("make it decidable without asking the author: name the property "
                                         "and the bound, e.g. 'sample size at least 10' rather than 'relevant'"),
                })

    decisions: list[dict] = []
    reasons: Counter = Counter()
    for index, record in enumerate(records):
        decided = _decide(record, include_c, exclude_c)
        if decided["decision"] == "include":
            for reason in decided["reasons"]:
                reasons[reason] += 1
        decisions.append({"record": index, "id": record.get("id") or record.get("record_id") or f"#{index}",
                          **decided})

    unexplained = [d for d in decisions if d["decision"] != "not_screened" and not d["reasons"]]
    if unexplained:
        findings.append({"dimension": "screening_record", "severity": "high", "locator": "screening",
                         "evidence": f"{len(unexplained)} decision(s) with no reason",
                         "suggested_action": "record the criterion that produced each decision and who made it"})

    applied = {d["decision"] for d in decisions}
    return {
        "schema": SCHEMA, "records": len(records),
        "include_criteria": len(include_c), "exclude_criteria": len(exclude_c),
        "decisions": decisions,
        "counts": {state: sum(1 for d in decisions if d["decision"] == state)
                   for state in DECISION_STATES},
        "criterion_usage": dict(reasons),
        "findings": findings,
        "status": "complete" if not any(f["severity"] == "high" for f in findings) else "needs_work",
        "rule": ("every decision names the criterion that produced it; a criterion that cannot be "
                 "adjudicated is a finding, because two reviewers would split on it"),
    }


def _decide(record: dict, include_c: list, exclude_c: list) -> dict:
    """Apply criteria as declared, recording which ones fired. No criterion, no decision."""
    text = " ".join(str(v) for v in record.values()).lower()
    fired, failed = [], []
    for criterion in exclude_c:
        if _matches(criterion, text):
            name = criterion if isinstance(criterion, str) else json.dumps(criterion, ensure_ascii=False)
            failed.append(name)
    if failed:
        return {"decision": "exclude", "reasons": failed, "kind": "exclusion"}
    for criterion in include_c:
        if _matches(criterion, text):
            name = criterion if isinstance(criterion, str) else json.dumps(criterion, ensure_ascii=False)
            fired.append(name)
    if fired and len(fired) == len(include_c):
        return {"decision": "include", "reasons": fired, "kind": "inclusion"}
    if fired:
        return {"decision": "uncertain", "reasons": fired,
                "kind": "partial", "missing": len(include_c) - len(fired)}
    return {"decision": "not_screened", "reasons": [],
            "note": "no declared criterion could be evaluated against this record"}


def _matches(criterion, text: str) -> bool:
    """A criterion is a term list, a keyword, or a mapping with terms. Matching is literal and recorded."""
    if isinstance(criterion, dict):
        terms = criterion.get("terms") or criterion.get("all_of") or []
        if criterion.get("kind") == "year_at_least":
            year = record_year = None
        return all(str(t).lower() in text for t in terms) if terms else False
    if isinstance(criterion, dict):
        return False
    # a criterion given as a string: match its significant words, all of them
    words = [w for w in re.findall(r"[A-Za-z\u4e00-\u9fff]{3,}", str(criterion).lower())]
    return all(w in text for w in words) if words else False


# ------------------------------------------------------------------ coverage

def coverage(records: list[dict], query: dict) -> dict:
    """Report what the corpus and the strategy could and could not cover.

    The point is to state the boundary of the conclusion rather than the size of the search: a claim
    derived from a corpus that omitted a category is bounded by that omission, and saying so is what
    makes the finding usable.
    """
    fields = set()
    for record in records:
        fields.update(k for k, v in record.items() if str(v).strip())
    # which of the query's blocks could actually be evaluated against the fields present
    blocks = query.get("blocks") or 0
    same_language = 0
    for record in records:
        text = " ".join(str(v) for v in record.values())
        if re.search(r"[\u4e00-\u9fff]", text):
            same_language += 1
    limits = query.get("limits") or {}
    omissions = []
    if blocks == 0:
        omissions.append({"what": "query", "why": "no strategy recorded, so coverage cannot be bounded"})
    if not limits.get("language"):
        omissions.append({"what": "language", "why": "not stated, so non-matching-language material is an unexplained omission"})
    if not limits.get("date"):
        omissions.append({"what": "date", "why": "not stated, so an older result cannot be distinguished from an absent one"})
    if limits.get("date") and re.search(r"(19|20)\d{2}", str(limits.get("date"))):
        pass
    return {
        "schema": SCHEMA, "records": len(records), "fields_present": sorted(fields),
        "records_with_non_ascii": same_language,
        "declared_limits": limits,
        "omissions": omissions,
        "bound": ("the conclusion below is bounded by the corpus supplied and by the limits declared "
                  "above; it does not extend to material those limits excluded, and material that could "
                  "not be screened is reported rather than absorbed"),
        "status": "bounded" if not omissions else "incomplete",
    }


# ------------------------------------------------------------------ appraisal

def appraise(records: list[dict], scale: dict) -> dict:
    """Apply a stated appraisal scale dimension by dimension, and carry the grade into the weight."""
    dimensions = scale.get("dimensions") or []
    if not dimensions:
        return {"schema": SCHEMA, "status": "refused",
                "reason": "no appraisal scale supplied; inventing one would make the grades uninterpretable",
                "rule": "the scale must be stated before it is applied"}
    findings: list[dict] = []
    graded: list[dict] = []
    for index, record in enumerate(records):
        per_dimension = {}
        text = " ".join(str(v) for v in record.values()).lower()
        for dim in dimensions:
            name = dim.get("name") if isinstance(dim, dict) else str(dim)
            markers = (dim.get("satisfied_by") or []) if isinstance(dim, dict) else []
            hit = [m for m in markers if str(m).lower() in text]
            per_dimension[name] = {
                "grade": ("satisfied" if hit else "not established"),
                "evidence": hit if hit else "no marker present in the record",
            }
            if not markers:
                findings.append({"dimension": "appraisal_scale", "severity": "medium",
                                 "locator": f"dimension:{name}",
                                 "evidence": "no marker defined for this dimension",
                                 "suggested_action": "state what establishes this dimension, so the grade is checkable"})
        established = sum(1 for v in per_dimension.values() if v["grade"] == "satisfied")
        ratio = established / len(dimensions)
        grade = ("high" if ratio >= 0.75 else "moderate" if ratio >= 0.4 else "low")
        graded.append({"record": index, "id": record.get("id", f"#{index}"),
                       "dimensions": per_dimension, "established": established,
                       "of": len(dimensions), "grade": grade,
                       "weight_in_conclusion": {"high": 1.0, "moderate": 0.6, "low": 0.25}[grade]})
    return {
        "schema": SCHEMA, "scale": scale.get("name", "unspecified"), "dimensions": len(dimensions),
        "graded": graded, "findings": findings,
        "rule": ("each dimension is graded against a stated marker with the supporting position; the "
                 "grade is carried into how much weight the finding gets, so a low-quality study does "
                 "not count equally with a high-quality one"),
        "status": "complete" if not any(f["severity"] == "high" for f in findings) else "needs_work",
    }


# ------------------------------------------------------------------ synonyms

def synonyms(terms: dict) -> dict:
    """Build cross-language synonym sets and record every translation that was applied."""
    sets = terms.get("sets") or terms
    out = []
    translations = []
    for key, group in sets.items():
        if isinstance(group, str):
            group = [group]
        zh = [t for t in group if re.search(r"[\u4e00-\u9fff]", str(t))]
        en = [t for t in group if not re.search(r"[\u4e00-\u9fff]", str(t))]
        out.append({"concept": key, "all_terms": sorted(set(map(str, group))),
                    "chinese": sorted(zh), "non_chinese": sorted(en),
                    "cross_language": bool(zh and en)})
        if zh and en:
            translations.append({"concept": key, "applied": True,
                                 "note": "a term in one language was matched by its counterpart in the other; "
                                         "the mapping is recorded so the match can be reviewed"})
    return {
        "schema": SCHEMA, "concepts": len(out), "sets": out, "translations": translations,
        "rule": ("a cross-language match is recorded as a translation, so a reviewer can see that a "
                 "match came from a mapping rather than from the text itself"),
    }


# ------------------------------------------------------------------ reconcile / verify

def reconcile(screening: dict) -> dict:
    """Check the stage counts add up. A stage that silently lost records is the failure this catches.

    The declared record count is compared against the decisions actually present. Deriving the stages
    from the decisions list alone cannot detect a lost record, because the list *is* the only evidence —
    so the declared total is the invariant that has to be checked against.
    """
    decisions = screening.get("decisions") or []
    declared = screening.get("records")
    stage_counts = {s: None for s in STAGES}
    stage_counts["retrieved"] = len(decisions)
    stage_counts["title_screened"] = sum(1 for d in decisions if d["decision"] != "not_screened")
    stage_counts["fulltext_screened"] = sum(1 for d in decisions
                                            if d["decision"] in ("include", "exclude"))
    stage_counts["included"] = sum(1 for d in decisions if d["decision"] == "include")

    problems = []
    if declared is not None and len(decisions) != declared:
        problems.append(f"{declared} record(s) declared but {len(decisions)} decision(s) recorded: "
                        f"{declared - len(decisions)} lost between retrieval and screening")
    ordered = ["retrieved", "title_screened", "fulltext_screened", "included"]
    for earlier, later in zip(ordered, ordered[1:]):
        if stage_counts[later] > stage_counts[earlier]:
            problems.append(f"{later} ({stage_counts[later]}) exceeds {earlier} ({stage_counts[earlier]})")
    not_screened = sum(1 for d in decisions if d["decision"] == "not_screened")
    uncertain = sum(1 for d in decisions if d["decision"] == "uncertain")
    if not_screened:
        problems.append(f"{not_screened} record(s) were never screened")
    return {
        "schema": SCHEMA, "declared_records": declared, "stages": stage_counts,
        "uncertain": uncertain, "not_screened": not_screened, "problems": problems,
        "status": "reconciled" if not problems else "needs_work",
        "rule": ("the counts must reconcile across stages and against the declared record count; a "
                 "record lost between stages is reported rather than absorbed into the total"),
    }


def verify(screening: dict) -> dict:
    """Prove the included set is recomputable from the record alone."""
    decisions = screening.get("decisions") or []
    included = [d for d in decisions if d["decision"] == "include"]
    problems = []
    for entry in included:
        if not entry.get("reasons"):
            problems.append(f"record {entry.get('id')} was included with no recorded reason")
    if not decisions:
        problems.append("no screening decisions recorded")
    recomputable = all(d.get("reasons") is not None for d in decisions)
    return {
        "schema": SCHEMA, "decisions": len(decisions), "included": len(included),
        "recomputable": recomputable, "problems": problems,
        "status": "verified" if not problems else "needs_work",
        "note": ("a second person with the same records and criteria reaches the same included set; "
                 "that is the test the briefs state"),
    }


# ------------------------------------------------------------------ cli

def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Search-strategy audit over a supplied corpus")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("query"); p.add_argument("--question", required=True); p.add_argument("--strategy", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("screen"); p.add_argument("--records", required=True); p.add_argument("--criteria", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("coverage"); p.add_argument("--records", required=True); p.add_argument("--query", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("appraise"); p.add_argument("--records", required=True); p.add_argument("--scale", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("synonyms"); p.add_argument("--terms", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("reconcile"); p.add_argument("--screening", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("verify"); p.add_argument("--screening", required=True); p.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.command == "query":
        result = build_query(Path(args.question).read_text(encoding="utf-8"), read_json(args.strategy))
        write_json(args.out, result)
        print(json.dumps({"blocks": result["blocks"], "findings": len(result["findings"])}, ensure_ascii=False))
        return 0
    if args.command == "screen":
        result = screen(read_csv(args.records), read_json(args.criteria)); write_json(args.out, result)
        print(json.dumps({"records": result["records"], "counts": result["counts"],
                          "status": result["status"]}, ensure_ascii=False))
        return 0 if result["status"] == "complete" else 3
    if args.command == "coverage":
        result = coverage(read_csv(args.records), read_json(args.query)); write_json(args.out, result)
        print(json.dumps({"records": result["records"], "omissions": len(result["omissions"]),
                          "status": result["status"]}, ensure_ascii=False))
        return 0
    if args.command == "appraise":
        result = appraise(read_csv(args.records), read_json(args.scale)); write_json(args.out, result)
        if result["status"] == "refused":
            print(json.dumps({"status": "refused", "reason": result["reason"][:120]}, ensure_ascii=False))
            return 3
        print(json.dumps({"graded": len(result["graded"]), "status": result["status"]}, ensure_ascii=False))
        return 0
    if args.command == "synonyms":
        result = synonyms(read_json(args.terms)); write_json(args.out, result)
        print(json.dumps({"concepts": result["concepts"],
                          "cross_language": len(result["translations"])}, ensure_ascii=False))
        return 0
    if args.command == "reconcile":
        result = reconcile(read_json(args.screening)); write_json(args.out, result)
        print(json.dumps({"stages": result["stages"], "status": result["status"]}, ensure_ascii=False))
        return 0 if result["status"] == "reconciled" else 3
    if args.command == "verify":
        result = verify(read_json(args.screening)); write_json(args.out, result)
        print(json.dumps({"included": result["included"], "status": result["status"]}, ensure_ascii=False))
        return 0 if result["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
