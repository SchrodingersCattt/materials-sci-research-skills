"""Independent package validator: well-formedness, relationships and content types.

Written as its own tool so the deck editor is not checked by its own assumptions.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def main(path_str: str) -> int:
    path = Path(path_str)
    problems = []
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        parts = {name: package.read(name) for name in names}

    xml_parts = [n for n in names if n.endswith(".xml") or n.endswith(".rels")]
    for name in xml_parts:
        try:
            ET.fromstring(parts[name])
        except ET.ParseError as error:
            problems.append(f"malformed XML in {name}: {error}")

    # every relationship target must exist
    for name in [n for n in names if n.endswith(".rels")]:
        directory = name.rsplit("/_rels/", 1)[0] if "/_rels/" in name else ""
        try:
            root = ET.fromstring(parts[name])
        except ET.ParseError:
            continue
        for rel in root.findall(f"{{{PKG_REL}}}Relationship"):
            target = rel.get("Target") or ""
            if rel.get("TargetMode") == "External" or target.startswith(("http", "mailto")):
                continue
            resolved = target.lstrip("/") if target.startswith("/") else ""
            if not resolved:
                base = directory
                remaining = target
                while remaining.startswith("../"):
                    remaining = remaining[3:]
                    base = base.rpartition("/")[0]
                resolved = f"{base}/{remaining}" if base else remaining
            if resolved not in parts:
                problems.append(f"{name}: relationship {rel.get('Id')} -> {resolved} is missing")

    # every part must be covered by a content type (Override or matching Default extension)
    content_types = ET.fromstring(parts["[Content_Types].xml"])
    defaults = {d.get("Extension").lower() for d in content_types.findall(f"{{{CT}}}Default")}
    overrides = {o.get("PartName") for o in content_types.findall(f"{{{CT}}}Override")}
    for name in names:
        if name == "[Content_Types].xml":
            continue
        if f"/{name}" in overrides:
            continue
        if name.rsplit(".", 1)[-1].lower() in defaults:
            continue
        problems.append(f"{name} has no content type")

    # presentation -> slides
    presentation = ET.fromstring(parts["ppt/presentation.xml"])
    rels = ET.fromstring(parts["ppt/_rels/presentation.xml.rels"])
    rel_map = {rel.get("Id"): rel.get("Target") for rel in rels.findall(f"{{{PKG_REL}}}Relationship")}
    slide_ids = []
    for entry in presentation.iter("{http://schemas.openxmlformats.org/presentationml/2006/main}"
                                   "sldId"):
        slide_ids.append(entry.get(f"{{{R}}}id"))
    for rel_id in slide_ids:
        if rel_id not in rel_map:
            problems.append(f"presentation.xml references {rel_id} with no relationship")

    # slide -> layout
    for name in [n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)]:
        rels_name = f"ppt/slides/_rels/{name.split('/')[-1]}.rels"
        if rels_name not in parts:
            problems.append(f"{name} has no relationship part")
            continue
        rels_root = ET.fromstring(parts[rels_name])
        types = [rel.get("Type") for rel in rels_root.findall(f"{{{PKG_REL}}}Relationship")]
        if not any((t or "").endswith("/slideLayout") for t in types):
            problems.append(f"{name} does not point at a slide layout")

    print(f"parts={len(names)} xml_parts={len(xml_parts)} slides={len(slide_ids)}")
    for problem in problems:
        print("PROBLEM:", problem)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
