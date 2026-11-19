"""Self-test for the mind-map builder.

Positive path: the fixture tree lays out with no overlaps, nothing outside the canvas, every label
drawn, and real SVG/PNG/PDF exports that verify.
Negative paths: a spec with no root must be refused, and a tree whose boxes cannot fit the canvas at
the declared size must report nodes outside the canvas rather than silently clipping them.
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
TOOL = CANDIDATE / "scripts" / "make_mindmap.py"
FIXTURE = CANDIDATE / "examples" / "synthetic_case.py"


def run(args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


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
    spec_path = fixture / "mindmap-spec.json"
    out = work / "out"

    build = run([str(TOOL), "build", "--spec", str(spec_path), "--out-prefix", str(out / "map")])
    if build.returncode != 0:
        failures.append(f"build failed: {build.stdout} {build.stderr[:300]}")
    else:
        report = json.loads((out / "map.build-report.json").read_text(encoding="utf-8"))
        if report["node_count"] != 14:
            failures.append(f"expected 14 nodes, got {report['node_count']}")
        if report["layout"]["overlap_count"]:
            failures.append(f"the fixture map has overlapping nodes: "
                            f"{report['layout']['node_overlaps'][:3]}")
        if report["layout"]["nodes_outside_canvas"]:
            failures.append(f"nodes outside the canvas: {report['layout']['nodes_outside_canvas']}")
        if report["layout"]["deep_nodes_without_evidence"]:
            failures.append(f"deep nodes without an evidence locator: "
                            f"{report['layout']['deep_nodes_without_evidence']}")
        checked = run([str(TOOL), "verify", "--prefix", str(out / "map"), "--spec", str(spec_path),
                       "--outdir", str(out)])
        if checked.returncode != 0:
            verification = json.loads((out / "map.verification.json").read_text(encoding="utf-8"))
            failures.append(f"verification failed: "
                            f"{[c['id'] for c in verification['checks'] if c['status'] == 'fail']}")

    # --- negative paths -------------------------------------------------------
    empty = dict(json.loads(spec_path.read_text(encoding="utf-8")))
    empty.pop("root")
    empty_path = work / "no-root.json"
    empty_path.write_text(json.dumps(empty, ensure_ascii=False), encoding="utf-8")
    refused = run([str(TOOL), "build", "--spec", str(empty_path), "--out-prefix", str(out / "bad")])
    if refused.returncode == 0 or "no root node" not in (refused.stdout + refused.stderr):
        failures.append("a spec with no root was not refused")

    tiny = json.loads(spec_path.read_text(encoding="utf-8"))
    tiny["width"], tiny["height"] = 420, 300
    tiny_path = work / "tiny.json"
    tiny_path.write_text(json.dumps(tiny, ensure_ascii=False), encoding="utf-8")
    built_tiny = run([str(TOOL), "build", "--spec", str(tiny_path), "--out-prefix", str(out / "tiny")])
    if built_tiny.returncode == 0:
        tiny_report = json.loads((out / "tiny.build-report.json").read_text(encoding="utf-8"))
        if not (tiny_report["layout"]["nodes_outside_canvas"]
                or tiny_report["layout"]["overlap_count"]):
            failures.append("a canvas too small for the tree reported no layout problem")
    else:
        failures.append("building on a small canvas raised instead of reporting the layout problem")

    print(json.dumps({
        "fixture": str(fixture),
        "checks": 10,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not a formal case, not an official result.",
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
