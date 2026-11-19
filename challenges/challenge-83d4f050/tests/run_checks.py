"""Self-test for the figure builder: three chart kinds, a diagram, and honest refusals.

Positive path: build bar/line/scatter charts and a diagram from declared data, then verify each
artifact (real signatures, decoded pixels, every declared mark drawn, every value inside the axis).

Negative paths:
  * a spec naming a column the data does not have must be refused
  * a declared value outside the axis range must fail verification
  * a diagram with two overlapping nodes must report the overlap
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent
FIGURE = CANDIDATE / "scripts" / "make_figure.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    work = Path(args.workdir)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    fixture = work / "fixture"

    failures: list[str] = []
    if run([str(FIXTURE), "--outdir", str(fixture)]).returncode != 0:
        print("fixture build failed")
        return 1

    chart_spec = json.loads((fixture / "chart-spec.json").read_text(encoding="utf-8"))
    chart_spec["data"] = str(fixture / "data.csv")
    out = work / "out"
    verification = {}
    for kind in ("bar", "line", "scatter"):
        spec = dict(chart_spec, kind=kind)
        spec_path = work / f"chart-{kind}.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        prefix = out / f"chart-{kind}"
        build = run([str(FIGURE), "chart", "--spec", str(spec_path), "--out-prefix", str(prefix)])
        if build.returncode != 0:
            failures.append(f"{kind} chart build failed: {build.stdout} {build.stderr[:300]}")
            continue
        checked = run([str(FIGURE), "verify", "--prefix", str(prefix), "--spec", str(spec_path),
                       "--outdir", str(out)])
        result = json.loads((out / f"chart-{kind}.verification.json").read_text(encoding="utf-8"))
        verification[kind] = result
        if checked.returncode != 0:
            failures.append(f"{kind} chart verification failed: "
                            f"{[c['id'] for c in result['checks'] if c['status'] == 'fail']}")
        build_report = json.loads((out / f"chart-{kind}.build-report.json").read_text(encoding="utf-8"))
        if build_report["layout"]["issue_count"]:
            failures.append(f"{kind} chart has layout issues: {build_report['layout']['issues'][:2]}")
        if not build_report.get("marks"):
            failures.append(f"{kind} chart declared no marks to check in the pixels")

    diagram_spec = json.loads((fixture / "diagram-spec.json").read_text(encoding="utf-8"))
    diagram_prefix = out / "diagram"
    build = run([str(FIGURE), "diagram", "--spec", str(fixture / "diagram-spec.json"),
                 "--out-prefix", str(diagram_prefix)])
    if build.returncode != 0:
        failures.append(f"diagram build failed: {build.stdout} {build.stderr[:300]}")
    else:
        checked = run([str(FIGURE), "verify", "--prefix", str(diagram_prefix),
                       "--spec", str(fixture / "diagram-spec.json"), "--outdir", str(out)])
        if checked.returncode != 0:
            failures.append("diagram verification failed")
        inspection = run([str(FIGURE), "inspect-png", str(diagram_prefix.with_suffix(".png"))])
        if inspection.returncode != 0:
            failures.append("PNG inspection failed")
        else:
            payload = json.loads(inspection.stdout)
            if payload["is_blank"]:
                failures.append("the diagram PNG came out blank")
            if payload["touches_edges"]:
                failures.append(f"the diagram PNG is clipped: {payload['ink_bbox']}")

    # --- negative paths -------------------------------------------------------
    bad_spec = dict(chart_spec, value="no_such_column")
    bad_path = work / "bad-column.json"
    bad_path.write_text(json.dumps(bad_spec, ensure_ascii=False), encoding="utf-8")
    refused = run([str(FIGURE), "chart", "--spec", str(bad_path), "--out-prefix", str(out / "bad")])
    if refused.returncode == 0 or "no_such_column" not in (refused.stdout + refused.stderr):
        failures.append("a spec naming a missing column was not refused")

    outside = dict(chart_spec, kind="bar")
    outside_prefix = out / "outside"
    build = run([str(FIGURE), "chart", "--spec", str(work / "chart-bar.json"),
                 "--out-prefix", str(outside_prefix)])
    if build.returncode == 0:
        build_report_path = outside_prefix.with_name(outside_prefix.name + ".build-report.json")
        report = json.loads(build_report_path.read_text(encoding="utf-8"))
        # forge a mark far outside the drawn axis, as a wrong declaration would
        report["marks"].append({"series": "forged", "category": "A", "value": 9999.0,
                                "x": 100, "y": 10})
        build_report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
        checked = run([str(FIGURE), "verify", "--prefix", str(outside_prefix),
                       "--spec", str(work / "chart-bar.json"), "--outdir", str(out)])
        result = json.loads((out / "outside.verification.json").read_text(encoding="utf-8"))
        failed_ids = [c["id"] for c in result["checks"] if c["status"] == "fail"]
        if checked.returncode == 0 or "values_inside_axis" not in failed_ids:
            failures.append(f"a value outside the axis was not caught: {failed_ids}")

    overlap_spec = json.loads(json.dumps(diagram_spec))
    overlap_spec["nodes"][1]["x"] = overlap_spec["nodes"][0]["x"]
    overlap_spec["nodes"][1]["y"] = overlap_spec["nodes"][0]["y"]
    overlap_path = work / "overlap.json"
    overlap_path.write_text(json.dumps(overlap_spec, ensure_ascii=False), encoding="utf-8")
    build = run([str(FIGURE), "diagram", "--spec", str(overlap_path),
                 "--out-prefix", str(out / "overlap")])
    if build.returncode == 0:
        report = json.loads((out / "overlap.build-report.json").read_text(encoding="utf-8"))
        if report["layout"]["issue_count"] == 0:
            failures.append("overlapping nodes were not reported")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": sum(len(v.get("checks", [])) for v in verification.values()),
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
