"""Run case-supplied Python methods and retain an auditable, bounded record."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("expected an input-relative path")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("path leaves the input copy")
    return result


def init(root: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    target = out / "result.json"
    if target.exists():
        return
    case = json.loads((root / "case.json").read_text(encoding="utf-8"))
    contract = case.get("output_contract", {})
    result = {key: None for key in contract} if isinstance(contract, dict) else {}
    result.update({"case_id": case.get("case_id"), "status": "partial", "sources": [],
                   "uncertainty": ["Run and verify both case-supplied methods; this is only an initial partial record."],
                   "change_log": [{"action": "initialize"}]})
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(root: Path, work: Path, out: Path, plan_path: Path) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    runs = plan.get("runs")
    if not isinstance(runs, list) or not runs or len(runs) > 10:
        raise ValueError("plan needs one to ten explicitly specified runs")
    if any(p.is_symlink() for p in root.rglob("*")):
        raise ValueError("input symlinks are not copied")
    root, work, out = root.resolve(), work.resolve(), out.resolve()
    if work.is_relative_to(root) or out.is_relative_to(root):
        raise ValueError('work/output must not be inside source input')
    copies = work / 'case-copies'
    logs = out / 'run-logs'
    if copies.exists() or logs.exists() or (out / 'execution_record.json').exists():
        raise ValueError('existing work or evidence: choose fresh work/output directories')
    # Validate the WHOLE plan before copying or running anything.
    for item in runs:
        if not isinstance(item, dict) or not isinstance(item.get('args', []), list) or any(not isinstance(x,str) for x in item.get('args',[])):
            raise ValueError('each run needs a script path and string arguments')
        script = safe(root, item.get('script'))
        if not script.is_file() or script.suffix != '.py':
            raise ValueError('each script must be an existing case-supplied Python file')
        if not safe(root,item.get('cwd','.')).is_dir():
            raise ValueError('run working directory does not exist')
        seconds = item.get('timeout_seconds',120)
        if type(seconds) is not int or not 1 <= seconds <= 180:
            raise ValueError('run timeout must be 1 to 180 seconds')
    inputs = [{'path': p.relative_to(root).as_posix(), 'sha256': sha(p)} for p in sorted(root.rglob('*')) if p.is_file()]
    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir()
    records = []
    report = {'python':sys.version,'platform':platform.platform(),'input_files':inputs,'runs':records,
              'limitations':['Separate file copies isolate method inputs, not OS processes or network access.',
                             'Execution is not original-paper reproduction or numerical agreement.']}
    def checkpoint():
        (out/'execution_record.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    checkpoint()
    for index, item in enumerate(runs,1):
        copy = copies / f'run-{index}'
        shutil.copytree(root,copy)
        script = safe(copy,item['script'])
        cwd = safe(copy,item.get('cwd','.'))
        seconds = item.get('timeout_seconds',120)
        argv = [sys.executable, str(script), *item.get("args", [])]
        script_hash = sha(script)
        env = {key: value for key, value in os.environ.items()
               if not any(word in key.upper() for word in ("TOKEN", "PASSWORD", "SECRET", "API_KEY"))}
        started = time.monotonic()
        try:
            proc = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=seconds, env=env)
            code, stdout, stderr, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr, timed_out = None, exc.stdout or b"", exc.stderr or b"", True
        stdout_size, stderr_size = len(stdout), len(stderr)
        stdout = stdout[:1_000_000]
        stderr = stderr[:1_000_000]
        (logs / f"run-{index}.stdout.txt").write_bytes(stdout)
        (logs / f"run-{index}.stderr.txt").write_bytes(stderr)
        records.append({"id": item.get("id", str(index)), "script_input_path": item["script"],
                        "script_sha256": script_hash, "script_sha256_after": sha(script) if script.is_file() else None,
                        "cwd_in_case_copy": item.get("cwd", "."),
                        "argv": argv, "exit_code": code, "timed_out": timed_out,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "stdout": f"run-logs/run-{index}.stdout.txt", "stderr": f"run-logs/run-{index}.stderr.txt",
                        "stdout_bytes": stdout_size, "stderr_bytes": stderr_size,
                        "case_copy": str(copy),
                        "output_truncated": stdout_size > 1_000_000 or stderr_size > 1_000_000})
        checkpoint()
    report = {"python": sys.version, "platform": platform.platform(), "input_files": inputs, "runs": records,
              "limitations": ["Case-supplied scripts were executed; this does not establish that they are original author code or reproduce the original experiment.",
                              "Compare outputs to source references and predeclared tolerances separately; a successful exit alone does not establish numerical agreement."]}
    (out / "execution_record.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def compare(path: Path, out: Path) -> dict:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("comparison needs at least one row")
    result = []
    for row in rows:
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ("metric", "reference_source", "observed_source", "tolerance_source")):
            raise ValueError("comparison rows need metric and three explicit provenance fields")
        ref, actual, tolerance = (float(row[k]) for k in ("reference", "observed", "absolute_tolerance"))
        if not all(math.isfinite(x) for x in (ref, actual, tolerance)) or tolerance < 0:
            raise ValueError("numbers must be finite and tolerance nonnegative")
        result.append({**row, "absolute_difference": abs(actual - ref), "within_tolerance": abs(actual - ref) <= tolerance})
    out.mkdir(parents=True, exist_ok=True)
    (out / "metric_comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"rows": len(result), "within_tolerance": sum(row["within_tolerance"] for row in result)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "run", "compare"])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=Path("/app/work"))
    parser.add_argument("--out", type=Path, default=Path("/app/output"))
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    if args.command == "init":
        init(args.input, args.out)
        print(json.dumps({"initialized": True}))
    elif args.command == "run":
        print(json.dumps(run(args.input, args.work, args.out, args.plan), ensure_ascii=False))
    else:
        print(json.dumps(compare(args.plan, args.out), ensure_ascii=False))


if __name__ == "__main__":
    main()
