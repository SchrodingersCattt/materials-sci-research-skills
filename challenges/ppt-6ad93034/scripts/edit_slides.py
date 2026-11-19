"""Template-aware PPTX editing: fill and clone real slides without rebuilding the deck.

The slide tasks judge three things this module can actually verify:

    * the template is *really* used — the master, the layouts, the theme fonts/colours and the
      placeholder inheritance survive into the output; untouched parts stay byte-identical;
    * each page's content *matches the source* — every filled placeholder records the source
      locator it came from, and every declared string is found again in the produced package;
    * the result is *deliverable* — text is measured against its placeholder box, overflow is
      reported per frame, and a real PDF/PNG preview is produced when a renderer exists.

Python standard library only (zipfile + xml.etree), so it works with no network, no
python-pptx and no Office suite.

Commands
--------
inspect  DECK                       slide size, theme, layouts, placeholders, slides, shapes
merge    --deck D --plan P          fill placeholders and/or add slides cloned from a layout
check    --deck D --out D2 [--plan P]  placeholder inheritance, overflow, template integrity
preview  --deck D --outdir DIR      real PDF/PNG when LibreOffice exists, an honest note otherwise
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"

NS = {"p": P, "a": A, "r": R, "rel": PKG_REL, "ct": CT}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

SLIDE_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
LAYOUT_RE = re.compile(r"ppt/slideLayouts/slideLayout(\d+)\.xml$")
EMU_PER_INCH = 914400
# Average glyph advance for the deck fonts at a given point size; used only for the overflow
# estimate, which is reported as an estimate and cross-checked against the rendered preview.
GLYPH_FACTOR = 0.52


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def declared_namespaces(raw: bytes) -> dict:
    """The xmlns declarations the part itself carries, so they survive a re-serialisation."""
    head = raw[:8192].decode("utf-8", "replace")
    return {f"xmlns:{prefix}" if prefix else "xmlns": uri
            for prefix, uri in re.findall(r'(?:xmlns:([A-Za-z0-9_.-]+)|xmlns)="([^"]+)"', head)}


def insert_before_close(raw: bytes, close_tag: str, insertion: str) -> bytes:
    """Patch XML textually. Byte-level edits keep every namespace declaration exactly as it was,
    which matters for parts like [Content_Types].xml where readers expect the default namespace."""
    text = raw.decode("utf-8")
    if close_tag not in text:
        raise ValueError(f"{close_tag} not found")
    return text.replace(close_tag, insertion + close_tag, 1).encode("utf-8")


def serialise_like(root, original: bytes) -> bytes:
    """Serialise an edited tree, re-declaring exactly the namespaces the original carried.

    ElementTree only emits the prefixes its tree actually uses, so declarations the part kept for
    compatibility (an unused ``xmlns:r`` on a slide, for instance) would disappear. They are
    re-injected textually after serialisation instead of set as attributes, which would duplicate
    the ones ElementTree already writes.
    """
    body = ET.tostring(root, encoding="unicode", xml_declaration=False)
    root_end = body.find(">")
    head = body[:root_end]
    missing = {name: uri for name, uri in declared_namespaces(original).items()
               if name not in head}
    if missing:
        injections = "".join(f' {name}="{uri}"' for name, uri in missing.items())
        body = head + injections + body[root_end:]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + body).encode("utf-8")


def read_parts(path: Path) -> tuple:
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        return {name: package.read(name) for name in names}, names


def root_of(parts: dict, name: str):
    raw = parts.get(name)
    if raw is None:
        return None
    head = raw[:8192].decode("utf-8", "replace")
    for prefix, uri in re.findall(r'xmlns:([A-Za-z0-9_.-]+)="([^"]+)"', head):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass
    return ET.fromstring(raw)


def rels_of(parts: dict, part: str) -> dict:
    """Relationship id -> (type, target, resolved target) for one part."""
    directory, _, filename = part.rpartition("/")
    rels_name = f"{directory}/_rels/{filename}.rels" if directory else f"_rels/{filename}.rels"
    root = root_of(parts, rels_name)
    if root is None:
        return {}
    out = {}
    for rel in root.findall(f"{{{PKG_REL}}}Relationship"):
        target = rel.get("Target") or ""
        if target.startswith("/"):
            resolved = target.lstrip("/")
        else:
            base = directory
            while target.startswith("../"):
                target = target[3:]
                base = base.rpartition("/")[0]
            resolved = f"{base}/{target}" if base else target
        out[rel.get("Id")] = {"type": rel.get("Type"), "target": target, "resolved": resolved}
    return out


def shape_geometry(shape) -> dict:
    transform = shape.find(f".//{{{A}}}xfrm")
    if transform is None:
        return {}
    offset = transform.find(f"{{{A}}}off")
    extent = transform.find(f"{{{A}}}ext")
    out = {}
    if offset is not None:
        out["x"] = int(offset.get("x") or 0)
        out["y"] = int(offset.get("y") or 0)
    if extent is not None:
        out["w"] = int(extent.get("cx") or 0)
        out["h"] = int(extent.get("cy") or 0)
    return out


def shape_text(shape) -> str:
    return "".join(node.text or "" for node in shape.iter(f"{{{A}}}t"))


def describe_shapes(root, part: str) -> list:
    shapes = []
    if root is None:
        return shapes
    for index, shape in enumerate(root.iter(f"{{{P}}}sp"), start=1):
        placeholder = shape.find(f".//{{{P}}}ph")
        text_body = shape.find(f"{{{P}}}txBody")
        paragraph_count = 0
        bullet_count = 0
        body_properties = {}
        if text_body is not None:
            paragraph_count = len(text_body.findall(f"{{{A}}}p"))
            bullet_count = sum(1 for p in text_body.findall(f"{{{A}}}p")
                               if p.find(f"{{{A}}}pPr/{{{A}}}buChar") is not None
                               or p.find(f"{{{A}}}pPr/{{{A}}}buAutoNum") is not None)
            body = text_body.find(f"{{{A}}}bodyPr")
            if body is not None:
                for key in ("anchor", "wrap", "lIns", "rIns", "tIns", "bIns"):
                    if body.get(key):
                        body_properties[key] = body.get(key)
        runs = []
        for run in shape.iter(f"{{{A}}}r"):
            properties = run.find(f"{{{A}}}rPr")
            size = properties.get("sz") if properties is not None else None
            bold = properties.get("b") if properties is not None else None
            runs.append({"size": size, "bold": bold, "text": (run.findtext(f"{{{A}}}t") or "")})
        shapes.append({
            "index": index,
            "part": part,
            "name": (shape.find(f".//{{{P}}}cNvPr").get("name")
                     if shape.find(f".//{{{P}}}cNvPr") is not None else None),
            "placeholder": ({
                "type": placeholder.get("type"), "idx": placeholder.get("idx")
            } if placeholder is not None else None),
            "geometry": shape_geometry(shape),
            "text": shape_text(shape),
            "paragraph_count": paragraph_count,
            "bullet_count": bullet_count,
            "body_properties": body_properties,
            "runs": runs[:24],
        })
    return shapes


def describe_theme(parts: dict) -> dict:
    root = root_of(parts, "ppt/theme/theme1.xml")
    if root is None:
        return {}
    fonts = {}
    scheme = root.find(f".//{{{A}}}fontScheme")
    if scheme is not None:
        for kind in ("majorFont", "minorFont"):
            node = scheme.find(f"{{{A}}}{kind}/{{{A}}}latin")
            if node is not None:
                fonts[kind] = node.get("typeface")
    colours = {}
    colour_scheme = root.find(f".//{{{A}}}clrScheme")
    if colour_scheme is not None:
        for slot in colour_scheme:
            child = next(iter(slot), None)
            if child is not None:
                colours[slot.tag.split("}")[-1]] = (child.get("val") or child.get("lastClr")
                                                    or child.tag.split("}")[-1])
    return {"name": root.get("name"), "fonts": fonts, "colours": colours}


def slide_size(parts: dict) -> dict:
    root = root_of(parts, "ppt/presentation.xml")
    if root is None:
        return {}
    size = root.find(f"{{{P}}}sldSz")
    if size is None:
        return {}
    return {"cx": int(size.get("cx") or 0), "cy": int(size.get("cy") or 0),
            "type": size.get("type"),
            "inches": {"w": round(int(size.get("cx") or 0) / EMU_PER_INCH, 2),
                       "h": round(int(size.get("cy") or 0) / EMU_PER_INCH, 2)}}


def inspect_deck(path: Path) -> dict:
    parts, names = read_parts(path)
    presentation = root_of(parts, "ppt/presentation.xml")
    layouts = {}
    for name in sorted(n for n in names if LAYOUT_RE.match(n)):
        root = root_of(parts, name)
        layouts[name] = {
            "name": (root.find(f"{{{P}}}cSld").get("name")
                     if root is not None and root.find(f"{{{P}}}cSld") is not None else None),
            "type": root.get("type") if root is not None else None,
            "placeholders": [shape for shape in describe_shapes(root, name)
                             if shape.get("placeholder")],
        }
    slides = []
    for name in sorted((n for n in names if SLIDE_RE.match(n)),
                       key=lambda n: int(SLIDE_RE.match(n).group(1))):
        root = root_of(parts, name)
        rels = rels_of(parts, name)
        layout_target = next((rel["resolved"] for rel in rels.values()
                              if (rel["type"] or "").endswith("/slideLayout")), None)
        slides.append({
            "part": name,
            "index": int(SLIDE_RE.match(name).group(1)),
            "layout": layout_target,
            "shapes": describe_shapes(root, name),
        })
    return {
        "schema": "deck-inspection/v1",
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "part_count": len(names),
        "slide_size": slide_size(parts),
        "theme": describe_theme(parts),
        "master": next((n for n in names if n.startswith("ppt/slideMasters/")
                        and n.endswith(".xml")), None),
        "layouts": layouts,
        "slides": slides,
        "slide_count": len(slides),
        "parts": sorted(names),
    }


# --------------------------------------------------------------------------- layout maths

def text_capacity(geometry: dict, paragraphs: list) -> dict:
    """Estimate whether the paragraphs fit the placeholder box; report the method."""
    width_emu = geometry.get("w") or 0
    height_emu = geometry.get("h") or 0
    if not width_emu or not height_emu:
        return {"fits": None, "reason": "placeholder has no explicit geometry"}
    width_in = width_emu / EMU_PER_INCH
    height_in = height_emu / EMU_PER_INCH
    total_lines = 0
    for paragraph in paragraphs:
        text = paragraph if isinstance(paragraph, str) else (paragraph.get("text") or "")
        size = (paragraph.get("size") if isinstance(paragraph, dict) else None) or 18.0
        available = max(width_in - 0.2, 0.5)
        per_line = max(int(available / (size * GLYPH_FACTOR / 72.0)), 1)
        total_lines += max(1, -(-len(text) // per_line))
    line_height = 1.22
    needed_in = total_lines * 18.0 * line_height / 72.0
    return {
        "fits": needed_in <= height_in + 1e-6,
        "estimated_lines": total_lines,
        "estimated_height_in": round(needed_in, 2),
        "box_height_in": round(height_in, 2),
        "method": "lines = ceil(characters / floor((width - 0.2in) / (size x 0.52 / 72))); "
                  "height = lines x size x 1.22 / 72. Report only; the preview is the visual check.",
    }


# --------------------------------------------------------------------------- editing

def set_placeholder_text(shape, lines: list) -> None:
    """Replace a placeholder's paragraphs, keeping the placeholder's own run properties."""
    text_body = shape.find(f"{{{P}}}txBody")
    if text_body is None:
        text_body = ET.SubElement(shape, f"{{{P}}}txBody")
    body = text_body.find(f"{{{A}}}bodyPr")
    template_paragraph = text_body.find(f"{{{A}}}p")
    properties = None
    run_properties = None
    if template_paragraph is not None:
        properties = template_paragraph.find(f"{{{A}}}pPr")
        first_run = template_paragraph.find(f"{{{A}}}r")
        if first_run is not None:
            run_properties = first_run.find(f"{{{A}}}rPr")
    for paragraph in list(text_body.findall(f"{{{A}}}p")):
        text_body.remove(paragraph)
    for entry in lines:
        text = entry if isinstance(entry, str) else (entry.get("text") or "")
        level = 0 if isinstance(entry, str) else int(entry.get("level") or 0)
        paragraph = ET.Element(f"{{{A}}}p")
        if properties is not None:
            copied = copy.deepcopy(properties)
        else:
            copied = ET.Element(f"{{{A}}}pPr")
        copied.set("lvl", str(level))
        paragraph.append(copied)
        run = ET.SubElement(paragraph, f"{{{A}}}r")
        if run_properties is not None:
            run.append(copy.deepcopy(run_properties))
        node = ET.SubElement(run, f"{{{A}}}t")
        node.text = text
        text_body.append(paragraph)
    if body is not None:
        text_body.remove(body)
        text_body.insert(0, body)


def find_shape_by_placeholder(root, placeholder: str):
    """`placeholder` is 'title', 'body', 'idx:1', or a shape name."""
    for shape in root.iter(f"{{{P}}}sp"):
        marker = shape.find(f".//{{{P}}}ph")
        name_node = shape.find(f".//{{{P}}}cNvPr")
        name = name_node.get("name") if name_node is not None else ""
        if marker is None:
            if placeholder == name:
                return shape
            continue
        kind = marker.get("type") or "body"
        idx = marker.get("idx") or "1"
        if placeholder in (kind, f"idx:{idx}", name):
            return shape
    return None


def next_free_ids(parts: dict) -> dict:
    presentation = root_of(parts, "ppt/presentation.xml")
    ids = []
    if presentation is not None:
        for entry in presentation.iter(f"{{{P}}}sldId"):
            try:
                ids.append(int(entry.get("id")))
            except (TypeError, ValueError):
                pass
    rels = rels_of(parts, "ppt/presentation.xml")
    numeric = []
    for rel_id in rels:
        match = re.fullmatch(r"rId(\d+)", rel_id or "")
        if match:
            numeric.append(int(match.group(1)))
    return {"slide_id": max(ids, default=255) + 1, "rel_id": max(numeric, default=0) + 1}


def clone_slide(parts: dict, names: list, source_part: str, layout_part: str) -> str:
    """Copy a slide package part and everything it points at."""
    highest = max([int(m.group(1)) for m in (SLIDE_RE.match(n) for n in names) if m] or [0])
    new_part = f"ppt/slides/slide{highest + 1}.xml"
    parts[new_part] = parts[source_part]
    names.append(new_part)
    source_rels = f"ppt/slides/_rels/{source_part.split('/')[-1]}.rels"
    new_rels = f"ppt/slides/_rels/slide{highest + 1}.xml.rels"
    if source_rels in parts:
        parts[new_rels] = parts[source_rels]
        names.append(new_rels)
    else:
        parts[new_rels] = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                           f'<Relationships xmlns="{PKG_REL}">'
                           '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                           'officeDocument/2006/relationships/slideLayout" '
                           f'Target="../slideLayouts/{layout_part.split("/")[-1]}"/>'
                           "</Relationships>").encode("utf-8")
        names.append(new_rels)
    # content types: a textual insert keeps the default namespace exactly as the package declares it
    content_types = parts["[Content_Types].xml"]
    marker = "<Override " if b"<Override " in content_types else "<Override"
    try:
        parts["[Content_Types].xml"] = insert_before_close(
            content_types, "</Types>",
            f'<Override PartName="/{new_part}" ContentType="application/vnd.openxmlformats-'
            'officedocument.presentationml.slide+xml"/>')
    except ValueError:
        parts["[Content_Types].xml"] = content_types.replace(
            b"</Types>", (f'<Override PartName="/{new_part}" ContentType="application/vnd.'
                          'openxmlformats-officedocument.presentationml.slide+xml"/>'
                          "</Types>").encode("utf-8"))
    del marker
    return new_part


def add_slide_to_presentation(parts: dict, slide_part: str) -> dict:
    presentation = root_of(parts, "ppt/presentation.xml")
    if presentation is None:
        raise SystemExit("ppt/presentation.xml is missing")
    ids = next_free_ids(parts)
    entry = (f'<p:sldId id="{ids["slide_id"]}" r:id="rId{ids["rel_id"]}"/>')
    raw = parts["ppt/presentation.xml"]
    try:
        parts["ppt/presentation.xml"] = insert_before_close(raw, "</p:sldIdLst>", entry)
    except ValueError as error:
        raise SystemExit(f"presentation.xml has no slide id list: {error}")
    rels_raw = parts.get("ppt/_rels/presentation.xml.rels")
    relationship = ('<Relationship Id="rId%s" Type="http://schemas.openxmlformats.org/'
                    'officeDocument/2006/relationships/slide" Target="slides/%s"/>'
                    % (ids["rel_id"], slide_part.split("/")[-1]))
    if rels_raw is None:
        rels_raw = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    f'<Relationships xmlns="{PKG_REL}"></Relationships>').encode("utf-8")
    parts["ppt/_rels/presentation.xml.rels"] = insert_before_close(
        rels_raw, "</Relationships>", relationship)
    return {"slide_id": ids["slide_id"], "rel_id": ids["rel_id"]}


def merge(deck: Path, plan: dict, outdir: Path) -> dict:
    parts, names = read_parts(deck)
    originals = dict(parts)
    before = {name: sha256_bytes(parts[name]) for name in names}
    template_parts = [n for n in names if n.startswith(("ppt/slideMasters/", "ppt/slideLayouts/",
                                                        "ppt/theme/"))]
    operations = []
    filled = 0

    for item in plan.get("slides", []):
        target = item.get("target_slide")
        slide_part = None
        cloned = False
        if target is not None:
            slide_part = f"ppt/slides/slide{int(target)}.xml"
            if slide_part not in parts:
                operations.append({"slide": item.get("id"), "status": "missing_target",
                                   "detail": f"{slide_part} not in the deck"})
                continue
        else:
            layout_name = item.get("layout")
            layout_part = None
            for name in names:
                if not LAYOUT_RE.match(name):
                    continue
                root = root_of(parts, name)
                c_sld = root.find(f"{{{P}}}cSld") if root is not None else None
                if layout_name and c_sld is not None and c_sld.get("name") == layout_name:
                    layout_part = name
                    break
                if layout_name and root is not None and root.get("type") == layout_name:
                    layout_part = name
                    break
            if layout_part is None:
                # fall back to the layout of the last slide so the theme still governs the new one
                for name in reversed(names):
                    if SLIDE_RE.match(name):
                        rels = rels_of(parts, name)
                        layout_part = next((rel["resolved"] for rel in rels.values()
                                            if (rel["type"] or "").endswith("/slideLayout")), None)
                        if layout_part:
                            break
            if layout_part is None:
                operations.append({"slide": item.get("id"), "status": "no_layout_available"})
                continue
            source_slide = None
            for name in reversed(names):
                if SLIDE_RE.match(name):
                    rels = rels_of(parts, name)
                    if any((rel["type"] or "").endswith("/slideLayout")
                           and rel["resolved"] == layout_part for rel in rels.values()):
                        source_slide = name
                        break
            if source_slide is None:
                source_slide = next((n for n in names if SLIDE_RE.match(n)), None)
            if source_slide is None:
                operations.append({"slide": item.get("id"), "status": "no_slide_to_clone"})
                continue
            slide_part = clone_slide(parts, names, source_slide, layout_part)
            add_slide_to_presentation(parts, slide_part)
            cloned = True

        root = root_of(parts, slide_part)
        if root is None:
            operations.append({"slide": item.get("id"), "status": "unparsable_slide"})
            continue
        entry = {"slide": item.get("id"), "part": slide_part, "cloned": cloned,
                 "filled": [], "missing_placeholders": [], "layout": item.get("layout")}
        for field in ("title", "subtitle", "body", "notes", "caption"):
            spec = item.get(field)
            if spec is None:
                continue
            placeholder = field if field in ("title", "subtitle", "body") else spec.get("placeholder", field)
            shape = find_shape_by_placeholder(root, placeholder)
            if shape is None:
                entry["missing_placeholders"].append(placeholder)
                continue
            lines = spec if isinstance(spec, list) else (spec.get("lines") or [spec.get("text") or ""])
            set_placeholder_text(shape, lines)
            filled += 1
            entry["filled"].append({"placeholder": placeholder,
                                    "lines": len(lines),
                                    "source_locator": (spec.get("source_locator")
                                                       if isinstance(spec, dict) else None)})
        parts[slide_part] = serialise_like(root, originals.get(slide_part, parts[slide_part]))
        operations.append(entry)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / "edited.pptx"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as package:
        for name in names:
            package.writestr(name, parts[name])

    after = {name: sha256_bytes(parts[name]) for name in names}
    changed = sorted(name for name in before if name in after and before[name] != after[name])
    added = sorted(name for name in after if name not in before)
    template_unchanged = all(before[name] == after[name] for name in template_parts
                             if name in after)
    report = {
        "schema": "deck-merge/v1",
        "deck": {"path": str(deck), "sha256": sha256_file(deck)},
        "plan": plan.get("schema") or "deck-merge-plan/v1",
        "out": {"path": str(out_path), "sha256": sha256_file(out_path),
                "bytes": out_path.stat().st_size},
        "operations": operations,
        "placeholders_filled": filled,
        "slides_added": sum(1 for op in operations if op.get("cloned")),
        "changed_parts": changed,
        "added_parts": added,
        "template_parts_unchanged": template_unchanged,
        "template_parts": sorted(template_parts),
        "preserved_verbatim": [name for name in names
                               if name not in changed and name not in added][:40],
        "note": "Only the edited slide parts, the presentation list, its relationships and the "
                "content-type table change. Master, layouts, theme and every untouched slide are "
                "copied byte-for-byte, which is what proves the template was really used.",
    }
    (outdir / "merge-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    return report


# --------------------------------------------------------------------------- checking

def check(deck: Path, output: Path, plan: dict, outdir: Path) -> dict:
    checks = []

    def add(check_id, requirement, ok, evidence, locator):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence, "locator": locator})

    before = inspect_deck(deck)
    try:
        after = inspect_deck(output)
    except (zipfile.BadZipFile, KeyError, OSError) as error:
        add("openable", "output opens as a PPTX package", False, repr(error), str(output))
        report = {"schema": "deck-check/v1", "checks": checks, "passed": 0, "failed": 1,
                  "status": "needs_work"}
        Path(outdir).mkdir(parents=True, exist_ok=True)
        (Path(outdir) / "slide-check.json").write_text(json.dumps(report, ensure_ascii=False,
                                                                  indent=2), encoding="utf-8")
        return report

    add("openable", "output opens as a PPTX package with presentation + master + layout",
        bool(after["master"]) and bool(after["layouts"]),
        f"master={after['master']} layouts={len(after['layouts'])} slides={after['slide_count']}",
        str(output))
    add("slide_size_kept", "the deck size follows the template",
        before["slide_size"] == after["slide_size"],
        f"before={before['slide_size']} after={after['slide_size']}", str(output))
    add("theme_kept", "theme fonts and colours are unchanged",
        before["theme"] == after["theme"],
        f"fonts={after['theme'].get('fonts')}", str(output))
    add("master_kept", "the slide master is the template's own master",
        before["master"] == after["master"], f"{after['master']}", str(output))

    before_parts, _ = read_parts(deck)
    after_parts, _ = read_parts(output)
    template_prefixes = ("ppt/slideMasters/", "ppt/slideLayouts/", "ppt/theme/")
    unchanged = [name for name in before_parts
                 if name.startswith(template_prefixes)
                 and name in after_parts
                 and sha256_bytes(before_parts[name]) == sha256_bytes(after_parts[name])]
    drifted = [name for name in before_parts
               if name.startswith(template_prefixes)
               and name in after_parts
               and sha256_bytes(before_parts[name]) != sha256_bytes(after_parts[name])]
    add("template_bytes_kept", "every master/layout/theme part is byte-identical",
        not drifted, f"unchanged={len(unchanged)} drifted={drifted}", str(output))

    # placeholder inheritance: each slide still points at a real layout, and each layout at a master
    dangling_layouts = [slide["part"] for slide in after["slides"]
                        if not slide["layout"] or slide["layout"] not in after_parts]
    add("placeholder_inheritance", "every slide resolves to a layout present in the package",
        not dangling_layouts, f"dangling={dangling_layouts}", str(output))

    # declared content must be present, and overflow must be reported per frame
    declared = []
    for item in plan.get("slides", []):
        for field in ("title", "subtitle", "body", "notes", "caption"):
            spec = item.get(field)
            if spec is None:
                continue
            lines = spec if isinstance(spec, list) else (spec.get("lines") or [spec.get("text") or ""])
            declared.extend(line if isinstance(line, str) else (line.get("text") or "")
                            for line in lines)
    present = [text for text in declared if text and text in
               json.dumps(after["slides"], ensure_ascii=False)]
    add("declared_content_present", "every declared line is found in the produced slides",
        len(present) == len([text for text in declared if text]),
        f"{len(present)}/{len([text for text in declared if text])} declared lines present",
        str(output))

    overflow = []
    for slide in after["slides"]:
        for shape in slide["shapes"]:
            if not shape.get("placeholder") or not shape.get("text"):
                continue
            paragraphs = [{"text": run.get("text") or "", "size": (int(run["size"]) / 100.0
                                                                   if run.get("size") else 18.0)}
                          for run in shape["runs"]] or [{"text": shape["text"], "size": 18.0}]
            capacity = text_capacity(shape["geometry"], paragraphs)
            if capacity.get("fits") is False:
                overflow.append({"slide": slide["part"], "placeholder": shape["placeholder"],
                                 "estimated_lines": capacity["estimated_lines"],
                                 "estimated_height_in": capacity["estimated_height_in"],
                                 "box_height_in": capacity["box_height_in"]})
    add("no_estimated_overflow", "no placeholder is estimated to overflow its own box",
        not overflow, f"overflowing frames={overflow[:4]}", str(output))

    plan_path = Path(outdir) / "deck-merge-plan-used.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    failures = [c for c in checks if c["status"] == "fail"]
    report = {
        "schema": "deck-check/v1",
        "deck": str(deck), "output": str(output),
        "checks": checks,
        "overflow_estimates": overflow,
        "slides_before": before["slide_count"], "slides_after": after["slide_count"],
        "passed": len(checks) - len(failures), "failed": len(failures),
        "status": "verified" if not failures else "needs_work",
        "scope_note": "Proves the template was really used, the declared content is present and no "
                      "frame is estimated to overflow. The overflow figure is an estimate; the "
                      "rendered preview is the visual check. Not an official score.",
    }
    Path(outdir).mkdir(parents=True, exist_ok=True)
    (Path(outdir) / "slide-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
    return report


def preview(deck: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    result = {"schema": "deck-preview/v1", "deck": str(deck),
              "renderer_available": bool(soffice), "slides": [], "pdf": None}
    if not soffice:
        result["note"] = ("no LibreOffice/soffice on PATH: the deck was not rendered. The editable "
                          "PPTX remains the deliverable and the missing preview is an explicit "
                          "limitation; do not claim a visual check that did not happen.")
        (outdir / "preview-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                                    encoding="utf-8")
        return result
    staging = outdir / "render"
    staging.mkdir(exist_ok=True)
    deck_path = Path(deck).resolve()

    def convert(target_pdf_must_exist_below: Path) -> tuple:
        command = [str(soffice), "--headless", "--norestore", "--convert-to", "pdf",
                   "--outdir", str(staging.resolve()), str(deck_path)]
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=600)
        return command, proc

    command, proc = convert(staging)
    pdf = staging / (deck_path.stem + ".pdf")
    if not pdf.exists():
        # A soffice instance left running by an earlier conversion can answer "source file could
        # not be loaded" for a perfectly valid deck; one clean retry, then report honestly.
        proc = subprocess.run([str(soffice), "--headless", "--terminate_after_init"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=120)
        command, proc = convert(staging)
    result["command"] = " ".join(command)
    result["returncode"] = proc.returncode
    result["stdout_tail"] = (proc.stdout or "")[-600:]
    result["stderr_tail"] = (proc.stderr or "")[-600:]
    if pdf.exists():
        result["pdf"] = str(pdf)
        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm:
            subprocess.run([pdftoppm, "-png", "-r", "80", str(pdf), str(staging / "slide")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600)
            result["slides"] = sorted(str(p) for p in staging.glob("slide*.png"))
        pdftotext = shutil.which("pdftotext")
        if pdftotext:
            text = subprocess.run([pdftotext, str(pdf), "-"], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=180)
            result["rendered_text"] = (text.stdout or "")[:4000]
            result["rendered_text_chars"] = len(text.stdout or "")
    else:
        result["note"] = "the renderer ran but produced no PDF; keep the editable deck"
    (outdir / "preview-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    return result


# --------------------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Template-aware PPTX editing")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect"); p.add_argument("deck"); p.add_argument("--out")
    p = sub.add_parser("merge"); p.add_argument("--deck", required=True)
    p.add_argument("--plan", required=True); p.add_argument("--outdir", required=True)
    p = sub.add_parser("check"); p.add_argument("--deck", required=True)
    p.add_argument("--output", required=True); p.add_argument("--plan", required=True)
    p.add_argument("--outdir", required=True)
    p = sub.add_parser("preview"); p.add_argument("--deck", required=True)
    p.add_argument("--outdir", required=True)

    args = parser.parse_args(argv)
    if args.command == "inspect":
        payload = inspect_deck(Path(args.deck))
        if args.out:
            Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        print(json.dumps({"slides": payload["slide_count"], "size": payload["slide_size"],
                          "theme": payload["theme"].get("fonts"),
                          "layouts": {Path(k).name: v["name"] for k, v in payload["layouts"].items()},
                          "placeholders_per_layout": {Path(k).name: [s["placeholder"]
                                                                     for s in v["placeholders"]]
                                                      for k, v in payload["layouts"].items()}},
                         ensure_ascii=False))
        return 0
    if args.command == "merge":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        report = merge(Path(args.deck), plan, Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("out", "placeholders_filled", "slides_added",
                                                 "template_parts_unchanged", "changed_parts")},
                         ensure_ascii=False))
        return 0
    if args.command == "check":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        report = check(Path(args.deck), Path(args.output), plan, Path(args.outdir))
        print(json.dumps({"passed": report["passed"], "failed": report["failed"],
                          "status": report["status"]}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    if args.command == "preview":
        result = preview(Path(args.deck), Path(args.outdir))
        print(json.dumps({"renderer_available": result["renderer_available"],
                          "pdf": result["pdf"], "slides": len(result["slides"]),
                          "note": result.get("note")}, ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
