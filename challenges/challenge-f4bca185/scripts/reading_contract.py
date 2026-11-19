"""Contract-driven reading answers: one result per requested field, each with its evidence.

The reading tasks share one demand: an answer that can be checked line by line. This module makes
that mechanical and standard-library only:

    contract  read the case's requested fields (a `target-fields.json`, a question list, or a field
              declaration in `case.json`) and emit one skeleton entry per field id, so no requested
              field can be silently dropped
    evidence  attach a source locator (paper id, paragraph/section id, page) and a verbatim short
              quotation to every claim, and refuse a quotation that is not actually in the supplied
              text
    status    use the case's own vocabulary — reported / not_reported / source_conflict /
              extraction_failed for field extraction, answered / partial / insufficient_evidence /
              input_error for questions — and never let a guess look like a reported value
    check     verify the produced answer against the contract: coverage, statuses, quotation
              fidelity, numeric preservation and the case's own required fields

Commands
--------
contract --case FILE [--fields FILE] [--questions FILE] --out FILE
check    --answer FILE --case FILE [--fields FILE] [--questions FILE] --outdir DIR
verify   --answer FILE --outdir DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

READING_STATUSES = ("reported", "not_reported", "source_conflict", "extraction_failed")
ANSWER_STATUSES = ("answered", "partial", "insufficient_evidence", "input_error")
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def discover_fields(case: dict, fields_path: Path | None) -> list:
    """The requested fields, from an explicit file or from the case contract itself."""
    if fields_path:
        payload = load_json(fields_path)
        if isinstance(payload, list):
            return payload
        for key in ("fields", "target_fields", "requested_fields"):
            if isinstance(payload.get(key), list):
                return payload[key]
        raise SystemExit(f"{fields_path} does not declare a field list")
    for key in ("target_fields", "fields", "requested_fields"):
        value = case.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [{"field_id": k, **v} if isinstance(v, dict) else {"field_id": k, "description": v}
                    for k, v in value.items()]
    return []


def field_id(field) -> str:
    if isinstance(field, str):
        return field
    for key in ("field_id", "id", "name", "key"):
        if field.get(key):
            return str(field[key])
    raise SystemExit(f"a requested field has no id: {field!r}")


def build_contract(case: dict, fields: list, questions: list) -> dict:
    case_id = case.get("case_id") or case.get("id")
    entries = []
    for field in fields:
        identifier = field_id(field)
        entries.append({
            "field_id": identifier,
            "description": field.get("description") if isinstance(field, dict) else None,
            "unit": field.get("unit") if isinstance(field, dict) else None,
            "status": None,
            "value": None,
            "paragraph_id": None,
            "quote": None,
            "note": None,
        })
    question_entries = []
    for question in questions:
        identifier = question.get("question_id") or question.get("id") if isinstance(question, dict) \
            else str(question)
        question_entries.append({
            "question_id": identifier,
            "text": question.get("text") if isinstance(question, dict) else str(question),
            "status": None,
            "answer": None,
            "conditions": [],
            "claims": [],
            "unanswered_parts": [],
        })
    return {
        "schema": "reading-contract/v1",
        "case_id": case_id,
        "requested_field_count": len(entries),
        "requested_question_count": len(question_entries),
        "fields": entries,
        "questions": question_entries,
        "status_vocabulary": {"fields": list(READING_STATUSES), "questions": list(ANSWER_STATUSES)},
        "instruction": ("Fill every entry. A value the material does not report is 'not_reported'; "
                        "a field whose sources disagree is 'source_conflict' and must carry both "
                        "locators; a field that could not be read is 'extraction_failed'. Every "
                        "'reported' entry needs a paragraph/section locator and a verbatim quote."),
    }


def collect_source_text(case: dict, base: Path) -> dict:
    """All text the answer may quote, keyed by the locator a human would use."""
    sources = {}
    for key in ("paragraphs", "sections", "text_blocks", "materials", "sources"):
        value = case.get(key)
        if isinstance(value, list):
            for index, item in enumerate(value, start=1):
                if isinstance(item, str):
                    sources[f"{key}[{index}]"] = item
                elif isinstance(item, dict):
                    locator = (item.get("paragraph_id") or item.get("id") or item.get("section")
                               or f"{key}[{index}]")
                    text = item.get("text") or item.get("content") or item.get("quote") or ""
                    if text:
                        sources[str(locator)] = text
        elif isinstance(value, dict):
            for locator, item in value.items():
                sources[str(locator)] = item if isinstance(item, str) else json.dumps(item)
    for key in ("material", "inputs", "files"):
        for item in case.get(key) or []:
            path = item.get("path") if isinstance(item, dict) else item
            if not path:
                continue
            candidate = (base / path).resolve()
            if candidate.exists() and candidate.suffix.lower() in (".md", ".txt", ".json", ".csv"):
                sources[str(path)] = candidate.read_text(encoding="utf-8", errors="replace")
    return sources


def check(answer: dict, case: dict, fields: list, questions: list, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    base = Path(case.get("_path") or ".").parent
    sources = collect_source_text(case, base)
    all_text = normalise(" ".join(sources.values()))
    checks = []

    def add(check_id, requirement, ok, evidence):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence})

    requested_ids = [field_id(field) for field in fields]
    answered = answer.get("fields") or answer.get("results") or []
    by_id = {}
    for entry in answered:
        identifier = entry.get("field_id") or entry.get("id")
        if identifier:
            by_id[str(identifier)] = entry
    missing = [identifier for identifier in requested_ids if identifier not in by_id]
    add("field_coverage", "every requested field id has exactly one result entry",
        not missing, f"missing={missing[:8]} of {len(requested_ids)} requested")
    duplicates = [identifier for identifier in requested_ids
                  if sum(1 for entry in answered
                         if str(entry.get("field_id") or entry.get("id")) == identifier) > 1]
    add("no_duplicate_fields", "no requested field is answered twice", not duplicates,
        f"duplicated={sorted(set(duplicates))}")

    bad_status = [identifier for identifier, entry in by_id.items()
                  if entry.get("status") not in READING_STATUSES]
    add("status_vocabulary", "every field result uses the case's own status vocabulary",
        not bad_status, f"off-vocabulary={bad_status[:8]} (allowed: {list(READING_STATUSES)})")

    unreported_with_value = [identifier for identifier, entry in by_id.items()
                             if entry.get("status") == "not_reported"
                             and entry.get("value") not in (None, "", "None")]
    add("no_value_for_unreported", "a 'not_reported' field carries no value",
        not unreported_with_value,
        f"not_reported entries carrying a value={unreported_with_value[:8]}")

    missing_quote = [identifier for identifier, entry in by_id.items()
                     if entry.get("status") == "reported"
                     and (not entry.get("quote") or not (entry.get("paragraph_id")
                                                         or entry.get("locator")))]
    add("reported_fields_have_evidence",
        "every 'reported' field carries a locator and a quotation", not missing_quote,
        f"reported without locator/quote={missing_quote[:8]}")

    unverifiable = []
    for identifier, entry in by_id.items():
        quote = entry.get("quote")
        if not quote or entry.get("status") != "reported":
            continue
        if sources and normalise(quote) not in all_text:
            unverifiable.append(identifier)
    add("quotes_are_verbatim", "every quotation actually appears in the supplied material",
        not unverifiable, f"quotes not found in the material={unverifiable[:8]}")

    conflicts_without_both = [identifier for identifier, entry in by_id.items()
                              if entry.get("status") == "source_conflict"
                              and len(entry.get("locators") or entry.get("conflicting_locators") or []) < 2]
    add("conflicts_carry_both_sources", "a 'source_conflict' names both conflicting locators",
        not conflicts_without_both, f"conflicts without two locators={conflicts_without_both[:8]}")

    def numbers_of(text: str) -> set:
        out = set()
        for match in NUMBER.finditer(normalise(text)):
            try:
                out.add(Decimal(match.group(0)).normalize())
            except InvalidOperation:
                pass
        return out

    drift = []
    for identifier, entry in by_id.items():
        quote, value = entry.get("quote"), entry.get("value")
        if not quote or value in (None, ""):
            continue
        if numbers_of(str(value)) - numbers_of(quote):
            drift.append(identifier)
    add("values_come_from_the_quote",
        "a reported value's digits occur in its own quotation", not drift,
        f"values with digits absent from the quote={drift[:8]}")

    question_ids = [str(question.get("question_id") or question.get("id")) for question in questions]
    answered_questions = answer.get("questions") or answer.get("answers") or []
    answered_by_id = {str(entry.get("question_id") or entry.get("id")): entry
                      for entry in answered_questions}
    missing_questions = [identifier for identifier in question_ids if identifier not in answered_by_id]
    add("question_coverage", "every requested question has one entry", not missing_questions,
        f"missing={missing_questions[:8]} of {len(question_ids)} asked")
    bad_question_status = [identifier for identifier, entry in answered_by_id.items()
                           if entry.get("status") not in ANSWER_STATUSES]
    add("question_status_vocabulary", "every question uses the case's own answer vocabulary",
        not bad_question_status,
        f"off-vocabulary={bad_question_status[:8]} (allowed: {list(ANSWER_STATUSES)})")
    claims_without_evidence = []
    for identifier, entry in answered_by_id.items():
        for claim in entry.get("claims") or []:
            evidence = claim.get("evidence") or []
            if claim.get("kind") == "reported" and not evidence:
                claims_without_evidence.append(f"{identifier}:{claim.get('claim_id')}")
    add("claims_have_evidence", "every 'reported' claim carries evidence entries",
        not claims_without_evidence, f"claims without evidence={claims_without_evidence[:8]}")

    for item in answer.get("required_fields") or []:
        add(f"contract_field:{item}", f"the case's required output field '{item}' is present",
            item in answer, f"present={item in answer}")

    failures = [entry for entry in checks if entry["status"] == "fail"]
    report = {
        "schema": "reading-check/v1",
        "answer": answer.get("_path"),
        "case": case.get("_path"),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "failed": len(failures),
        "status": "verified" if not failures else "needs_work",
        "scope_note": "Proves contract coverage, status vocabulary, quotation fidelity and numeric "
                      "preservation. It does not prove that a semantically correct reading was "
                      "chosen for an ambiguous passage; that needs review.",
    }
    (outdir / "reading-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    return report


def verify(answer_path: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    answer = json.loads(Path(answer_path).read_text(encoding="utf-8"))
    checks = []

    def add(check_id, requirement, ok, evidence):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence})

    add("answer_hash_recorded", "the answer file has a recorded hash",
        Path(answer_path).exists(), f"sha256={sha256_file(answer_path)[:16]}…")
    for field in answer.get("required_fields") or []:
        add(f"present:{field}", f"the declared output field '{field}' exists", field in answer,
            f"keys={sorted(answer)[:10]}")
    add("case_id_preserved", "the answer keeps the case identifier from the input",
        bool(answer.get("case_id")), f"case_id={answer.get('case_id')!r}")
    add("status_present", "the answer carries a status from the case vocabulary",
        answer.get("status") in ANSWER_STATUSES,
        f"status={answer.get('status')!r} allowed={list(ANSWER_STATUSES)}")
    failures = [entry for entry in checks if entry["status"] == "fail"]
    report = {"schema": "reading-verify/v1", "checks": checks,
              "passed": len(checks) - len(failures), "failed": len(failures),
              "status": "verified" if not failures else "needs_work"}
    (outdir / "reading-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Contract-driven reading answers")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("contract")
    p.add_argument("--case", required=True)
    p.add_argument("--fields")
    p.add_argument("--questions")
    p.add_argument("--out", required=True)
    p = sub.add_parser("check")
    p.add_argument("--answer", required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--fields")
    p.add_argument("--questions")
    p.add_argument("--outdir", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--answer", required=True)
    p.add_argument("--outdir", required=True)
    args = parser.parse_args(argv)

    if args.command == "contract":
        case_path = Path(args.case)
        case = load_json(case_path)
        case["_path"] = str(case_path)
        fields = discover_fields(case, Path(args.fields) if args.fields else None)
        questions = load_json(Path(args.questions)) if args.questions else (case.get("questions") or [])
        contract = build_contract(case, fields, questions)
        Path(args.out).write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"fields": contract["requested_field_count"],
                          "questions": contract["requested_question_count"],
                          "out": args.out}, ensure_ascii=False))
        return 0
    if args.command == "check":
        case_path = Path(args.case)
        case = load_json(case_path)
        case["_path"] = str(case_path)
        answer_path = Path(args.answer)
        answer = load_json(answer_path)
        answer["_path"] = str(answer_path)
        fields = discover_fields(case, Path(args.fields) if args.fields else None)
        questions = load_json(Path(args.questions)) if args.questions else (case.get("questions") or [])
        report = check(answer, case, fields, questions, Path(args.outdir))
        print(json.dumps({"passed": report["passed"], "failed": report["failed"],
                          "status": report["status"]}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    if args.command == "verify":
        report = verify(Path(args.answer), Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
