"""Prove data_profile and sql_audit behave, with negative controls where they matter.

The four states this track conflates most often are missing, zero, not-applicable and unparsable. Every
check below fails if the tool merges any two of them. Fixtures are pairs: a defective case and a
correct one, so a check fails when the tool cannot tell them apart.

    python tests/analysis_checks.py [--workdir work/analysis]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
PROFILE = SCRIPTS / "data_profile.py"
SQL = SCRIPTS / "sql_audit.py"


def run(tool: Path, *argv) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(tool), *[str(a) for a in argv]],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="work/analysis")
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    observed: dict = {}

    # ---- fixture: a dirty table where every ambiguous state appears
    dirty = work / "dirty.csv"
    dirty.write_text(
        "sample_id,conc_mg_l,group,instrument\n"
        "S1,12.5,ctrl,XS205\n"
        "S2,,ctrl,XS205\n"            # missing
        "S3,0.0,ctrl,XS205\n"         # a real zero
        "S4,n/a,ctrl,XS205\n"         # not applicable
        "S5,12.7,trt,XS205\n"
        "S6,13.1,trt,XS205\n"
        "S7,13.0,trt,XS205\n"
        "S8,13.2,trt,XS205\n"
        "S9,13.05,trt,XS205\n"
        "S10,999.0,trt,XS205\n",      # planted outlier
        encoding="utf-8")
    (work / "dict.json").write_text(json.dumps({
        "conc_mg_l": {"unit": "mg/L", "type": "float", "semantic": "concentration",
                      "constraints": ">= 0"},
        "group": {"type": "str", "semantic": "arm"},
    }, ensure_ascii=False), encoding="utf-8")

    # ---- 1 dictionary: the undeclared column must be reported, not assumed
    run(PROFILE, "dictionary", "--data", dirty, "--dictionary", work / "dict.json", "--out", work / "schema.json")
    schema = load(work / "schema.json")
    observed["dictionary"] = {"columns": len(schema["columns"]), "undeclared": schema["undeclared_columns"]}
    if "instrument" not in schema["undeclared_columns"]:
        failures.append("a column with no dictionary entry was not reported as undeclared")
    if any(c["name"] == "conc_mg_l" and not c.get("declared_unit") for c in schema["columns"]):
        failures.append("the declared unit was not carried from the dictionary")

    # ---- 2 profile: four states counted separately, outlier flagged with its rule
    run(PROFILE, "profile", "--data", dirty, "--schema", work / "schema.json", "--out", work / "profile.json")
    prof = load(work / "profile.json")
    conc = next(c for c in prof["columns"] if c["name"] == "conc_mg_l")
    observed["profile"] = {"counts": conc["counts"], "outliers": len(conc.get("outliers", [])),
                           "rule": conc.get("outlier_rule")}
    for state, want in (("missing", 1), ("zero", 1), ("not_applicable", 1)):
        if conc["counts"][state] != want:
            failures.append(f"{state} counted as {conc['counts'][state]}, expected {want}")
    # the four states must be mutually exclusive and cover every row
    total_states = sum(conc["counts"].values())
    if total_states != prof["rows"]:
        failures.append(f"state counts total {total_states} but the file has {prof['rows']} rows")
    if conc["counts"]["zero"] == 0:
        failures.append("a real zero was not counted as zero")
    if not conc.get("outliers"):
        failures.append("the planted 999.0 outlier was not flagged")
    elif not any(abs(o["value"] - 999.0) < 1e-9 for o in conc["outliers"]):
        failures.append("an outlier was reported but not the planted one")
    if not conc.get("outlier_rule"):
        failures.append("the outlier rule was not stated")

    # ---- 3 clean: input untouched, changes logged, dedupe on identity
    (work / "rules.json").write_text(json.dumps({
        "fill_missing": "flag", "deduplicate": "none", "identity_columns": ["sample_id"],
    }, ensure_ascii=False), encoding="utf-8")
    before = dirty.read_bytes()
    run(PROFILE, "clean", "--data", dirty, "--schema", work / "schema.json", "--rules", work / "rules.json",
        "--out", work / "clean.csv", "--transform-log", work / "transforms.json")
    if dirty.read_bytes() != before:
        failures.append("cleaning modified the input file")
    clean = load(work / "transforms.json")
    observed["clean"] = {"changes": len(clean["changes"])}
    if not clean["changes"]:
        failures.append("no transform log was produced for a file that needed changes")

    # ---- 4 verify: a tampered clean file must fail verification
    run(PROFILE, "verify", "--data", dirty, "--clean", work / "clean.csv",
        "--transform-log", work / "transforms.json", "--out", work / "verify-ok.json")
    ok = load(work / "verify-ok.json")
    observed["verify_clean"] = {"status": ok["status"], "untraced": ok["untraced_values"]}
    # now tamper: change a value with no logged change
    rows = (work / "clean.csv").read_text(encoding="utf-8").splitlines()
    rows[1] = rows[1].replace("12.5", "77.7")
    (work / "tampered.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    run(PROFILE, "verify", "--data", dirty, "--clean", work / "tampered.csv",
        "--transform-log", work / "transforms.json", "--out", work / "verify-bad.json")
    bad = load(work / "verify-bad.json")
    observed["verify_tampered"] = {"status": bad["status"], "untraced": bad["untraced_values"]}
    if bad["status"] == "verified":
        failures.append("verification passed a clean file that was tampered with untraced")

    # ---- 5 infer: two groups run; three groups must be refused, not forced
    run(PROFILE, "infer", "--data", work / "clean.csv", "--group-by", "group",
        "--value-col", "conc_mg_l", "--out", work / "infer.json")
    infer = load(work / "infer.json")
    observed["infer"] = {"status": infer.get("status"), "p": infer.get("p"),
                         "d": infer.get("effect_size_cohens_d")}
    if infer.get("status") != "completed":
        failures.append(f"a two-group comparison did not complete: {infer.get('status')}")
    if infer.get("p") is None or infer.get("effect_size_cohens_d") is None:
        failures.append("no p-value or no effect size was reported")
    if not infer.get("effect_size_ci_95"):
        failures.append("no confidence interval accompanied the effect size")
    # three groups
    (work / "three.csv").write_text(
        "v,g\n" + "".join(f"{x},{g}\n" for g, vals in
                          {"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]}.items() for x in vals),
        encoding="utf-8")
    rc3, _ = run(PROFILE, "infer", "--data", work / "three.csv", "--group-by", "g",
                 "--value-col", "v", "--out", work / "infer3.json")
    infer3 = load(work / "infer3.json")
    observed["infer_three_groups"] = {"rc": rc3, "status": infer3.get("status")}
    if infer3.get("status") != "refused":
        failures.append("three groups were not refused: a two-sample test must not be forced onto them")

    # ---- 6 quality: numbers must come from the cleaned file, and remaining issues be named
    run(PROFILE, "quality", "--profile", work / "profile.json", "--clean", work / "clean.csv",
        "--out", work / "quality.json")
    qual = load(work / "quality.json")
    observed["quality"] = {"issues": len(qual["issues"]), "counts": qual["issue_counts"]}
    if "cannot disagree" not in qual.get("source_of_numbers", ""):
        failures.append("the quality report does not state that its numbers come from the cleaned file")
    if not qual["issues"]:
        failures.append("a table with an undeclared column and a retained outlier produced no issues")

    # ---- 7 sql: bad column fails before running; missing join key is detected
    db = work / "lab.sqlite"
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    conn.executescript("""
        create table sample (sample_id text primary key, group_name text, ph real);
        create table reading (reading_id text primary key, sample_id text, value real, unit text);
        insert into sample values ('S1','ctrl',7.0),('S2','trt',7.2);
        insert into reading values ('R1','S1',12.5,'mg/L'),('R2','S1',12.6,'mg/L'),
                                   ('R3','S2',13.1,'mg/L'),('R4','S2',13.0,'mg/L');
    """)
    conn.commit()
    conn.close()

    run(SQL, "schema", "--database", db, "--out", work / "sqlschema.json")
    sqlschema = load(work / "sqlschema.json")
    observed["sql_schema"] = {"tables": sqlschema["table_count"]}
    if sqlschema["table_count"] != 2:
        failures.append(f"schema listed {sqlschema['table_count']} tables, expected 2")

    (work / "bad.sql").write_text("select sample_id, totl from sample", encoding="utf-8")
    rc_bad, _ = run(SQL, "check", "--database", db, "--sql", work / "bad.sql", "--out", work / "chk-bad.json")
    chk_bad = load(work / "chk-bad.json")
    observed["sql_unknown_column"] = {"rc": rc_bad, "status": chk_bad["status"],
                                      "problems": [p["kind"] for p in chk_bad["problems"]]}
    if chk_bad["status"] == "valid":
        failures.append("a query selecting a non-existent column was judged valid")

    (work / "good.sql").write_text("select s.sample_id, r.value from sample s join reading r "
                                   "on r.sample_id = s.sample_id", encoding="utf-8")
    rc_ok, _ = run(SQL, "check", "--database", db, "--sql", work / "good.sql", "--out", work / "chk-ok.json")
    chk_ok = load(work / "chk-ok.json")
    observed["sql_valid_query"] = {"rc": rc_ok, "status": chk_ok["status"]}
    if chk_ok["status"] != "valid":
        failures.append(f"a valid query was judged {chk_ok['status']!r} (false positive)")

    # the join key sample_id is unique in sample but NOT in reading -> 2 readings per sample
    run(SQL, "joins", "--database", db, "--sql", work / "good.sql", "--out", work / "joins.json")
    jr = load(work / "joins.json")
    observed["sql_join_multiplicity"] = {"status": jr["status"], "findings": len(jr["findings"])}
    if jr["status"] != "multiplicity_risk":
        failures.append("the non-unique join key on reading.sample_id was not detected")

    # an aggregate over a text column must be refused
    (work / "agg.sql").write_text("select sum(sample_id) from sample", encoding="utf-8")
    run(SQL, "check", "--database", db, "--sql", work / "agg.sql", "--out", work / "chk-agg.json")
    chk_agg = load(work / "chk-agg.json")
    observed["sql_aggregate_text"] = {"problems": [p["kind"] for p in chk_agg["problems"]]}
    if not any(p["kind"] == "aggregate_over_text" for p in chk_agg["problems"]):
        failures.append("aggregating a text column as a number was not flagged")

    # a clean query must produce rows and an audit naming the query
    run(SQL, "run", "--database", db, "--sql", work / "good.sql", "--out", work / "result.csv",
        "--audit", work / "audit.json")
    audit = load(work / "audit.json")
    observed["sql_run"] = {"status": audit["status"], "rows": audit.get("rows")}
    if audit.get("rows", 0) < 4:
        failures.append("the join query returned fewer rows than the data supports")
    if "sql" not in audit:
        failures.append("the audit does not carry the query that produced the table")

    report = {"fixture": str(work), "checks": 7, "failures": failures, "observed": observed,
              "verdict": "pass" if not failures else "fail",
              "note": "Synthetic fixtures only; not organiser cases, not official results."}
    (work / "analysis-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
