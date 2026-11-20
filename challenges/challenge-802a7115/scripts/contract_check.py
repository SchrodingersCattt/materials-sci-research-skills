"""Output-contract conformance: read the case's contract, then prove the deliverables satisfy it.

Published top-scoring skills in this ecosystem all work the same way: read the output contract clause
by clause, extract the exact filenames, column names and JSON keys, produce them, and then re-check
the artifacts against that list with a separate script. This module makes that mechanical.

    extract   --case FILE [--task FILE] --out contract.json
    skeleton  --contract contract.json --out result.json
    conform   --contract contract.json --output DIR [--result FILE] --outdir DIR
    verify    --case FILE [--task FILE] --outdir DIR

Python standard library only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"^\s*(?:<[^>]{1,40}>|TODO|TBD|FIXME|\.{3}|\?{3})\s*$", re.I)
TYPE_HINTS = ("str", "string", "text", "int", "integer", "float", "number", "bool", "boolean",
              "list", "array", "dict", "object")
EXPECTED_TYPE = {
    "str": "str", "string": "str", "text": "str", "int": "int", "integer": "int",
    "float": "float", "number": "float", "bool": "bool", "boolean": "bool",
    "list": "list", "array": "list", "dict": "dict", "object": "dict",
}
KEY_LINE = re.compile(r"^\s*[-*>]?\s*`([A-Za-z_][A-Za-z0-9_.]{0,60})`\s*[:：]?\s*(.*)$")
FILE_TOKEN = re.compile(r"[`\"']([A-Za-z0-9_.-]+\.(?:json|jsonl|md|csv|docx|pptx|pdf|png|svg|txt|tex))[`\"']")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flatten(payload, prefix: str = "") -> list:
    out = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.append({"path": path, "type": type(value).__name__})
            out.extend(flatten(value, path))
    elif isinstance(payload, list) and payload:
        out.extend(flatten(payload[0], f"{prefix}[]"))
    return out


def get_path(payload, path: str):
    node = payload
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None, False
    return node, True


def from_contract_object(contract: dict) -> list:
    keys = []
    for key, value in contract.items():
        entry = {"path": str(key), "declared": value if isinstance(value, str) else None}
        if isinstance(value, str):
            lowered = value.lower()
            for hint in TYPE_HINTS:
                if re.search(rf"\b{hint}\b", lowered):
                    entry["expected_type"] = EXPECTED_TYPE[hint]
                    break
            if "|" in value:
                allowed = [part.strip() for part in value.split("|") if part.strip()]
                if len(allowed) > 1:
                    entry["allowed_values"] = allowed
        elif isinstance(value, list):
            entry["expected_type"] = "list"
        elif isinstance(value, dict):
            entry["expected_type"] = "dict"
        keys.append(entry)
    return keys


def column_names(window: str) -> list:
    """Names a "columns ..." clause asks for: backticked names first, then bare identifiers."""
    found = re.findall(r"`([A-Za-z_][A-Za-z0-9_]{0,40})`", window)
    if not found:
        found = [match for match in
                 re.findall(r"^\s*([a-z][a-z0-9_]{1,40})|\b([a-z]+_[a-z0-9_]+)\b", window)
                 for match in (match[0] or match[1],)]
    return [name for name in dict.fromkeys(found) if name and name.lower() not in ("and", "the")]


def from_prose(text: str) -> dict:
    files, keys, columns = [], [], []
    for match in FILE_TOKEN.finditer(text):
        name = match.group(1)
        if name not in files and name not in ("case.json", "task.md", "result.json"):
            files.append(name)
    for line in text.splitlines():
        match = KEY_LINE.match(line)
        if match:
            key = match.group(1)
            if "." in key or key in ("case_id",) or key not in [e["path"] for e in keys]:
                keys.append({"path": key, "declared": match.group(2)[:200]})
    for match in re.finditer(r"columns?|字段", text, re.I):
        window = text[match.end():match.end() + 400]
        window = re.split(r"[\n。]", window)[0]
        for candidate in column_names(window):
            if candidate not in columns:
                columns.append(candidate)
    return {"files": files, "keys": keys, "columns": columns}


def extract(case_path: Path, task_path: Path | None) -> dict:
    case = json.loads(case_path.read_text(encoding="utf-8"))
    contract = case.get("output_contract")
    keys: list = []
    if isinstance(contract, dict) and contract:
        keys = from_contract_object(contract)
    prose_parts = [str(case.get(key) or "") for key in
                   ("task_instruction", "instruction", "deliverable", "evaluation")]
    if task_path and task_path.exists():
        prose_parts.append(task_path.read_text(encoding="utf-8", errors="replace"))
    prose = "\n".join(prose_parts)
    extra = from_prose(prose) if prose.strip() else {"files": [], "keys": [], "columns": []}

    known = {entry["path"] for entry in keys}
    for entry in extra["keys"]:
        if entry["path"] not in known:
            keys.append(entry)
            known.add(entry["path"])

    case_id = case.get("case_id") or case.get("id")
    required_files = [name for name in extra["files"] if not name.startswith(("http", "result."))]
    return {
        "schema": "output-contract/v1",
        "case": {"path": str(case_path), "sha256": sha256_file(case_path), "case_id": case_id,
                 "title": case.get("title") or case.get("topic_title")},
        "task": {"path": str(task_path)} if task_path else None,
        "required_keys": keys,
        "required_files": required_files,
        "required_columns": extra["columns"],
        "checklist": [
            f"result.json exists, is valid JSON, and keeps case_id = {case_id!r}",
            *[f"result.json carries key '{entry['path']}'"
              + (f" from the vocabulary {entry['allowed_values']}" if entry.get("allowed_values") else "")
              for entry in keys],
            *[f"{name} exists and is non-empty" for name in required_files],
            *[f"the CSV deliverable carries the column '{name}'" for name in extra["columns"]],
            "no value is left as a placeholder marker",
        ],
        "source_note": "Extracted from the case's own output contract and task text. A case that "
                       "states its contract only in prose yields a shorter checklist; a key missing "
                       "here is not permission to omit it from result.json.",
    }


def skeleton(contract: dict) -> dict:
    case_id = (contract.get("case") or {}).get("case_id")
    payload: dict = {}
    for entry in contract.get("required_keys", []):
        path = entry["path"]
        expected = entry.get("expected_type")
        if path == "case_id":
            value = case_id
        elif expected == "str":
            value = ""
        elif expected == "int":
            value = 0
        elif expected == "float":
            value = 0.0
        elif expected == "bool":
            value = False
        elif expected == "list":
            value = []
        elif expected == "dict":
            value = {}
        else:
            value = None
        head, _, tail = path.partition(".")
        if tail:
            payload.setdefault(head, {})
            if isinstance(payload[head], dict):
                payload[head][tail] = value
        else:
            payload[path] = value
    if case_id and "case_id" not in payload:
        payload = {"case_id": case_id, **payload}
    return payload


def conform(contract: dict, output_dir: Path, result_path: Path | None, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    checks: list = []

    def add(check_id, requirement, ok, evidence):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence})

    result_file = Path(result_path) if result_path else output_dir / "result.json"
    payload = None
    if not result_file.exists():
        add("result_exists", "result.json exists", False, f"{result_file} not found")
    else:
        try:
            payload = json.loads(result_file.read_text(encoding="utf-8"))
            add("result_parses", "result.json is valid JSON", True,
                f"{result_file.stat().st_size} bytes at {result_file}")
        except json.JSONDecodeError as error:
            add("result_parses", "result.json is valid JSON", False, repr(error))

    missing_keys: list = []
    if payload is not None:
        expected_case = (contract.get("case") or {}).get("case_id")
        add("case_id_preserved", "the result keeps the case identifier from the input",
            expected_case is None or payload.get("case_id") == expected_case,
            f"expected={expected_case!r} found={payload.get('case_id')!r}")

        flat = {entry["path"]: entry["type"] for entry in flatten(payload)}
        wrong_type = []
        for entry in contract.get("required_keys", []):
            path = entry["path"]
            expected = entry.get("expected_type")
            if path not in flat:
                missing_keys.append(path)
                continue
            found = flat[path]
            if expected == "str" and found != "str":
                wrong_type.append(f"{path}: declared str, found {found}")
            elif expected == "list" and found != "list":
                wrong_type.append(f"{path}: declared list, found {found}")
            elif expected == "dict" and found != "dict":
                wrong_type.append(f"{path}: declared object, found {found}")
        add("required_keys_present", "every contract key is present in result.json",
            not missing_keys, f"missing={missing_keys[:10]}")
        add("key_types_match", "declared key types match the produced values", not wrong_type,
            f"{wrong_type[:6]}")

        vocabulary_violations = []
        for entry in contract.get("required_keys", []):
            allowed = entry.get("allowed_values")
            if not allowed:
                continue
            value, present = get_path(payload, entry["path"])
            if present and isinstance(value, str) and value and value not in allowed:
                vocabulary_violations.append(f"{entry['path']}={value!r} not in {allowed}")
            elif present and isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item and item not in allowed:
                        vocabulary_violations.append(f"{entry['path']}[]={item!r} not in {allowed}")
        add("declared_vocabulary_respected",
            "a key with a declared vocabulary uses only those values",
            not vocabulary_violations, f"{vocabulary_violations[:6]}")

        placeholders: list = []

        def scan(node, prefix=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    scan(value, f"{prefix}.{key}" if prefix else str(key))
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    scan(value, f"{prefix}[{index}]")
            elif isinstance(node, str) and PLACEHOLDER.match(node):
                placeholders.append(prefix)

        scan(payload)
        add("no_placeholders", "no value is left as a placeholder marker", not placeholders,
            f"{placeholders[:8]}")

        add("sources_recorded", "the result records where its facts came from",
            any(key in payload for key in ("evidence_map", "sources", "source_map", "claims")),
            f"keys={sorted(payload)[:12]}")

    missing_files, empty_files = [], []
    for name in contract.get("required_files", []):
        candidate = output_dir / name
        if not candidate.exists():
            missing_files.append(name)
        elif candidate.stat().st_size == 0:
            empty_files.append(name)
    add("required_files_exist", "every declared deliverable file exists", not missing_files,
        f"missing={missing_files[:8]}")
    add("required_files_nonempty", "every declared deliverable file is non-empty", not empty_files,
        f"empty={empty_files[:8]}")

    column_problems = []
    for name in contract.get("required_files", []):
        if not name.endswith(".csv"):
            continue
        candidate = output_dir / name
        if not candidate.exists():
            continue
        with candidate.open(newline="", encoding="utf-8", errors="replace") as handle:
            header = next(csv.reader(handle), [])
        for column in contract.get("required_columns", []):
            if column not in header:
                column_problems.append(f"{name}: no '{column}' column (has {header[:8]})")
    add("declared_columns_present", "every declared column appears in the CSV deliverable",
        not column_problems, f"{column_problems[:6]}")

    failures = [entry for entry in checks if entry["status"] == "fail"]
    report = {
        "schema": "output-contract-check/v1",
        "contract": contract.get("case"),
        "output_dir": str(output_dir),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "failed": len(failures),
        "status": "conformant" if not failures else "needs_work",
        "missing": {"keys": missing_keys, "files": missing_files, "columns": column_problems},
        "scope_note": "Proves the deliverables satisfy the case's declared contract: presence, "
                      "nesting, declared vocabulary, files and columns. It does not judge scientific "
                      "content and is not an official score.",
    }
    (outdir / "conformance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Output-contract conformance")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--case", required=True)
    p.add_argument("--task")
    p.add_argument("--out", required=True)
    p = sub.add_parser("skeleton")
    p.add_argument("--contract", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("conform")
    p.add_argument("--contract", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--result")
    p.add_argument("--outdir", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--case", required=True)
    p.add_argument("--task")
    p.add_argument("--outdir", required=True)
    args = parser.parse_args(argv)

    if args.command == "extract":
        contract = extract(Path(args.case), Path(args.task) if args.task else None)
        Path(args.out).write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"keys": len(contract["required_keys"]),
                          "files": len(contract["required_files"]),
                          "columns": len(contract["required_columns"]),
                          "checklist": len(contract["checklist"])}, ensure_ascii=False))
        return 0
    if args.command == "skeleton":
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        payload = skeleton(contract)
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"keys": sorted(payload)}, ensure_ascii=False))
        return 0
    if args.command == "conform":
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        report = conform(contract, Path(args.output),
                         Path(args.result) if args.result else None, Path(args.outdir))
        print(json.dumps({"passed": report["passed"], "failed": report["failed"],
                          "status": report["status"], "missing": report["missing"]},
                         ensure_ascii=False))
        return 0 if report["status"] == "conformant" else 3
    if args.command == "verify":
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        case_path = Path(args.case)
        first = extract(case_path, Path(args.task) if args.task else None)
        second = extract(case_path, Path(args.task) if args.task else None)
        checks = [
            {"id": "case_hash", "requirement": "the case hash is recorded",
             "status": "pass" if first["case"]["sha256"] else "fail",
             "evidence": f"sha256={first['case']['sha256'][:16]}…"},
            {"id": "deterministic", "requirement": "two extractions produce the same checklist",
             "status": "pass" if first["checklist"] == second["checklist"] else "fail",
             "evidence": f"checklist items={len(first['checklist'])}"},
            {"id": "checklist_nonempty", "requirement": "the checklist covers at least result.json",
             "status": "pass" if first["checklist"] else "fail",
             "evidence": f"{len(first['checklist'])} items"},
        ]
        failures = [entry for entry in checks if entry["status"] == "fail"]
        report = {"schema": "output-contract-verify/v1", "checks": checks,
                  "passed": len(checks) - len(failures), "failed": len(failures),
                  "status": "verified" if not failures else "needs_work"}
        (outdir / "contract-verification.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
