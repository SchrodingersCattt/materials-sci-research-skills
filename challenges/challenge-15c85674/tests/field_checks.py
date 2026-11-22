"""True positive and true negative controls for scripts/field_semantics.py.

The fixture is a 20-field extraction request of the size the evaluation case uses - several fields
per paper, each naming statistic, unit, condition and comparator - because the two failures this
guards against only show up when the fields differ from one another in those slots.

Each planted defect must be caught, the compliant extraction must pass, and the checks that are
about precision (an absent field is not a zero, a quoted number is not a semantic match) must fail on
exactly that one condition.

    python tests/field_checks.py --workdir work/field-checks
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "field_semantics.py"

PAPERS = ["p-a", "p-b", "p-c"]
STATISTICS = ["mean", "standard deviation", "maximum", "minimum", "median"]
CONDITIONS = ["480 C ageing", "room temperature", "as-cast", "quenched"]
UNITS = ["MPa", "HV", "GPa", "%"]
COMPARATORS = ["control specimen", "as-cast specimen", "supplier datasheet"]


def build_fields() -> list[dict]:
    fields = []
    for index in range(20):
        fields.append({
            "field_id": f"F{index + 1:02d}",
            "paper_id": PAPERS[index % len(PAPERS)],
            "statistic": STATISTICS[index % len(STATISTICS)],
            "unit": UNITS[index % len(UNITS)],
            "condition": CONDITIONS[index % len(CONDITIONS)],
            "comparator": COMPARATORS[index % len(COMPARATORS)],
            "description": f"value {index + 1} of the campaign table",
        })
    return fields


def quote_for(index: int, value: str) -> str:
    """A realistically long sentence that carries every slot the request names."""
    field = build_fields()[index]
    return (f"Under the {field['condition']} condition the {field['statistic']} of the "
            f"{field['comparator']} was {value} with an expanded uncertainty of 4 "
            f"{field['unit']}, measured on three specimens in the same campaign.")


def compliant_extraction() -> dict:
    entries = []
    for index in range(20):
        field = build_fields()[index]
        if index == 17:
            entries.append({"field_id": field["field_id"], "status": "not_reported", "value": None,
                            "note": "the campaign did not record this statistic"})
            continue
        if index == 18:
            entries.append({"field_id": field["field_id"], "status": "source_conflict",
                            "value": None, "note": "table and text disagree",
                            "evidence": [{"paragraph_id": "p19-t1", "quote": quote_for(index, "312")},
                                         {"paragraph_id": "p19-b4",
                                          "quote": quote_for(index, "298")}]})
            continue
        if index == 19:
            entries.append({"field_id": field["field_id"], "status": "extraction_failed",
                            "value": None, "note": "supplementary table could not be read"})
            continue
        value = f"{200 + index}.5"
        entries.append({
            "field_id": field["field_id"], "status": "reported", "value": value,
            "unit": field["unit"], "statistic": field["statistic"],
            "condition": field["condition"], "comparator": field["comparator"],
            "paragraph_id": f"p{index + 1:02d}-b2", "quote": quote_for(index, value),
        })
    return {"case_id": "case-extraction-01", "fields": entries}


def mutate(extraction: dict, name: str) -> dict:
    payload = json.loads(json.dumps(extraction))
    site = payload["fields"][0]
    if name == "zero-for-absent":
        payload["fields"][17] = {**payload["fields"][17], "value": 0}
    elif name == "dash-for-absent":
        payload["fields"][17] = {**payload["fields"][17], "value": "-"}
    elif name == "value-not-in-quote":
        site["value"] = "999.5"
    elif name == "quote-not-verbatim":
        site["quote"] = ("Under the 480 C ageing condition the mean of the control specimen was "
                         "200.5 MPa after three specimens of the campaign were tested and the "
                         "laboratory record was countersigned by the operator on the same day.")
    elif name == "statistic-mismatch":
        site["quote"] = ("Under the 480 C ageing condition the maximum of the control specimen was "
                         "200.5 MPa with an expanded uncertainty of 4 MPa, measured on three "
                         "specimens in the same campaign.")
    elif name == "condition-missing":
        site["quote"] = ("The mean of the control specimen was 200.5 MPa with an expanded "
                         "uncertainty of 4 MPa, measured on three specimens in the same campaign.")
    elif name == "unit-missing":
        site["quote"] = ("Under the 480 C ageing condition the mean of the control specimen was "
                         "200.5 with an expanded uncertainty of 4, measured on three specimens.")
    elif name == "conflict-one-source":
        payload["fields"][18]["evidence"] = [payload["fields"][18]["evidence"][0]]
    elif name == "status-invented":
        site["status"] = "mostly_reported"
    elif name == "field-omitted":
        payload["fields"] = [f for f in payload["fields"] if f["field_id"] != "F07"]
    elif name == "no-locator":
        site.pop("paragraph_id")
    else:
        raise KeyError(name)
    return payload


PLANTS = {
    "zero-for-absent": ("field.F18.absent_is_not_zero", True),
    "dash-for-absent": ("field.F18.absent_is_not_zero", True),
    "value-not-in-quote": ("field.F01.numbers_in_quote", True),
    "quote-not-verbatim": ("field.F01.quote_verbatim", True),
    # strict = the defect must fail on exactly one check id. The three slot mutations below rewrite
    # the sentence, so they legitimately fail the verbatim check as well.
    "statistic-mismatch": ("field.F01.semantic_statistic", False),
    "condition-missing": ("field.F01.semantic_condition", False),
    "unit-missing": ("field.F01.semantic_unit", False),
    "conflict-one-source": ("field.F19.conflict_names_two_locators", True),
    "status-invented": ("field.F01.status", True),
    "field-omitted": ("fields.every_target_once", True),
    "no-locator": ("field.F01.reported_has_locator", True),
}


def run_engine(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ENGINE), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(cwd))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default=str(ROOT / "work" / "field-checks"))
    args = parser.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    fields_path = work / "target-fields.json"
    fields_path.write_text(
        json.dumps({"case_id": "case-extraction-01", "target_fields": build_fields()},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    # the material the quotations must come from: one text file per paper, of realistic length
    material_dir = work / "material"
    material_dir.mkdir(parents=True, exist_ok=True)
    for paper in PAPERS:
        body = [f"# {paper}"] + [quote_for(index, f"{200 + index}.5") for index in range(20)
                                 if index < 17 and build_fields()[index]["paper_id"] == paper]
        (material_dir / f"{paper}.md").write_text("\n\n".join(body), encoding="utf-8")
    # the source-conflict pair is quoted out of the same material
    conflict = material_dir / "p-c.md"
    conflict.write_text(conflict.read_text(encoding="utf-8") + "\n\n" +
                        quote_for(18, "312") + "\n\n" + quote_for(18, "298"), encoding="utf-8")

    failures: list[str] = []
    checks: list[dict] = []

    def record(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"id": check_id, "result": "pass" if ok else "fail", "detail": detail})
        if not ok:
            failures.append(f"{check_id}: {detail}")

    plan_path = work / "field-plan.json"
    plan_run = run_engine(["plan", "--fields", str(fields_path), "--out", str(plan_path)], work)
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {}
    record("plan.runs", plan_run.returncode == 0, f"rc={plan_run.returncode}")
    record("plan.count", plan.get("field_count") == 20, f"field_count={plan.get('field_count')}")
    record("plan.slots", all(entry.get("required_slots") for entry in plan.get("fields", [])),
           "every scheduled field lists the slots it must fill")

    good_path = work / "extraction-good.json"
    good_path.write_text(json.dumps(compliant_extraction(), ensure_ascii=False, indent=1),
                         encoding="utf-8")
    good = run_engine(["check", "--answer", str(good_path), "--fields", str(fields_path),
                       "--material", str(material_dir), "--outdir", str(work / "good")], work)
    good_report = json.loads((work / "good" / "field-check.json").read_text(encoding="utf-8"))
    record("negative.compliant_passes", good.returncode == 0 and not good_report["failed_checks"],
           f"rc={good.returncode} failed={good_report['failed_checks']}")
    record("negative.checks_exercised", len(good_report["checks"]) >= 45,
           f"checks={len(good_report['checks'])}")

    for name, (expected, strict) in PLANTS.items():
        target = work / f"extraction-{name}.json"
        target.write_text(json.dumps(mutate(compliant_extraction(), name), ensure_ascii=False,
                                     indent=1), encoding="utf-8")
        run = run_engine(["check", "--answer", str(target), "--fields", str(fields_path),
                          "--material", str(material_dir), "--outdir", str(work / name)], work)
        out = work / name / "field-check.json"
        report_payload = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        failed = report_payload.get("failed_checks", [])
        record(f"positive.{name}.caught", run.returncode != 0 and expected in failed,
               f"expected {expected}; failed={failed}")
        if strict:
            record(f"positive.{name}.precise", failed == [expected],
                   f"expected only {expected}; failed={failed}")

    payload = {"verdict": "pass" if not failures else "fail", "fixture": str(fields_path),
               "checks": checks, "failures": failures}
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
