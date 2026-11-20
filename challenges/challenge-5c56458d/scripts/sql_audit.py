"""Validate SQL against a real schema before running it, then audit what the result means.

The database challenge names its failures precisely, and they are all avoidable before or immediately
after execution:

  * wrong connection parameters and invented table or column names -> **validate against the schema first**
  * **a missing join condition inflating the row count** -> measure row multiplicity against key
    uniqueness and report it, rather than trusting a number that grew silently
  * encoding-typed fields aggregated as numbers -> report each column's type and refuse a numeric
    aggregate over a text column
  * a delivered table with no trace back to the query -> the audit carries the query that produced it

    python sql_audit.py schema  --database DB.sqlite --out schema.json
    python sql_audit.py check   --database DB.sqlite --sql q.sql --out check.json
    python sql_audit.py run     --database DB.sqlite --sql q.sql --out result.csv --audit audit.json
    python sql_audit.py joins   --database DB.sqlite --sql q.sql --out joins.json
    python sql_audit.py explain --database DB.sqlite --sql q.sql --out explain.json

Python standard library only. Uses sqlite3, which is in the standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

SCHEMA = "sql-audit/v1"

TABLE_REF = re.compile(r"\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)
# A table in a join may carry an alias with or without `as`. Requiring `as` made the whole pattern
# match nothing on ordinary SQL, so join multiplicity was never examined at all.
ON_CLAUSE = re.compile(
    r"\bjoin\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+(?:as\s+)?([A-Za-z_][A-Za-z0-9_]*))?\s+on\s+(.+?)"
    r"(?=\b(?:join|where|group|order|limit|having)\b|\Z)",
    re.I | re.S)
QUALIFIED = re.compile(r"\b(\w+)\.(\w+)\b")
SELECT_ITEMS = re.compile(r"^\s*select\s+(.*?)\s+from\b", re.I | re.S)
AGGREGATES = re.compile(r"\b(sum|avg|mean|total|min|max|count)\s*\(\s*(?:distinct\s+)?(\w+|\*)\s*\)", re.I)


def connect(database: Path) -> sqlite3.Connection:
    if not Path(database).exists():
        raise SystemExit(f"no such database: {database}")
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def read_schema(database: Path) -> dict:
    """Real tables, columns and declared types, so a query is written against what exists."""
    with connect(database) as connection:
        tables = [r["name"] for r in connection.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")]
        payload = {"schema": SCHEMA, "database": str(database), "tables": []}
        for name in tables:
            columns = []
            for row in connection.execute(f'pragma table_info("{name}")'):
                columns.append({"name": row["name"], "declared_type": row["type"] or "untyped",
                                "nullable": not row["notnull"], "primary_key": bool(row["pk"])})
            counts = connection.execute(f'select count(*) as n from "{name}"').fetchone()["n"]
            unique = [c["name"] for c in columns if c["primary_key"]]
            payload["tables"].append({"name": name, "columns": columns, "rows": counts,
                                      "unique_keys": unique or None})
        payload["table_count"] = len(payload["tables"])
    return payload


def check(database: Path, sql: str, schema: dict | None = None) -> dict:
    """Fail a query that names something absent, before it is ever run."""
    schema = schema or read_schema(database)
    known_tables = {t["name"].lower() for t in schema["tables"]}
    columns_by_table = {t["name"].lower(): {c["name"].lower() for c in t["columns"]}
                        for t in schema["tables"]}
    all_columns = set().union(*columns_by_table.values()) if columns_by_table else set()

    problems: list[dict] = []
    referenced = {m.group(1).lower() for m in TABLE_REF.finditer(sql)}
    for table in sorted(referenced - known_tables):
        problems.append({"kind": "unknown_table", "severity": "high", "name": table,
                         "detail": f"no such table; available: {sorted(known_tables)}"})

    # a qualified column must exist on that table
    for table, column in {(m.group(1).lower(), m.group(2).lower()) for m in QUALIFIED.finditer(sql)}:
        if table in columns_by_table and column not in columns_by_table[table]:
            problems.append({"kind": "unknown_column", "severity": "high", "name": f"{table}.{column}",
                             "detail": f"{table} has no column {column}"})
    # a bare identifier is suspicious only where a column is required. Names in a create table, a
    # column definition or a type name are not column references, so scanning every word produced false
    # positives on valid queries.
    select_match = SELECT_ITEMS.search(sql)
    if select_match:
        items = [i.strip() for i in select_match.group(1).split(",")]
        for item in items:
            bare = item.strip().split()[0] if item.strip() else ""
            if not bare or bare == "*" or "(" in item or "." in bare:
                continue
            if bare.lower() not in all_columns:
                problems.append({"kind": "unknown_column", "severity": "high", "name": bare,
                                 "detail": f"no column named {bare} in any table"})

    # numeric aggregate over a text column is the "encoded field aggregated as a number" failure
    for func, column in ((m.group(1).lower(), m.group(2).lower()) for m in AGGREGATES.finditer(sql)):
        if column == "*" or func == "count":
            continue
        for table, cols in columns_by_table.items():
            if column in cols:
                declared = next(c["declared_type"] for c in schema["tables"][
                    [t["name"].lower() for t in schema["tables"]].index(table)]["columns"]
                    if c["name"].lower() == column)
                if not re.search(r"int|real|num|dec|float|double", declared, re.I):
                    problems.append({
                        "kind": "aggregate_over_text", "severity": "high",
                        "name": f"{func}({column})",
                        "detail": (f"{column} is declared {declared!r}, not numeric. Aggregating an "
                                   "encoded or categorical field as a number produces a meaningless "
                                   "result; map it to a label first."),
                    })

    return {"schema": SCHEMA, "problems": problems,
            "high_severity": sum(1 for p in problems if p["severity"] == "high"),
            "tables_referenced": sorted(referenced),
            "status": "valid" if not any(p["severity"] == "high" for p in problems) else "invalid",
            "rule": "a table or column that does not exist fails before execution, not during it"}


def joins(database: Path, sql: str, schema: dict | None = None) -> dict:
    """Detect the join whose key is not unique on one side, which multiplies rows silently.

    The direction matters and cannot be read off the SQL text: `a join b on b.k = a.k` multiplies rows
    when `b.k` is non-unique, because one row of `a` then matches several of `b`. So every table named in
    a join — on either side of the `on` clause — is tested for key uniqueness, and the multiplicity is
    reported rather than assumed.
    """
    schema = schema or read_schema(database)
    columns_by_table = {t["name"].lower(): t for t in schema["tables"]}
    findings: list[dict] = []
    examined = 0
    with connect(database) as connection:
        for match in ON_CLAUSE.finditer(sql):
            joined_table = match.group(1).lower()
            alias = (match.group(2) or "").lower()
            clause = match.group(3)
            examined += 1
            keys = [(m.group(1).lower(), m.group(2).lower()) for m in QUALIFIED.finditer(clause)]
            # the alias stands for the joined table, so resolve it before looking anything up
            alias_map = {alias: joined_table} if alias and alias != joined_table else {}
            alias_map[joined_table] = joined_table
            candidates = {joined_table} | {alias_map.get(t, t) for t, _ in keys}
            for table in sorted(candidates):
                info = columns_by_table.get(table)
                if not info:
                    continue
                for column in {c for t, c in keys if alias_map.get(t, t) == table} | {
                        c["name"].lower() for c in info["columns"] if c["primary_key"]}:
                    if not any(c["name"].lower() == column for c in info["columns"]):
                        continue
                    total = connection.execute(f'select count(*) as n from "{info["name"]}"').fetchone()["n"]
                    distinct = connection.execute(
                        f'select count(distinct "{column}") as n from "{info["name"]}"').fetchone()["n"]
                    if total == 0:
                        continue
                    ratio = (total / distinct) if distinct else None
                    if not distinct:
                        findings.append({"table": info["name"], "key": column, "severity": "high",
                                         "detail": "the join key is entirely null in this table"})
                    elif ratio and ratio > 1.05:
                        findings.append({
                            "table": info["name"], "key": column, "rows": total,
                            "distinct_keys": distinct, "multiplicity": round(ratio, 3),
                            "severity": "high",
                            "detail": (f"join key {info['name']}.{column} is not unique: {total} rows over "
                                       f"{distinct} distinct values, so each match multiplies by up to "
                                       f"{round(ratio, 1)}x and the row count inflates without an error."),
                        })
    return {
        "schema": SCHEMA, "joins_examined": examined, "findings": findings,
        "status": "clean" if not findings else "multiplicity_risk",
        "rule": ("a join key that is not unique multiplies rows; every table named in a join is measured "
                 "for key uniqueness rather than assumed unique"),
    }


def explain(database: Path, sql: str) -> dict:
    with connect(database) as connection:
        try:
            rows = connection.execute("explain query plan " + sql).fetchall()
        except sqlite3.Error as exc:
            return {"schema": SCHEMA, "status": "error", "detail": str(exc)}
    return {"schema": SCHEMA, "status": "ok",
            "plan": [dict(r) for r in rows]}


def run(database: Path, sql: str, out_path: Path, audit_path: Path, schema: dict | None = None) -> dict:
    """Run the query, write the rows, and record what produced them."""
    schema = schema or read_schema(database)
    validation = check(database, sql, schema)
    multiplicity = joins(database, sql, schema)
    with connect(database) as connection:
        try:
            cursor = connection.execute(sql)
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description or []]
        except sqlite3.Error as exc:
            result = {"schema": SCHEMA, "status": "error", "detail": str(exc),
                      "sql": sql, "validation": validation}
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[c] for c in columns])

    column_types = {}
    for table in schema["tables"]:
        for col in table["columns"]:
            column_types.setdefault(col["name"].lower(), col["declared_type"])
    audit = {
        "schema": SCHEMA, "status": "ok", "sql": sql, "rows": len(rows), "columns": columns,
        "column_types": {c: column_types.get(c.lower(), "unknown") for c in columns},
        "validation": {"status": validation["status"], "high_severity": validation["high_severity"]},
        "join_multiplicity": {"status": multiplicity["status"], "findings": len(multiplicity["findings"])},
        "out": str(out_path),
        "rule": ("the delivered table carries the query that produced it, the row count, and the column "
                 "types, so a field's meaning is auditable rather than assumed"),
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate and audit SQL against a real schema")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("schema"); p.add_argument("--database", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("check"); p.add_argument("--database", required=True); p.add_argument("--sql", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("joins"); p.add_argument("--database", required=True); p.add_argument("--sql", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("explain"); p.add_argument("--database", required=True); p.add_argument("--sql", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("run")
    p.add_argument("--database", required=True); p.add_argument("--sql", required=True)
    p.add_argument("--out", required=True); p.add_argument("--audit", required=True)

    args = parser.parse_args(argv)
    sql_text = Path(args.sql).read_text(encoding="utf-8") if hasattr(args, "sql") else ""

    if args.command == "schema":
        result = read_schema(Path(args.database)); write_json(args.out, result)
        print(json.dumps({"tables": result["table_count"]}, ensure_ascii=False))
        return 0
    if args.command == "check":
        result = check(Path(args.database), sql_text); write_json(args.out, result)
        print(json.dumps({"status": result["status"], "high": result["high_severity"]}, ensure_ascii=False))
        return 0 if result["status"] == "valid" else 3
    if args.command == "joins":
        result = joins(Path(args.database), sql_text); write_json(args.out, result)
        print(json.dumps({"status": result["status"], "findings": len(result["findings"])}, ensure_ascii=False))
        return 0 if result["status"] == "clean" else 3
    if args.command == "explain":
        result = explain(Path(args.database), sql_text); write_json(args.out, result)
        print(json.dumps({"status": result["status"]}, ensure_ascii=False))
        return 0
    if args.command == "run":
        result = run(Path(args.database), sql_text, Path(args.out), Path(args.audit))
        print(json.dumps({k: result.get(k) for k in ("status", "rows")}, ensure_ascii=False))
        return 0 if result.get("status") == "ok" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
