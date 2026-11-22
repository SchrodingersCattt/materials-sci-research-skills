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
        diagram_result = json.loads((out / "diagram.verification.json").read_text(encoding="utf-8"))
        if checked.returncode != 0:
            failed = [c["id"] for c in diagram_result["checks"] if c["status"] == "fail"]
            failures.append(f"diagram verification failed: {failed}")
        # The diagram branch must actually assert the diagram's own claims, not just that a file
        # exists, so a spec that declares semantics has to produce these checks.
        required = {"drawio_parents_resolve", "drawio_edges_wired", "provenance_traceable",
                    "provenance_matches_artwork", "element_classes_declared",
                    "legend_covers_classes", "polarity_distinguishable_in_artwork",
                    "declared_values_carry_units"}
        present = {c["id"] for c in diagram_result["checks"]}
        absent = sorted(required - present)
        if absent:
            failures.append(f"diagram verification skipped checks: {absent}")
        for check_id in sorted(required & present):
            if next(c for c in diagram_result["checks"] if c["id"] == check_id)["status"] != "pass":
                failures.append(f"diagram check did not pass on a good diagram: {check_id}")
        inspection = run([str(FIGURE), "inspect-png", str(diagram_prefix.with_suffix(".png"))])
        if inspection.returncode != 0:
            failures.append("PNG inspection failed")
        else:
            payload = json.loads(inspection.stdout)
            if payload["is_blank"]:
                failures.append("the diagram PNG came out blank")
            if payload["touches_edges"]:
                failures.append(f"the diagram PNG is clipped: {payload['ink_bbox']}")

        # --- negative controls for the diagram checks -------------------------
        # Each of these breaks exactly one thing in a copy of the real bundle and asserts that the
        # matching check notices. A check that cannot fail is not evidence.
        def diagram_negative(name, check_id, mutate, spec_override=None):
            prefix = out / f"neg-{name}"
            for suffix in (".svg", ".png", ".pdf", ".drawio", ".build-report.json",
                           ".provenance.csv"):
                source = diagram_prefix.with_name(diagram_prefix.name + suffix)
                if source.exists():
                    shutil.copyfile(source, prefix.with_name(prefix.name + suffix))
            spec_path = fixture / "diagram-spec.json"
            if spec_override is not None:
                spec_path = work / f"neg-{name}-spec.json"
                spec_path.write_text(json.dumps(spec_override, ensure_ascii=False), encoding="utf-8")
            mutate(prefix)
            result = run([str(FIGURE), "verify", "--prefix", str(prefix), "--spec", str(spec_path),
                          "--outdir", str(out)])
            report = json.loads((out / f"{prefix.name}.verification.json").read_text(encoding="utf-8"))
            row = next((c for c in report["checks"] if c["id"] == check_id), None)
            if row is None:
                failures.append(f"negative control {name}: check {check_id} was not emitted")
            elif row["status"] != "fail":
                failures.append(f"negative control {name}: {check_id} did not fail")
            elif result.returncode == 0:
                failures.append(f"negative control {name}: exit code stayed 0 despite a failure")

        def orphan_parent(prefix):
            path = prefix.with_suffix(".drawio")
            path.write_text(path.read_text(encoding="utf-8").replace('parent="layer-nodes"',
                                                                    'parent="layer-gone"'),
                            encoding="utf-8")

        def unwire_edge(prefix):
            path = prefix.with_suffix(".drawio")
            path.write_text(path.read_text(encoding="utf-8").replace(
                'source="node-ligand"', 'source="node-missing"'), encoding="utf-8")

        def blank_locator(prefix):
            path = prefix.with_name(prefix.name + ".provenance.csv")
            rows = path.read_text(encoding="utf-8").splitlines()
            cells = rows[1].split(",")
            cells[-1] = '""'
            rows[1] = ",".join(cells)
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")

        def undraw_element(prefix):
            path = prefix.with_suffix(".svg")
            path.write_text(path.read_text(encoding="utf-8").replace("kinase K", "kinase Z"),
                            encoding="utf-8")

        def collapse_polarity_ink(prefix):
            # Simulate a renderer that lost the polarity distinction: the declared polarities stay
            # in the spec, but the artwork paints every relation with the positive colour.
            path = prefix.with_suffix(".svg")
            path.write_text(path.read_text(encoding="utf-8").replace("#b91c1c", "#15803d"),
                            encoding="utf-8")

        def drop_polarity_from_key(spec):
            spec = json.loads(json.dumps(spec))
            spec["relation_key"] = {"activate": "activation"}
            return spec

        def strip_unit(spec):
            spec = json.loads(json.dumps(spec))
            for node in spec["nodes"]:
                node.pop("unit", None)
            return spec

        diagram_negative("orphan-parent", "drawio_parents_resolve", orphan_parent)
        diagram_negative("unwired-edge", "drawio_edges_wired", unwire_edge)
        diagram_negative("blank-locator", "provenance_traceable", blank_locator)
        diagram_negative("undrawn-element", "provenance_matches_artwork", undraw_element)
        diagram_negative("polarity-key-dropped", "relation_key_present", lambda p: None,
                         spec_override=drop_polarity_from_key(diagram_spec))
        diagram_negative("polarity-collapsed", "polarity_distinguishable_in_artwork",
                         collapse_polarity_ink)
        diagram_negative("unit-stripped", "declared_values_carry_units", lambda p: None,
                         spec_override=strip_unit(diagram_spec))

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
