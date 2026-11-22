"""Question-shaped literature answers: schedule the questions, then prove every claim carries evidence.

The reading tasks share a demand, but not the same shape. This channel publishes a question-shaped
contract: one entry per question (`answered` / `partial` / `insufficient_evidence` / `input_error`),
claims split into `reported` and `inferred`, each evidence entry carrying the paper identifier, the
paragraph id and a verbatim quotation, plus a stated reading range. That shape is published, so it is
checkable - and the two ways such a document usually fails are mechanical:

* a question that never appears, so a gap reads as coverage (the statement says an omitted question
  is not allowed, and that a status label alone must not be taken as an answer);
* a quotation that is not actually in the supplied material, or a reported number whose own
  quotation does not carry it - the fabricated-evidence case, which scores zero.

    plan      read the case input and emit one scheduled entry per question, the paragraph
              inventory quotations must resolve against, the identity fields to echo, and the exact
              field list the result has to carry
    preflight audit a result document against that contract: identity echo, one entry per question,
              the status vocabulary, claim/evidence pairing, verbatim quotations, reported numbers
              traceable to their own quotation, and a reading range whose unread parts carry reasons
    mirror    write the same result to the second published path (`/app/answers.json`) when the
              image allows it, and report which paths now carry the artifact

Commands
--------
plan      --input DIR|FILE [--questions FILE] [--out FILE]
preflight --result FILE --case FILE [--questions FILE] [--outdir DIR]
mirror    --result FILE [--also PATH] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ANSWER_STATUSES = ("answered", "partial", "insufficient_evidence", "input_error")
CLAIM_KINDS = ("reported", "inferred")
IDENTITY_FIELDS = ("case_id", "paper_id", "material_version")
PARAGRAPH_KEYS = ("paragraphs", "passages", "sections", "body", "materials", "corpus", "content")
QUESTION_KEYS = ("questions", "question_list", "question_set", "items")
# Keys whose text is an instruction or a prompt rather than supplied material: a quotation from one
# of these is not evidence about the paper, so they never enter the quotable text.
EXCLUDED_KEYS = ("questions", "question_list", "question_set", "target_fields", "task",
                 "instructions", "instruction", "prompt")
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)*(?![\w.])")
DEFAULT_ANSWERS = "/app/answers.json"


def normalise(text: object) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def identifier(entry: object, keys=("paragraph_id", "id", "name", "key")) -> str | None:
    if not isinstance(entry, dict):
        return None
    for key in keys:
        value = entry.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(value).strip()
    return None


def entry_text(entry: object) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for key in ("text", "content", "body", "paragraph", "sentence", "quote"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return ""


def find_list(blob: dict, keys: tuple) -> list:
    """The first list under one of `keys`, at the top level or one level down (case v3 nests)."""
    for key in keys:
        value = blob.get(key)
        if isinstance(value, list) and value:
            return value
    for key in ("case", "paper", "material", "package", "input", "data"):
        nested = blob.get(key)
        if isinstance(nested, dict):
            for probe in keys:
                value = nested.get(probe)
                if isinstance(value, list) and value:
                    return value
    return []


def question_id(question: object) -> str | None:
    for key in ("question_id", "id", "qid", "name"):
        if isinstance(question, dict) and question.get(key) is not None:
            value = str(question[key]).strip()
            if value:
                return value
    if isinstance(question, dict):
        for key in ("text", "question", "prompt"):
            if isinstance(question.get(key), str):
                return "q" + re.sub(r"\W+", "-", normalise(question[key]))[:40].strip("-").lower()
    return None


def question_text(question: object) -> str:
    if isinstance(question, dict):
        for key in ("text", "question", "prompt", "title"):
            if isinstance(question.get(key), str) and question[key].strip():
                return question[key]
    return "" if question is None else str(question)


def paragraph_inventory(blob: dict) -> tuple[dict, bool]:
    """{paragraph_id: text} plus whether the ids are the case's own or synthesised for the report."""
    entries = find_list(blob, PARAGRAPH_KEYS)
    if not entries:
        for key in ("paragraphs", "passages", "sections"):
            if isinstance(blob.get(key), dict):
                return ({str(k): normalise(v) for k, v in blob[key].items()
                         if isinstance(v, (str, dict))}, True)
        return {}, False
    declared = all(isinstance(e, dict) and identifier(e) for e in entries)
    inventory: dict[str, str] = {}
    for index, entry in enumerate(entries, start=1):
        key = identifier(entry) if declared else f"p{index:02d}"
        inventory[str(key)] = normalise(entry_text(entry))
    return inventory, declared


def material_text(blob: dict, questions: list) -> str:
    """Everything a quotation may come from: the material, never the questions or the instructions.

    A quotation copied out of the question text is not evidence, so the question list and the task
    instruction are removed before the text is flattened. What remains is what the paper supplied.
    """
    def strip(value: object) -> object:
        if isinstance(value, dict):
            out = {}
            for key, item in value.items():
                lowered = str(key).lower()
                if lowered in EXCLUDED_KEYS:
                    continue
                out[key] = strip(item)
            return out
        if isinstance(value, list):
            return [strip(item) for item in value]
        return value

    cleaned = strip(blob)
    chunks: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(cleaned)
    return normalise(" \n ".join(chunks))


def numbers_in(text: str) -> list[str]:
    return [match.group(0).replace(",", "") for match in NUMBER.finditer(str(text))]


def subject_from(blob: dict, paragraphs: dict, questions: list) -> dict:
    identity = {}
    for field in IDENTITY_FIELDS:
        value = blob.get(field)
        if value is None:
            for key in ("case", "paper", "package", "material", "input"):
                nested = blob.get(key)
                if isinstance(nested, dict) and nested.get(field) is not None:
                    value = nested[field]
                    break
        if isinstance(value, dict):
            value = value.get("version") or value.get("name")
        identity[field] = None if value is None else str(value)
    return {
        "identity": identity,
        "paragraph_count": len(paragraphs),
        "question_ids": [q for q in (question_id(q) for q in questions) if q],
    }


def resolve_input(target: Path) -> tuple[Path | None, Path | None, list[str]]:
    """A submission directory or a single case file -> (case file, question file, notes)."""
    notes: list[str] = []
    if target.is_dir():
        case = next((target / n for n in ("case.json", "case-v3.json", "input.json")
                     if (target / n).exists()), None)
        questions = next((target / n for n in ("questions.json", "question_list.json")
                          if (target / n).exists()), None)
        if case is None:
            candidates = sorted(p for p in target.glob("*.json") if p.name != "resources.yaml")
            if candidates:
                case = candidates[0]
                notes.append(f"no case.json; read {case.name} as the case")
            else:
                notes.append("no case file found in the input directory")
        if questions is None:
            notes.append("no separate question file; questions read from the case itself")
        return case, questions, notes
    if target.exists():
        return target, None, ["input is a single file; questions read from the case itself"]
    return None, None, [f"input path does not exist: {target}"]


def command_plan(args) -> int:
    case_path, questions_path, notes = resolve_input(Path(args.input))
    if case_path is None:
        print(json.dumps({"stage": "plan", "failed": True, "notes": notes}, ensure_ascii=False))
        return 2
    case = load_json(case_path)
    if questions_path is not None:
        payload = load_json(questions_path)
        questions = payload if isinstance(payload, list) else find_list(payload, QUESTION_KEYS)
    else:
        questions = find_list(case, QUESTION_KEYS)
    paragraphs, declared = paragraph_inventory(case)
    identity = subject_from(case, paragraphs, questions)["identity"]
    scheduled = [{"question_id": question_id(q), "text": question_text(q), "status": None,
                  "answer": None, "conditions": [], "claims": [], "unanswered_parts": []}
                 for q in questions]
    plan = {
        "schema": "literature-qa-plan/v1",
        "case_file": str(case_path),
        "question_file": str(questions_path) if questions_path else None,
        "notes": notes,
        "identity": identity,
        "result_path": args.result,
        "alternate_result_path": args.alternate,
        "answer_statuses": list(ANSWER_STATUSES),
        "claim_kinds": list(CLAIM_KINDS),
        "required_fields": {
            "top_level": ["case_id", "paper_id", "material_version", "answers", "coverage"],
            "per_answer": ["question_id", "answer", "conditions", "status", "claims",
                           "unanswered_parts"],
            "per_claim": ["claim_id", "text", "kind", "evidence"],
            "per_evidence": ["paragraph_id", "quote"],
            "coverage": ["read", "unread"],
        },
        "scheduled_answers": scheduled,
        "question_count": len(scheduled),
        "paragraph_ids": list(paragraphs.keys()),
        "paragraph_ids_declared_by_case": declared,
        "material_characters": len(material_text(case, questions)),
        "instruction": (
            "Fill one entry per scheduled question, by question_id, and keep every gap in "
            "unanswered_parts rather than leaving the question out. Reported numbers must appear in "
            "their own quotation; anything derived or explained is an `inferred` claim. Write the "
            "result to result_path and then run preflight."),
    }
    if not scheduled:
        plan["notes"] = plan["notes"] + ["no questions found in the input; check the case shape"]
    write_json(Path(args.out), plan)
    print(json.dumps({"stage": "plan", "questions": len(scheduled), "paragraphs": len(paragraphs),
                      "paragraph_ids_declared_by_case": declared, "identity": identity,
                      "material_characters": plan["material_characters"], "out": args.out,
                      "notes": notes}, ensure_ascii=False))
    return 0 if scheduled else 2


def command_preflight(args) -> int:
    case = load_json(Path(args.case))
    if args.questions:
        payload = load_json(Path(args.questions))
        questions = payload if isinstance(payload, list) else find_list(payload, QUESTION_KEYS)
    else:
        questions = find_list(case, QUESTION_KEYS)
    result_path = Path(args.result)
    answered = load_json(result_path)
    paragraphs, declared = paragraph_inventory(case)
    material = material_text(case, questions)
    subject = subject_from(case, paragraphs, questions)
    expected_ids = subject["question_ids"]

    checks: list[dict] = []
    failures: list[str] = []

    def check(check_id: str, rule: str, ok: bool, detail: str = "") -> bool:
        checks.append({"id": check_id, "rule": rule, "result": "pass" if ok else "fail",
                       "detail": detail})
        if not ok:
            failures.append(check_id)
        return ok

    if isinstance(answered.get("_skeleton"), bool) and answered["_skeleton"]:
        check("result.not_skeleton", "a skeleton is not a result", False,
              "the file declares _skeleton: true")
    if isinstance(answered, list):
        answered = {"answers": answered}

    check("material.supplied", "the case carries material to quote from", bool(material),
          f"{len(material)} characters after removing questions and instructions")

    for field in IDENTITY_FIELDS:
        expected = subject["identity"].get(field)
        actual = answered.get(field)
        if expected is None:
            check(f"identity.{field}", f"{field} echoed when the input declares it", True,
                  "the input does not declare it; nothing to echo")
        else:
            check(f"identity.{field}", f"{field} matches the input",
                  str(actual).strip() == expected, f"input={expected!r} result={actual!r}")

    answers = answered.get("answers")
    if not check("answers.present", "answers[] present", isinstance(answers, list),
                 f"type={type(answers).__name__}"):
        return finish(checks, failures, result_path, args, subject, declared, 0)

    seen: dict[str, int] = {}
    for index, entry in enumerate(answers):
        key = question_id(entry) if isinstance(entry, dict) else None
        if key:
            seen.setdefault(key, 0)
            seen[key] += 1
    missing = [q for q in expected_ids if q not in seen]
    duplicated = [q for q, n in seen.items() if n > 1]
    unknown = [q for q in seen if expected_ids and q not in expected_ids]
    check("answers.every_question_once", "one entry per supplied question, none omitted",
          not missing and not duplicated,
          f"missing={missing} duplicated={duplicated}")
    check("answers.no_unknown_question", "no entry for a question the case does not ask",
          not unknown, f"unknown={unknown}")

    for index, entry in enumerate(answers):
        label = question_id(entry) if isinstance(entry, dict) else f"answers[{index}]"
        if not isinstance(entry, dict):
            check(f"answer.{label}.shape", "each answer is an object", False,
                  f"type={type(entry).__name__}")
            continue
        status = entry.get("status")
        check(f"answer.{label}.status", "status from the published vocabulary",
              status in ANSWER_STATUSES, f"status={status!r}")
        check(f"answer.{label}.text", "a result document is not a status label", bool(
            normalise(entry.get("answer") or "")), f"answer={normalise(entry.get('answer'))[:60]!r}")
        check(f"answer.{label}.conditions", "conditions is a list",
              isinstance(entry.get("conditions"), list))
        gaps = entry.get("unanswered_parts")
        check(f"answer.{label}.unanswered_parts", "unanswered_parts is always present",
              isinstance(gaps, list), f"type={type(gaps).__name__}")
        if status in ANSWER_STATUSES and status != "answered":
            check(f"answer.{label}.gap_declared",
                  "a partial answer names the parts it did not answer",
                  isinstance(gaps, list) and len(gaps) > 0, f"unanswered_parts={gaps!r}")
        if isinstance(gaps, list):
            for position, gap in enumerate(gaps):
                reason = gap.get("reason") if isinstance(gap, dict) else gap
                check(f"answer.{label}.gap_reason[{position}]", "every gap carries a reason",
                      bool(normalise(reason or "")), f"gap={gap!r}")

        claims = entry.get("claims")
        if not check(f"answer.{label}.claims", "claims is a list", isinstance(claims, list)):
            continue
        claim_ids: dict[str, int] = {}
        for c_index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                check(f"claim.{label}.{c_index}.shape", "each claim is an object", False,
                      f"type={type(claim).__name__}")
                continue
            cid = claim.get("claim_id")
            key = str(cid).strip() if cid is not None else f"{label}#{c_index}"
            claim_ids.setdefault(key, 0)
            claim_ids[key] += 1
            check(f"claim.{label}.{key}.id", "claim_id present and unique inside its answer",
                  bool(normalise(cid or "")) and claim_ids[key] == 1, f"claim_id={cid!r}")
            check(f"claim.{label}.{key}.text", "claim text present",
                  bool(normalise(claim.get("text") or "")),
                  f"text={normalise(claim.get('text'))[:60]!r}")
            kind = claim.get("kind")
            check(f"claim.{label}.{key}.kind", "kind is reported or inferred",
                  kind in CLAIM_KINDS, f"kind={kind!r}")
            evidence = claim.get("evidence")
            if not check(f"claim.{label}.{key}.evidence",
                         "every claim carries at least one evidence entry",
                         isinstance(evidence, list) and len(evidence) > 0,
                         f"evidence={evidence!r}"):
                continue
            quotes: list[str] = []
            for e_index, item in enumerate(evidence):
                if not isinstance(item, dict):
                    check(f"evidence.{label}.{key}.{e_index}.shape", "each evidence is an object",
                          False, f"type={type(item).__name__}")
                    continue
                pid = identifier(item, ("paragraph_id", "paragraph", "locator"))
                check(f"evidence.{label}.{key}.{e_index}.paragraph_id",
                      "every evidence entry carries a paragraph id", bool(normalise(pid or "")),
                      f"paragraph_id={pid!r}")
                if pid and declared:
                    check(f"evidence.{label}.{key}.{e_index}.paragraph_id_known",
                          "the paragraph id exists in the supplied material",
                          str(pid).strip() in paragraphs, f"paragraph_id={pid!r}")
                quote = normalise(item.get("quote") or "")
                check(f"evidence.{label}.{key}.{e_index}.quote", "every evidence entry carries a quote",
                      bool(quote), f"quote={quote[:60]!r}")
                if quote:
                    check(f"evidence.{label}.{key}.{e_index}.quote_verbatim",
                          "the quote is actually in the supplied material",
                          quote in material, f"quote={quote[:80]!r}")
                    quotes.append(quote)
            if kind == "reported" and quotes:
                joined = " ".join(quotes)
                untraceable = [n for n in numbers_in(claim.get("text") or "")
                               if n not in joined.replace(",", "")]
                check(f"claim.{label}.{key}.numbers_in_quote",
                      "a reported number appears in its own quotation",
                      not untraceable,
                      f"untraceable={untraceable}; move a derived value into an inferred claim")

    coverage = answered.get("coverage")
    if check("coverage.present", "coverage present", isinstance(coverage, dict),
             f"type={type(coverage).__name__}"):
        read = coverage.get("read") or coverage.get("sections_read")
        unread = coverage.get("unread") or coverage.get("sections_unread") or []
        check("coverage.read", "the reading range names what was read",
              isinstance(read, list) and len(read) > 0, f"read={read!r}")
        check("coverage.unread", "the reading range names what was not read, as a list",
              isinstance(unread, list), f"type={type(unread).__name__}")
        if isinstance(unread, list):
            for position, item in enumerate(unread):
                reason = item.get("reason") if isinstance(item, dict) else item
                check(f"coverage.unread_reason[{position}]", "every unread part carries a reason",
                      bool(normalise(reason or "")), f"unread={item!r}")
    return finish(checks, failures, result_path, args, subject, declared, len(answers))


def finish(checks, failures, result_path, args, subject, declared, count) -> int:
    report = {
        "schema": "literature-qa-preflight/v1",
        "result_file": str(result_path),
        "answers_seen": count,
        "paragraph_ids_declared_by_case": declared,
        "paragraph_count": subject["paragraph_count"],
        "checks": checks,
        "failed_checks": failures,
        "status": "verified" if not failures else "needs_repair",
    }
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "preflight.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    print(json.dumps({"answers": count, "checks": len(checks), "failed_checks": failures,
                      "status": report["status"]}, ensure_ascii=False))
    return 0 if not failures else 3


def command_mirror(args) -> int:
    source = Path(args.result)
    mirrored: list[dict] = []
    skipped: list[dict] = []
    for target in [Path(args.also)]:
        if target.resolve() == source.resolve():
            skipped.append({"path": str(target), "reason": "same file as the result"})
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            mirrored.append({"path": str(target), "bytes": target.stat().st_size})
        except OSError as exc:
            skipped.append({"path": str(target), "reason": f"{type(exc).__name__}: {exc}"})
    report = {"schema": "literature-qa-mirror/v1", "source": str(source),
              "mirrored": mirrored, "skipped": skipped,
              "note": ("both published result paths now carry the same document; a path that could "
                       "not be written is reported rather than assumed")}
    if args.out:
        write_json(Path(args.out), report)
    print(json.dumps({"mirrored": [m["path"] for m in mirrored],
                      "skipped": [s["path"] for s in skipped]}, ensure_ascii=False))
    return 0 if mirrored or not skipped else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Question-shaped literature answers")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="schedule the questions and the field list of the result")
    p.add_argument("--input", required=True, help="the submission input directory or case file")
    p.add_argument("--questions", help="explicit question list when it is a separate file")
    p.add_argument("--result", default="/app/output/result.json")
    p.add_argument("--alternate", default=DEFAULT_ANSWERS)
    p.add_argument("--out", default="/app/work/qa-plan.json")

    p = sub.add_parser("preflight", help="audit a result document against the published contract")
    p.add_argument("--result", required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--questions")
    p.add_argument("--outdir", required=True)

    p = sub.add_parser("mirror", help="write the same result to the second published path")
    p.add_argument("--result", required=True)
    p.add_argument("--also", default=DEFAULT_ANSWERS)
    p.add_argument("--out")

    args = parser.parse_args(argv)
    if args.command == "plan":
        return command_plan(args)
    if args.command == "preflight":
        return command_preflight(args)
    return command_mirror(args)


if __name__ == "__main__":
    sys.exit(main())
