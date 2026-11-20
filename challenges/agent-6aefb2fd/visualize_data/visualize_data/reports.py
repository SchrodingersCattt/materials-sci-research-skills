"""Human-readable and JSON QA reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import CheckResult


def payload(results: Iterable[CheckResult]) -> dict[str, object]:
    records = [result.to_dict() for result in results]
    return {
        "passed": all(record["passed"] for record in records),
        "checks": records,
        "duration_seconds": sum(float(record["duration_seconds"]) for record in records),
    }


def print_report(results: Iterable[CheckResult]) -> dict[str, object]:
    report = payload(results)
    for record in report["checks"]:
        status = "PASS" if record["passed"] else "FAIL"
        print(f"[{status}] {record['check']} ({record['duration_seconds']:.3f}s)")
        for finding in record["findings"]:
            panel = f" [{finding['panel']}]" if finding["panel"] else ""
            print(f"  - {finding['level'].upper()}{panel} {finding['rule']}: {finding['message']}")
    print(f"Overall: {'PASS' if report['passed'] else 'FAIL'} ({report['duration_seconds']:.3f}s)")
    return report


def write_json(report: dict[str, object], path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
