"""Mind map builder: a radial tree laid out from declared nodes, with real SVG/PNG/PDF exports.

The topic asks for a knowledge structure, not a picture: branches that trace back to the material,
a readable hierarchy, and evidence attached to the nodes that make claims. This module draws a
radial mind map from a declared tree and lays it out itself (angles, radii, text boxes), then
re-uses the shared primitive layer of `make_figure.py` for the SVG/PNG/PDF emitters.

Commands
--------
build   --spec FILE --out-prefix P   lay out and draw the map from the declared tree
verify  --prefix P --spec FILE       bind the artifacts to the spec and inspect the pixels
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_primitives():
    """Import the shared primitive layer (SVG/PNG/PDF emitters) from make_figure.py."""
    spec = importlib.util.spec_from_file_location("figure_primitives", HERE / "make_figure.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRIM = load_primitives()

LEVEL_COLOURS = ["#0f4c81", "#2b6d7f", "#3f7f4f", "#8a6134", "#7a4f86", "#b7472a"]
WORDS = re.compile(r"[A-Za-z\u4e00-\u9fff]+")


def wrap(text: str, limit: int = 22) -> list:
    """Split a label into at most `limit` characters per line, on word boundaries when possible."""
    text = str(text)
    if len(text) <= limit:
        return [text]
    lines, current = [], ""
    for token in re.findall(r"\S+\s*", text):
        if len(current) + len(token) <= limit:
            current += token
        else:
            if current.strip():
                lines.append(current.strip())
            current = token
    if current.strip():
        lines.append(current.strip())
    return lines or [text[:limit]]


def flatten(tree: dict, depth: int = 0, parent: str | None = None, out: list | None = None) -> list:
    out = [] if out is None else out
    identifier = tree.get("id") or f"n{len(out) + 1}"
    out.append({"node": tree, "id": identifier, "depth": depth, "parent": parent})
    for child in tree.get("children") or []:
        flatten(child, depth + 1, identifier, out)
    return out


def leaf_weights(entry: dict, nodes: list) -> int:
    """How many leaves hang under this node (used to size its angular wedge)."""
    children = [item for item in nodes if item["parent"] == entry["id"]]
    if not children:
        return 1
    return sum(leaf_weights(child, nodes) for child in children)


def _xml_escape(text) -> str:
    return (str("" if text is None else text)
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _children_of(nodes: list, parent) -> list:
    return [entry for entry in nodes if entry["parent"] == parent]


def write_opml(tree: dict, nodes: list, title: str, out_path: Path) -> None:
    """OPML 2.0: the format every outliner imports, so the map stays editable after the run."""
    def emit(entry: dict, depth: int) -> list:
        node = entry["node"]
        label = node.get("label") or entry["id"]
        attrs = [f'text="{_xml_escape(label)}"']
        evidence = node.get("evidence")
        if evidence:
            attrs.append(f'_note="{_xml_escape(evidence)}"')
        attrs.append(f'_locator="{_xml_escape(node.get("locator") or "")}"')
        if node.get("relation"):
            attrs.append(f'_relation="{_xml_escape(node["relation"])}"')
        pad = "  " * depth
        lines = [f"{pad}<outline {' '.join(attrs)}>"]
        for child in _children_of(nodes, entry["id"]):
            lines.extend(emit(child, depth + 1))
        lines.append(f"{pad}</outline>")
        return lines

    body = emit(nodes[0], 2)
    out_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<opml version="2.0">\n'
        "  <head>\n"
        f"    <title>{_xml_escape(title)}</title>\n"
        "  </head>\n"
        "  <body>\n" + "\n".join(body) + "\n"
        "  </body>\n"
        "</opml>\n", encoding="utf-8")


def write_freemind(tree: dict, nodes: list, title: str, out_path: Path) -> None:
    """FreeMind .mm: the other format mind-map editors import, with evidence as a note."""
    def emit(entry: dict, depth: int) -> list:
        node = entry["node"]
        label = node.get("label") or entry["id"]
        pad = "  " * depth
        bits = [f'TEXT="{_xml_escape(label)}"']
        if node.get("locator"):
            bits.append(f'POSITION="right"')
        lines = [f'{pad}<node {" ".join(bits)}>']
        note = node.get("evidence")
        if note:
            lines.append(f"{pad}  <richcontent TYPE=\"NOTE\"><html><body><p>"
                         f"{_xml_escape(note)}</p></body></html></richcontent>")
        lines.append(f"{pad}  <font NAME=\"SansSerif\" SIZE=\"12\"/>")
        for child in _children_of(nodes, entry["id"]):
            lines.extend(emit(child, depth + 1))
        lines.append(f"{pad}</node>")
        return lines

    body = emit(nodes[0], 1)
    out_path.write_text(
        '<map version="1.0.1">\n'
        "<!-- Generated mind map. Open in FreeMind, XMind, MindManager, or any .mm reader. -->\n"
        + "\n".join(body) + "\n"
        "</map>\n", encoding="utf-8")


def build_mindmap(spec: dict, out_prefix: Path) -> dict:
    tree = spec.get("root")
    if not tree:
        raise SystemExit("the spec declares no root node")
    width = int(spec.get("width") or 1100)
    height = int(spec.get("height") or 760)
    centre = (width / 2, height / 2 + 10)
    nodes = flatten(tree)
    depth_of = {entry["id"]: entry["depth"] for entry in nodes}
    max_depth = max(entry["depth"] for entry in nodes) or 1

    # --- box sizes first: the layout has to respect the text it must hold ---
    sizes = {}
    for entry in nodes:
        depth = entry["depth"]
        lines = wrap(entry["node"].get("label") or entry["id"], 20 if depth else 26)
        widest = max(len(line) for line in lines)
        sizes[entry["id"]] = {
            "w": max(96.0, widest * (7.6 if depth else 9.2) + 24),
            "h": 20.0 + len(lines) * 15,
        }
    widest_box = max(size["w"] for size in sizes.values())

    # --- wedge allocation: each subtree owns an angular span proportional to its leaves ---
    for entry in nodes:
        entry["weight"] = leaf_weights(entry, nodes)
    root_weight = max(leaf_weights(nodes[0], nodes), 1)
    leaves = [entry for entry in nodes if not any(item["parent"] == entry["id"] for item in nodes)]
    smallest_wedge = 2 * math.pi * min(entry["weight"] for entry in leaves) / root_weight
    # Radius so that two neighbouring leaves at the deepest level keep their boxes apart.
    needed = (widest_box + 26) / (2 * math.sin(max(smallest_wedge, 1e-3) / 2))
    radius_step = min(max(needed / max_depth, 150.0),
                      (min(width, height) / 2 - 60) / max_depth)

    def assign(entry: dict, start: float, end: float) -> None:
        entry["angle"] = (start + end) / 2
        radius = radius_step * entry["depth"]
        entry["x"] = centre[0] + math.cos(entry["angle"]) * radius
        entry["y"] = centre[1] + math.sin(entry["angle"]) * radius
        children = [item for item in nodes if item["parent"] == entry["id"]]
        if not children:
            return
        total = sum(child["weight"] for child in children)
        cursor = start
        for child in children:
            span = (end - start) * child["weight"] / total
            assign(child, cursor, cursor + span)
            cursor += span

    assign(nodes[0], 0.0, 2 * math.pi)

    PRIM.reset_primitives()
    if spec.get("title"):
        PRIM.text(width / 2, 26, spec["title"], size=16, colour="#111111", anchor="middle",
                  weight="bold")

    boxes = {}
    for entry in nodes:
        size = sizes[entry["id"]]
        boxes[entry["id"]] = {"x": entry["x"] - size["w"] / 2, "y": entry["y"] - size["h"] / 2,
                              "w": size["w"], "h": size["h"]}

    # edges first, so the boxes sit on top
    for entry in nodes:
        if entry["depth"] == 0:
            continue
        parent = boxes[entry["parent"]]
        child = boxes[entry["id"]]
        start = (parent["x"] + parent["w"] / 2, parent["y"] + parent["h"] / 2)
        end = (child["x"] + child["w"] / 2, child["y"] + child["h"] / 2)
        mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        PRIM.polyline([start, mid, end],
                      stroke=LEVEL_COLOURS[entry["depth"] % len(LEVEL_COLOURS)],
                      width=max(2.6 - 0.5 * entry["depth"], 1.0))
        label = entry["node"].get("edge")
        if label:
            PRIM.text(mid[0], mid[1] - 6, label, size=11.5, colour="#404040", anchor="middle")

    for entry in nodes:
        node, depth = entry["node"], entry["depth"]
        box = boxes[entry["id"]]
        colour = LEVEL_COLOURS[depth % len(LEVEL_COLOURS)]
        PRIM.rect(box["x"], box["y"], box["w"], box["h"],
                  fill="#eef4fb" if depth == 0 else "#ffffff", stroke=colour,
                  width=2.0 if depth <= 1 else 1.2)
        lines = wrap(node.get("label") or entry["id"], 20 if depth else 26)
        for index, line in enumerate(lines):
            PRIM.text(entry["x"], entry["y"] - (len(lines) - 1) * 7.5 + index * 15 + 4, line,
                      size=14 if depth == 0 else (12.5 if depth == 1 else 11.5),
                      colour="#0f172a", anchor="middle",
                      weight="bold" if depth == 0 else "normal")
        if node.get("evidence"):
            PRIM.text(entry["x"], box["y"] + box["h"] + 12, f"[{node['evidence']}]", size=10,
                      colour="#4b5563", anchor="middle")

    if spec.get("caption"):
        PRIM.text(width / 2, height - 12, spec["caption"], size=12, colour="#404040",
                  anchor="middle")

    svg = PRIM.to_svg(width, height)
    png_bytes, rasterizer = PRIM.render_png(width, height)
    pdf_bytes = PRIM.to_pdf(width, height)
    (out_prefix.with_suffix(".svg")).write_text(svg, encoding="utf-8")
    (out_prefix.with_suffix(".png")).write_bytes(png_bytes)
    (out_prefix.with_suffix(".pdf")).write_bytes(pdf_bytes)

    overlaps = []
    items = list(boxes.items())
    for index, (first_id, first) in enumerate(items):
        for second_id, second in items[index + 1:]:
            if (first["x"] < second["x"] + second["w"] and second["x"] < first["x"] + first["w"]
                    and first["y"] < second["y"] + second["h"]
                    and second["y"] < first["y"] + first["h"]):
                overlaps.append({"a": first_id, "b": second_id})
    outside = [identifier for identifier, box in boxes.items()
               if box["x"] < 0 or box["y"] < 0
               or box["x"] + box["w"] > width or box["y"] + box["h"] > height]
    without_evidence = [entry["id"] for entry in nodes
                        if entry["depth"] >= 2 and not entry["node"].get("evidence")]
    # Editable formats matter as much as the picture: the case asks for a mind map that can keep
    # being edited, and an SVG is not what a mind-map editor opens.
    opml_path = out_prefix.with_suffix(".opml")
    mm_path = out_prefix.with_suffix(".mm")
    write_opml(tree, nodes, spec.get("title") or "Mind map", opml_path)
    write_freemind(tree, nodes, spec.get("title") or "Mind map", mm_path)

    return {
        "schema": "mindmap-build/v1",
        "kind": "mindmap",
        "out": {"svg": str(out_prefix.with_suffix(".svg")),
                "png": str(out_prefix.with_suffix(".png")),
                "pdf": str(out_prefix.with_suffix(".pdf")),
                "opml": str(opml_path),
                "mm": str(mm_path)},
        "sha256": {suffix: hashlib.sha256(out_prefix.with_suffix(suffix).read_bytes()).hexdigest()
                   for suffix in (".svg", ".png", ".pdf", ".opml", ".mm")},
        "rasterizer": rasterizer,
        "size": {"width": width, "height": height},
        "node_count": len(nodes),
        "branch_count": len({entry["parent"] for entry in nodes if entry["parent"]}),
        "max_depth": max_depth,
        "radius_step": round(radius_step, 1),
        "nodes": [{"id": entry["id"], "depth": entry["depth"], "parent": entry["parent"],
                   "label": entry["node"].get("label"), "evidence": entry["node"].get("evidence"),
                   "x": round(entry["x"], 1), "y": round(entry["y"], 1),
                   "angle_deg": round(math.degrees(entry.get("angle", 0.0)), 1)} for entry in nodes],
        "layout": {
            "node_overlaps": overlaps[:12],
            "overlap_count": len(overlaps),
            "nodes_outside_canvas": outside,
            "deep_nodes_without_evidence": without_evidence,
            "method": "radial tree with wedge allocation: each subtree owns an angular span "
                      "proportional to its leaf count, so sibling branches cannot cross; the radius "
                      "is derived from the widest box and the smallest leaf wedge; labels wrap at 20 "
                      "characters. Geometry is checked by axis-aligned box intersection and the PNG "
                      "is inspected separately.",
        },
    }


def verify(prefix: Path, spec: dict, outdir: Path) -> dict:
    checks = []

    def add(check_id, requirement, ok, evidence, locator):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence,
                       "locator": locator})

    for suffix in (".svg", ".png", ".pdf", ".opml", ".mm"):
        path = prefix.with_suffix(suffix)
        exists = path.exists() and path.stat().st_size > 0
        add(f"artifact{suffix}", f"{suffix} artifact exists and is non-empty", exists,
            f"bytes={path.stat().st_size if path.exists() else 0}", str(path))
        if exists:
            signature = {".svg": b"<svg", ".png": b"\x89PNG", ".pdf": b"%PDF",
                         ".opml": b"<?xml", ".mm": b"<map"}[suffix]
            add(f"format{suffix}", f"{suffix} starts with the real signature",
                path.read_bytes()[:16].lstrip().startswith(signature), "signature check", str(path))

    report_path = prefix.with_name(prefix.name + ".build-report.json")
    build_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    add("layout_clean", "no node overlaps and nothing outside the canvas",
        build_report.get("layout", {}).get("overlap_count") == 0
        and not build_report.get("layout", {}).get("nodes_outside_canvas"),
        f"overlaps={build_report.get('layout', {}).get('overlap_count')} "
        f"outside={build_report.get('layout', {}).get('nodes_outside_canvas')}", str(report_path))

    svg_path = prefix.with_suffix(".svg")
    labels = []
    for entry in flatten(spec.get("root") or {}):
        label = entry["node"].get("label")
        if label:
            labels.extend(wrap(label, 20 if entry["depth"] else 26))
    if svg_path.exists():
        svg_text = svg_path.read_text(encoding="utf-8")
        missing = [line for line in labels if line not in svg_text]
        add("labels_drawn", "every declared label appears in the drawing", not missing,
            f"missing={missing[:6]} of {len(labels)} label lines", str(svg_path))

    png_path = prefix.with_suffix(".png")
    if png_path.exists():
        info = PRIM.inspect_png(png_path)
        add("png_not_blank", "the PNG contains drawn content", not info["is_blank"],
            f"ink_coverage={info['ink_coverage']}", str(png_path))
        add("png_inside_canvas", "no ink is clipped at the canvas edge",
            not info["touches_edges"], f"ink_bbox={info['ink_bbox']}", str(png_path))

    # The editable file must contain the same nodes, or "editable" is a claim rather than a fact.
    for suffix, open_tag in ((".opml", "<outline"), (".mm", "<node ")):
        path = prefix.with_suffix(suffix)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        drawn = sum(1 for entry in flatten(spec.get("root") or {})
                    if (entry["node"].get("label") or entry["id"]))
        found = text.count(open_tag)
        add(f"editable{suffix}_complete",
            f"the {suffix} file carries every node of the tree",
            found == drawn, f"nodes_in_file={found} nodes_in_spec={drawn}", str(path))

    failures = [c for c in checks if c["status"] == "fail"]
    report = {"schema": "mindmap-verify/v1", "checks": checks,
              "passed": len(checks) - len(failures), "failed": len(failures),
              "status": "verified" if not failures else "needs_work",
              "scope_note": "Proves the layout is clean, the labels were drawn and the exports are "
                            "real. It does not judge whether the knowledge structure is the right "
                            "one for the material."}
    Path(outdir).mkdir(parents=True, exist_ok=True)
    (Path(outdir) / f"{prefix.name}.verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Radial mind map builder")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build")
    p.add_argument("--spec", required=True)
    p.add_argument("--out-prefix", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--prefix", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--outdir", required=True)
    args = parser.parse_args(argv)
    if args.command == "build":
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        prefix = Path(args.out_prefix)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        report = build_mindmap(spec, prefix)
        report_path = prefix.with_name(prefix.name + ".build-report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"kind": report["kind"], "nodes": report["node_count"],
                          "branches": report["branch_count"],
                          "layout_issues": report["layout"]["overlap_count"],
                          "out": report["out"], "rasterizer": report["rasterizer"]},
                         ensure_ascii=False))
        return 0
    if args.command == "verify":
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        report = verify(Path(args.prefix), spec, Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
