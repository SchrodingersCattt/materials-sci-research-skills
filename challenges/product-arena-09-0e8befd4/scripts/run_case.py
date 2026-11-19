"""One command for the mechanical half of a case, so the agent spends its budget on content.

The organizer gives the evaluation agent 64 model requests for three cases, which is roughly twenty
requests per case. A workflow that spends eight of them on orchestration (extract the contract,
skeleton the result, build the artifact, audit, conform, verify, write result.json, re-open) leaves
very little for reading the material and writing the deliverable. This runner collapses those into
two calls:

    python <skill>/scripts/run_case.py plan                 # contract + checklist + result skeleton
    <the agent reads the material and writes the deliverable>
    python <skill>/scripts/run_case.py finish --md work/deliverable.md

Both calls are resilient: if a sibling script is absent they skip that stage and say so, rather than
failing the whole run. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

PLACEHOLDER = {
    "str": "<REPLACE-WITH-THE-REAL-VALUE>",
    "int": 0,
    "float": 0.0,
    "bool": False,
    "list": [],
    "dict": {},
}


def script(name: str):
    path = SCRIPTS / name
    return path if path.exists() else None


def call(argv):
    proc = subprocess.run([sys.executable, *[str(a) for a in argv]], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "").strip()
    payload = None
    for chunk in reversed([line for line in out.replace("\r", "\n").splitlines()
                           if line.strip().startswith("{")]):
        try:
            payload = json.loads(chunk)
            break
        except json.JSONDecodeError:
            continue
    return {"rc": proc.returncode, "json": payload,
            "stdout": out[-1200:], "stderr": (proc.stderr or "")[-600:]}


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def skeleton(contract: dict) -> dict:
    payload = {}
    case = contract.get("case") or {}
    if case.get("case_id"):
        payload["case_id"] = case["case_id"]
    for entry in contract.get("required_keys") or []:
        path = entry.get("path") or ""
        if "." in path:
            continue
        expected = entry.get("expected_type") or "str"
        if entry.get("allowed_values"):
            payload.setdefault(path, entry["allowed_values"][0])
        else:
            payload.setdefault(path, PLACEHOLDER.get(expected, "<REPLACE-WITH-THE-REAL-VALUE>"))
    return payload


def checklist(contract: dict) -> str:
    lines = ["# Contract check list", "",
             f"Extracted from `{(contract.get('case') or {}).get('path')}`.", "",
             "## result.json"]
    for entry in contract.get("required_keys") or []:
        vocab = entry.get("allowed_values")
        note = f"  \u2014 allowed: {vocab}" if vocab else ""
        lines.append(f"- [ ] `{entry['path']}` ({entry.get('expected_type') or 'str'}){note}")
    if contract.get("required_files"):
        lines += ["", "## deliverables that must exist"]
        lines += [f"- [ ] `{name}` (non-empty, real format)" for name in contract["required_files"]]
    if contract.get("required_columns"):
        lines += ["", "## CSV columns"]
        lines += [f"- [ ] `{name}`" for name in contract["required_columns"]]
    lines += ["", "## always", "",
              "- [ ] every number is either a declared source value or a declared "
              "compatible-unit calculation",
              "- [ ] every missing value says \"not reported\"; nothing is invented",
              "- [ ] result.json keeps the original case_id and every original output_contract field",
              "- [ ] the run's own limits (missing renderer, unreadable file) are stated in the status",
              ""]
    return "\n".join(lines)


BOOKKEEPING = {"contract.json", "result-skeleton.json", "checklist.md", "quantity-plan.json",
               "run-evidence.json"}


def collect_deliverables(work: Path, out: Path) -> list:
    """Copy everything the run produced from the work directory into the output directory.

    The runtime contract requires the case's named deliverables to be under /app/output, but an
    agent naturally writes them in the work directory it was told to use. Files the runner itself
    wrote (contract, skeleton, check list, audit inputs) are skipped, and so are the runner's own
    sub-directories; everything else is treated as a deliverable. `run-evidence.json` is copied on
    purpose: the evidence trail is meant to travel with the output.
    """
    copied = []
    if not work.is_dir():
        return copied
    skip_dirs = {"quantity-audit", "conformance", "verify"}
    for path in sorted(work.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(work)
        if rel.parts[0] in skip_dirs or "__pycache__" in rel.parts:
            continue
        if rel.parent == Path(".") and rel.name in BOOKKEEPING - {"run-evidence.json"}:
            continue
        if rel.name == "result.json":
            continue
        target = out / rel
        if target.exists() and target.read_bytes() == path.read_bytes():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        copied.append(rel.as_posix())
    return copied


def cmd_plan(args) -> int:
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    case_path = Path(args.case)
    report = {"case_path": str(case_path), "case_found": case_path.exists(), "stages": {}}

    contract_path = work / "contract.json"
    if case_path.exists():
        tool = script("contract_check.py")
        if tool:
            result = call([tool, "extract", "--case", case_path,
                           "--task", str(args.task), "--out", contract_path])
            report["stages"]["contract"] = result["rc"]
        else:
            report["stages"]["contract"] = "skipped: no contract_check.py"
    else:
        report["stages"]["contract"] = "skipped: case file absent"

    if contract_path.exists():
        contract = read_json(contract_path) or {}
        (work / "checklist.md").write_text(checklist(contract), encoding="utf-8")
        (work / "result-skeleton.json").write_text(
            json.dumps(skeleton(contract), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["contract_names"] = {
            "keys": [e["path"] for e in contract.get("required_keys") or []],
            "files": contract.get("required_files") or [],
            "columns": contract.get("required_columns") or [],
        }

    report["next"] = [
        "read the case material the case names, from the real files",
        "write the deliverable now, even if some sections are still thin",
        "write result.json to " + str(work / "result.json") + " (the shape is in "
        "work/result-skeleton.json), replacing every placeholder; finish copies it to the output "
        "directory",
        "then run: python " + str(SCRIPTS / "run_case.py") + " finish --md <each markdown file>",
    ]
    report["work"] = str(work)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_finish(args) -> int:
    work = Path(args.work)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"stages": {}, "outputs": []}

    markdown = [Path(p) for p in args.md]
    if not markdown and work.exists():
        markdown = sorted(p for p in work.glob("*.md") if p.name != "checklist.md")

    deliver = script("deliver.py")
    if deliver and markdown:
        suffix = Path(args.name).suffix or ".docx"
        # A case asks for one editable deliverable, so several sections belong in one file unless
        # the caller asks for per-section files with --per-file.
        if args.per_file:
            groups = [(md_path.stem or f"deliverable-{i}", [md_path])
                      for i, md_path in enumerate(markdown, start=1)]
        else:
            groups = [(Path(args.name).stem or "deliverable", markdown)]
        for label, sources in groups:
            target = out / (label if label.endswith(suffix) else f"{label}{suffix}")
            argv = [deliver, "build-docx"]
            for md_path in sources:
                argv += ["--md", md_path]
            argv += ["--out", target]
            result = call(argv)
            report["stages"][f"build:{'+'.join(p.name for p in sources)}"] = result["rc"]
            if result["rc"] == 0 and target.exists():
                verify_argv = [deliver, "verify", "--out-file", target]
                for md_path in sources:
                    verify_argv += ["--md", md_path]
                verify_argv += ["--outdir", work / "verify"]
                verify = call(verify_argv)
                report["stages"][f"verify:{target.name}"] = verify["rc"]
                report["outputs"].append(str(target))
    elif deliver:
        report["stages"]["build"] = "skipped: no markdown found"
    else:
        report["stages"]["build"] = "skipped: no deliver.py in this skill"

    result_path = out / "result.json"
    work_result = work / "result.json"
    if work_result.exists():
        # The agent wrote result.json where `plan` told it to; it belongs in the output directory too.
        payload = read_json(work_result)
        if isinstance(payload, dict):
            payload["deliverables"] = report["outputs"] or payload.get("deliverables") or []
            written = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            work_result.write_text(written, encoding="utf-8")
            if not result_path.exists() or result_path.read_text(encoding="utf-8") != written:
                result_path.write_text(written, encoding="utf-8")
            report["stages"]["result_json"] = "copied from work/result.json into the output directory"
        else:
            report["stages"]["result_json"] = "work/result.json is not valid JSON"
    elif result_path.exists():
        report["stages"]["result_json"] = "present in the output directory"
    else:
        source = work / "result-skeleton.json"
        payload = read_json(source) if source.exists() else None
        if not payload:
            payload = {"case_id": args.case_id or "<REPLACE-WITH-THE-ORIGINAL-CASE-ID>"}
        payload.setdefault("status", "partial")
        payload["deliverables"] = report["outputs"]
        payload.setdefault("uncertainties", [])
        # An empty list is an honest "nothing declared"; a missing key is a completeness failure.
        for key in ("sources", "evidence_map", "change_log"):
            payload.setdefault(key, [])
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        report["stages"]["result_json"] = ("no result.json was written; a skeleton with placeholders "
                                          "was placed in the output directory and MUST be filled in")

    report["copied_to_output"] = collect_deliverables(work, out)

    audit = script("quantity_audit.py")
    plan_file = work / "quantity-plan.json"
    if audit and plan_file.exists():
        report["stages"]["quantity_audit"] = call(
            [audit, "--plan", plan_file, "--outdir", work / "quantity-audit"])["rc"]
    elif audit:
        report["stages"]["quantity_audit"] = "skipped: no work/quantity-plan.json"

    # The scan needs no hand-written plan, so unlike quantity_audit it always runs. It is the check
    # that catches an invented number, which is the one defect a reviewer cannot see by eye.
    scan = script("number_scan.py")
    wanted = [Path(item) for item in (args.data or [])]
    if not wanted:
        wanted = [Path("/input/material"), Path("/input/data"), Path("/input")]
    data_dirs = [p for p in wanted if p.exists()]
    if scan and markdown and data_dirs:
        argv = [scan]
        for md_path in markdown:
            argv += ["--md", md_path]
        for path in data_dirs:
            argv += ["--data", path]
        argv += ["--out", work / "number-scan.json"]
        result = call(argv)
        report["stages"]["number_scan"] = result["rc"]
        payload = result.get("json") or {}
        if payload.get("counts"):
            report["number_scan_counts"] = payload["counts"]
        if payload.get("undeclared"):
            report["undeclared_numbers"] = [
                f"{item['number']}{item['unit']} :: {item['sentence'][:80]}"
                for item in payload["undeclared"][:10]]
    elif scan:
        report["stages"]["number_scan"] = "skipped: no markdown or no input data found"

    conform_tool = script("contract_check.py")
    contract_path = work / "contract.json"
    if conform_tool and contract_path.exists():
        result = call([conform_tool, "conform", "--contract", contract_path,
                       "--output", out, "--outdir", work / "conformance"])
        report["stages"]["conformance"] = result["rc"]
        conformance = work / "conformance" / "conformance.json"
        payload = read_json(conformance) if conformance.exists() else None
        if payload:
            report["failed_checks"] = [c["id"] for c in payload.get("checks") or []
                                       if c.get("status") == "fail"]
    else:
        report["stages"]["conformance"] = "skipped: no contract.json"

    # result_path is created by every branch above, so a leftover placeholder is always reported.
    if result_path.exists():
        text = result_path.read_text(encoding="utf-8")
    else:
        text = ""
    report["remaining_placeholders"] = [line.strip() for line in text.splitlines()
                                        if "REPLACE-WITH" in line]
    report["note"] = ("Exit 0 means the mechanical stages ran; it is not a score. A non-zero stage "
                      "or a listed failed check must be repaired, and a placeholder left in "
                      "result.json must be replaced.")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    hard = [v for v in report["stages"].values() if isinstance(v, int) and v != 0]
    return 0 if not hard and not report["remaining_placeholders"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="run the mechanical stages of one case")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="read the case contract and lay out the run")
    plan.add_argument("--case", default="/input/case.json")
    plan.add_argument("--task", default="/input/task.md")
    plan.add_argument("--work", default="/app/work")
    plan.set_defaults(func=cmd_plan)
    finish = sub.add_parser("finish", help="build, audit, conform and verify the deliverables")
    finish.add_argument("--md", action="append", default=[])
    finish.add_argument("--work", default="/app/work")
    finish.add_argument("--out", default="/app/output")
    finish.add_argument("--name", default="deliverable.docx")
    finish.add_argument("--data", action="append", default=[],
                        help="supplied data files or directories for the number scan "
                             "(default: /input/material, /input/data, /input)")
    finish.add_argument("--per-file", action="store_true",
                        help="build one document per markdown file instead of one combined file")
    finish.add_argument("--case-id", default="")
    finish.set_defaults(func=cmd_finish)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
