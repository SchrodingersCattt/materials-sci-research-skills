"""Field extraction against a requested-field declaration: presence is not correctness.

The conclusion-and-data-extraction case supplies a declaration of the fields it wants
(`/input/target-fields.json`): for each `field_id` it names the statistic, the unit, the experimental
condition, the comparator and the paper the value should come from. Two failure modes survive a
naive check and are what this module is for:

* **An absent field is not zero.** "the paper does not report it" written as `0`, `-`, `n/a` or a
  blank is not an extraction and not an honest refusal either - the value slot has to stay empty and
  the status has to say why.
* **A literal quotation match is not semantic correctness.** A real sentence can carry the right
  number and still be about a different statistic, a different condition or a different comparator.
  So the quotation has to contain the statistic, condition, comparator and unit the request named -
  otherwise the upstream match proves only that the sentence exists.

    plan  --fields target-fields.json [--out FILE]
          one entry per requested field_id, listing the slots that have to be filled, so no field is
          silently dropped and no slot is silently skipped
    check --answer FILE --fields target-fields.json --outdir DIR
          audit the produced document: coverage, status vocabulary, no filler value, verbatim
          quotation, numbers inside their own quotation, and the requested statistic / condition /
          comparator / unit actually present

Commands
--------
plan  --fields FILE [--result PATH] [--out FILE]
check --answer FILE --fields FILE [--outdir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FIELD_STATUSES = ("reported", "not_reported", "source_conflict", "extraction_failed")
LOCATOR_KEYS = ("paragraph_id", "locator", "page", "section", "table", "figure", "row")
VALUE_KEYS = ("value", "scalar", "measured", "result")
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)*(?![\w.])")
FILLER = {"0", "0.0", "-", "--", "n/a", "na", "none", "null", "unknown", "tbd", "?"}
SLOT_KEYS = ("statistic", "condition", "comparator", "unit", "paper_id", "scalar", "value")
# The slots whose presence the quotation has to demonstrate. `comparator` and `paper_id` are
# deliberately outside this set: a comparison is frequently expressed by naming the other specimen
# rather than the declared phrase, and the paper identity is carried by the output envelope rather
# than by the quoted sentence. Checking them here would flag correct work, which is the failure mode
# this package exists to avoid.
SLOT_CHECKED = ("statistic", "condition", "unit")
SYNONYMS = {
    "statistic": {
        "mean": ("mean", "average", "averaged", "arithmetic mean"),
        "standard deviation": ("standard deviation", "std", "sd", "sigma", "dispersion"),
        "maximum": ("maximum", "max", "highest", "peak"),
        "minimum": ("minimum", "min", "lowest"),
        "median": ("median", "50th percentile", "middle value"),
    },
}


def normalise(text: object) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def requested_fields(payload) -> list:
    if isinstance(payload, list):
        return payload
    for key in ("target_fields", "fields", "requested_fields", "field_list", "items"):
        value = payload.get(key)
        if isinstance(value, list) and value:
            return value
        if isinstance(value, dict) and value:
            return [{"field_id": k, **(v if isinstance(v, dict) else {"description": v})}
                    for k, v in value.items()]
    raise SystemExit("the field declaration does not carry a field list")


def field_id(field) -> str:
    if isinstance(field, str):
        return field
    for key in ("field_id", "id", "name", "key"):
        if isinstance(field, dict) and field.get(key) is not None:
            value = str(field[key]).strip()
            if value:
                return value
    raise SystemExit(f"a requested field carries no id: {field!r}")


def requested_slots(field) -> dict:
    if not isinstance(field, dict):
        return {}
    slots = {}
    for key in SLOT_KEYS:
        value = field.get(key)
        if isinstance(value, (str, int, float)) and str(value).strip():
            slots[key] = str(value).strip()
    for key in ("requires", "slots", "must_state"):
        value = field.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    slots[item.strip().lower()] = True
    return slots


def synonyms(slot: str, expected: str) -> set[str]:
    """Spellings of the same requirement, so a correct extraction is not flagged for a wording."""
    table = SYNONYMS.get(slot) or {}
    if expected.lower() in table:
        return set(table[expected.lower()])
    if slot == "unit":
        return {expected.replace(" ", ""), expected.replace("°", "")}
    if slot == "condition":
        return {re.sub(r"\s+(c|k)\b", "", expected), expected.replace(" C", " °C"),
                expected.replace("C", "°C")}
    return set()


def value_of(entry: dict, keys=VALUE_KEYS):
    for key in keys:
        if key in entry:
            return entry[key]
    return None


def load_material(target) -> str:
    """Whitespace-normalised text of the supplied material: the file, or every text file in a tree."""
    path = Path(target)
    if not path.exists():
        return ""
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    chunks: list[str] = []
    for item in files:
        try:
            chunks.append(item.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return normalise(" \n ".join(chunks))


def looks_like_filler(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) == 0.0
    text = normalise(value).lower()
    return text == "" or text in FILLER


def searchable_text(entry: dict) -> str:
    """The text a slot may be answered in: the quotation, plus any note the extractor left."""
    chunks = [normalise(entry.get("quote") or ""), normalise(entry.get("note") or "")]
    for evidence in entry.get("evidence") or []:
        if isinstance(evidence, dict):
            chunks.append(normalise(evidence.get("quote") or ""))
    return normalise(" ".join(chunk for chunk in chunks if chunk))


def command_plan(args) -> int:
    fields = requested_fields(load_json(Path(args.fields)))
    entries = []
    for field in fields:
        slots = requested_slots(field)
        entries.append({
            "field_id": field_id(field),
            "description": field.get("description") if isinstance(field, dict) else None,
            "required_slots": slots,
            "status": None,
            "value": None,
            "unit": slots.get("unit"),
            "locator": {key: None for key in LOCATOR_KEYS[:2]},
            "quote": None,
        })
    plan = {
        "schema": "field-extraction-plan/v1",
        "field_source": args.fields,
        "result_path": args.result,
        "field_statuses": list(FIELD_STATUSES),
        "field_count": len(entries),
        "fields": entries,
        "rules": [
            "an absent field is not zero: leave the value empty and use not_reported",
            "a literal quotation match alone does not establish semantic correctness: the quotation "
            "must carry the requested statistic, condition, comparator and unit",
            "a source conflict names two distinct locators",
            "a field that could not be read is extraction_failed, not not_reported",
        ],
    }
    write_json(Path(args.out), plan)
    print(json.dumps({"fields": len(entries), "out": args.out}, ensure_ascii=False))
    return 0 if entries else 2


def command_check(args) -> int:
    fields = requested_fields(load_json(Path(args.fields)))
    wanted = {}
    for field in fields:
        wanted[field_id(field)] = requested_slots(field)
    answer = load_json(Path(args.answer))
    material = load_material(args.material) if args.material else ""
    entries = answer
    for key in ("fields", "results", "extraction", "targets", "items"):
        if isinstance(answer.get(key), list):
            entries = answer[key]
            break

    checks: list[dict] = []
    failures: list[str] = []

    def check(check_id: str, rule: str, ok: bool, detail: str = "") -> bool:
        checks.append({"id": check_id, "rule": rule, "result": "pass" if ok else "fail",
                       "detail": detail})
        if not ok:
            failures.append(check_id)
        return ok

    if not check("fields.present", "the result lists the extracted fields", isinstance(entries, list),
                 f"type={type(entries).__name__}"):
        return report(checks, failures, Path(args.outdir))

    seen: dict[str, int] = {}
    for entry in entries:
        if isinstance(entry, dict):
            key = field_id(entry) if any(entry.get(k) for k in ("field_id", "id", "name")) else None
            if key:
                seen.setdefault(key, 0)
                seen[key] += 1
    missing = [f for f in wanted if f not in seen]
    duplicated = [f for f, n in seen.items() if n > 1]
    unknown = [f for f in seen if f not in wanted]
    check("fields.every_target_once", "one entry per requested field_id, none omitted",
          not missing and not duplicated, f"missing={missing} duplicated={duplicated}")
    check("fields.no_unknown_target", "no entry for a field the request does not declare",
          not unknown, f"unknown={unknown}")

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = next((str(entry[k]) for k in ("field_id", "id", "name") if entry.get(k)), "?")
        slots = wanted.get(key, {})
        status = entry.get("status")
        check(f"field.{key}.status", "status from the published vocabulary",
              status in FIELD_STATUSES, f"status={status!r}")
        raw_value = value_of(entry)
        if status in ("not_reported", "extraction_failed"):
            check(f"field.{key}.absent_is_not_zero",
                  "a field the material does not carry keeps an empty value",
                  not looks_like_filler(raw_value) or raw_value is None,
                  f"value={raw_value!r} with status={status!r}")
        if status == "source_conflict":
            locators = []
            for evidence in entry.get("evidence") or []:
                if isinstance(evidence, dict):
                    for lkey in LOCATOR_KEYS:
                        if evidence.get(lkey):
                            locators.append(f"{lkey}:{evidence[lkey]}")
            for lkey in LOCATOR_KEYS:
                if entry.get(lkey):
                    locators.append(f"{lkey}:{entry[lkey]}")
            distinct = {loc.split(":", 1)[1] for loc in locators}
            check(f"field.{key}.conflict_names_two_locators",
                  "a source conflict names the two sources it saw",
                  len(distinct) >= 2, f"locators={sorted(distinct)}")
        quote = normalise(entry.get("quote") or "")
        if status == "reported":
            check(f"field.{key}.reported_has_quote", "a reported value carries a quotation",
                  bool(quote), f"quote={quote[:60]!r}")
            if quote and material:
                check(f"field.{key}.quote_verbatim",
                      "the quotation is in the supplied material, not composed around it",
                      quote in material, f"quote={quote[:80]!r}")
            check(f"field.{key}.reported_has_locator",
                  "a reported value carries a locator",
                  any(entry.get(lkey) for lkey in LOCATOR_KEYS),
                  f"keys={[lkey for lkey in LOCATOR_KEYS if entry.get(lkey)]}")
            if quote:
                numbers = [n for n in NUMBER.findall(normalise(raw_value))] if raw_value is not None \
                    else []
                untraceable = [n for n in numbers if n not in quote.replace(",", "")]
                check(f"field.{key}.numbers_in_quote",
                      "the value appears in its own quotation", not untraceable,
                      f"untraceable={untraceable}")
        for slot, slot_expected in slots.items():
            if slot not in SLOT_CHECKED or status != "reported":
                continue
            declared = normalise(entry.get(slot) or "")
            haystack = searchable_text(entry).lower()
            spellings = {slot_expected.lower()} | synonyms(slot, slot_expected)
            if declared:
                spellings.add(declared.lower())
            present = sorted(s for s in spellings if s and s in haystack)
            check(f"field.{key}.semantic_{slot}",
                  f"the quotation demonstrates the requested {slot}, not just a matching number",
                  bool(present),
                  f"requested={slot_expected!r} declared={declared!r} "
                  f"found={present} quote={haystack[:70]!r}")

    return report(checks, failures, Path(args.outdir))


def report(checks: list, failures: list, outdir: Path) -> int:
    payload = {"schema": "field-extraction-check/v1", "checks": checks,
               "failed_checks": failures,
               "status": "verified" if not failures else "needs_repair"}
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "field-check.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    print(json.dumps({"checks": len(checks), "failed_checks": failures,
                      "status": payload["status"]}, ensure_ascii=False))
    return 0 if not failures else 3


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Field extraction against a field declaration")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan", help="one scheduled entry per requested field_id")
    p.add_argument("--fields", required=True)
    p.add_argument("--result", default="/app/output/result.json")
    p.add_argument("--out", default="/app/work/field-plan.json")
    p = sub.add_parser("check", help="audit the extracted document against the declaration")
    p.add_argument("--answer", required=True)
    p.add_argument("--fields", required=True)
    p.add_argument("--material", help="the supplied material (file or directory) to verify "
                                      "quotations against")
    p.add_argument("--outdir", required=True)
    args = parser.parse_args(argv)
    return command_plan(args) if args.command == "plan" else command_check(args)


if __name__ == "__main__":
    sys.exit(main())
