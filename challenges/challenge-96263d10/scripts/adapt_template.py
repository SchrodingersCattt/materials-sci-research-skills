"""Dependency-free academic template adaptation for DOCX manuscripts.

This module is the whole runtime of the Skill: it inspects a supplied template
and manuscript, extracts an explicit format checklist, applies the template's
style definitions to the manuscript without rewriting its text, and verifies
the result item by item. It uses only the Python standard library (zipfile +
xml.etree), so it runs in a container that has no network, no doc-forge
installation and no Office suite. Rendering a PDF preview is optional and is
reported honestly as unavailable when no renderer exists.

Commands
--------
inspect  PATH                      report a DOCX/template's structure and hashes
specify --template T --source S    extract the format checklist + style mapping
apply   --source S --template T    produce the adapted DOCX (text preserved)
verify  --source S --output O      per-item compliance and content-coverage checks
preview --docx D                   optional real PDF/PNG render, or an honest note

Every command writes machine-readable JSON next to its human summary.
"""

from __future__ import annotations

import argparse
import copy as _copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
V = "urn:schemas-microsoft-com:vml"
O = "urn:schemas-microsoft-com:office:office"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

NS_PREFIXES = {
    "w": W, "r": R, "w14": W14, "wp": WP, "a": A, "pic": PIC, "mc": MC,
    "v": V, "o": O, "m": M, "pr": PKG_REL, "ct": CT,
}
for _prefix, _uri in NS_PREFIXES.items():
    ET.register_namespace(_prefix, _uri)

DOCX_PARTS = ("[Content_Types].xml", "word/document.xml", "word/styles.xml")

HEADING_WORD = r"(?:heading|head|h|ha|标题|章节|section|chapter|chapitre|titre|rubrik|überschrift|заголовок)"
HEADING_RE = re.compile(rf"^(?:{HEADING_WORD})[\s_.-]*([1-9])$", re.I)
HEADING_LOOSE_RE = re.compile(rf"(?:^|[\s_.-])(?:{HEADING_WORD})[\s_.-]*([1-9])(?:$|[\s_.-])", re.I)
HEADING_SHORT_RE = re.compile(r"^h([1-9])$", re.I)
CN_NUMERALS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
HEADING_CN_RE = re.compile(r"([一二三四五六七八九])\s*级?\s*标题")
CAPTION_RE = re.compile(r"(caption|题注|图注|表注|figure\s*\d|table\s*\d|图\s*\d|表\s*\d)", re.I)
REFERENCE_RE = re.compile(r"(reference|bibliograph|参考文献|文献|引文|works cited)", re.I)
ABSTRACT_RE = re.compile(r"(abstract|摘要)", re.I)
KEYWORD_RE = re.compile(r"(keyword|关键词)", re.I)
TITLE_RE = re.compile(r"(^|[\s_.-])(title|标题|篇名|题目)([\s_.-]|$)", re.I)
BODY_RE = re.compile(r"(normal|body|正文|text|paragraph|默认|默认段落)", re.I)

TEXT_LIKE = {".md", ".markdown", ".txt", ".rst", ".tex"}


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def register_declared_namespaces(raw: bytes) -> dict:
    """Register every xmlns prefix the raw document declared.

    ElementTree drops unused declarations when serialising, which can turn a
    valid Word part (mc:Ignorable="w14 wp14") into an invalid one. Reading the
    original declarations first keeps the output namespace-complete.
    """
    head = raw[:8192].decode("utf-8", "replace")
    found = {}
    for prefix, uri in re.findall(r'xmlns:([A-Za-z0-9_.-]+)="([^"]+)"', head):
        found[prefix] = uri
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass
    return found


def read_zip_parts(path: Path) -> tuple[dict, list]:
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        parts = {name: package.read(name) for name in names}
    return parts, names


def xml_root(parts: dict, name: str):
    raw = parts.get(name)
    if raw is None:
        return None
    register_declared_namespaces(raw)
    return ET.fromstring(raw)


def paragraph_text(paragraph) -> str:
    chunks = [node.text or "" for node in paragraph.iter(q("t"))]
    for _ in paragraph.iter(q("tab")):
        chunks.append("\t")
    return "".join(chunks)


def paragraph_style_id(paragraph) -> str:
    style = paragraph.find(f"{q('pPr')}/{q('pStyle')}")
    return (style.get(q("val")) or "") if style is not None else ""


def style_outline_level(style):
    level = style.find(f"{q('pPr')}/{q('outlineLvl')}")
    if level is None:
        return None
    try:
        return int(level.get(q("val")))
    except (TypeError, ValueError):
        return None


def style_name(style) -> str:
    name = style.find(q("name"))
    return (name.get(q("val")) or "") if name is not None else ""


def rpr_summary(rpr) -> dict:
    if rpr is None:
        return {}
    out = {}
    fonts = rpr.find(q("rFonts"))
    if fonts is not None:
        per_script = {key: fonts.get(q(key)) for key in ("ascii", "hAnsi", "eastAsia", "cs")
                      if fonts.get(q(key))}
        if per_script:
            out["fonts"] = per_script
    size = rpr.find(q("sz"))
    if size is not None:
        out["size_half_points"] = size.get(q("val"))
    for tag, key in (("b", "bold"), ("i", "italic"), ("u", "underline")):
        node = rpr.find(q(tag))
        if node is not None:
            value = node.get(q("val"))
            out[key] = value not in ("0", "false", "off")
    return out


def ppr_summary(ppr) -> dict:
    if ppr is None:
        return {}
    out = {}
    spacing = ppr.find(q("spacing"))
    if spacing is not None:
        for key in ("before", "after", "line", "lineRule"):
            value = spacing.get(q(key))
            if value is not None:
                out.setdefault("spacing", {})[key] = value
    ind = ppr.find(q("ind"))
    if ind is not None:
        for key in ("left", "right", "firstLine", "hanging"):
            value = ind.get(q(key))
            if value is not None:
                out.setdefault("indent", {})[key] = value
    align = ppr.find(q("jc"))
    if align is not None:
        out["align"] = align.get(q("val"))
    level = ppr.find(q("outlineLvl"))
    if level is not None:
        out["outline_level"] = level.get(q("val"))
    num = ppr.find(q("numPr"))
    if num is not None:
        num_id = num.find(q("numId"))
        ilvl = num.find(q("ilvl"))
        out["numbering"] = {
            "numId": num_id.get(q("val")) if num_id is not None else None,
            "ilvl": ilvl.get(q("val")) if ilvl is not None else None,
        }
    return out


def describe_styles(root) -> dict:
    styles = {}
    if root is None:
        return styles
    for style in root.findall(q("style")):
        style_id = style.get(q("styleId")) or ""
        entry = {
            "style_id": style_id,
            "type": style.get(q("type")) or "paragraph",
            "name": style_name(style),
            "based_on": (style.find(q("basedOn")).get(q("val"))
                         if style.find(q("basedOn")) is not None else None),
            "link": (style.find(q("link")).get(q("val"))
                     if style.find(q("link")) is not None else None),
            "outline_level": style_outline_level(style),
        }
        entry.update(rpr_summary(style.find(q("rPr"))))
        entry.update(ppr_summary(style.find(q("pPr"))))
        entry["default"] = style.get(q("default")) in ("1", "true")
        styles[style_id] = entry
    return styles


def describe_section(root) -> dict:
    if root is None:
        return {}
    body = root.find(q("body"))
    if body is None:
        return {}
    section = body.find(q("sectPr"))
    if section is None:
        return {}
    out = {"source": "sectPr"}
    size = section.find(q("pgSz"))
    if size is not None:
        out["page_size"] = {k: size.get(q(k)) for k in ("w", "h", "orient") if size.get(q(k))}
    margins = section.find(q("pgMar"))
    if margins is not None:
        out["margins"] = {k: margins.get(q(k)) for k in
                          ("top", "right", "bottom", "left", "header", "footer", "gutter")
                          if margins.get(q(k)) is not None}
    cols = section.find(q("cols"))
    if cols is not None:
        out["columns"] = {k: cols.get(q(k)) for k in ("num", "space", "sep") if cols.get(q(k)) is not None}
    grid = section.find(q("docGrid"))
    if grid is not None:
        out["doc_grid"] = {k: grid.get(q(k)) for k in ("type", "linePitch") if grid.get(q(k))}
    return out


def describe_doc_defaults(root) -> dict:
    if root is None:
        return {}
    defaults = root.find(q("docDefaults"))
    if defaults is None:
        return {}
    return {
        "run": rpr_summary(defaults.find(f"{q('rPrDefault')}/{q('rPr')}")),
        "paragraph": ppr_summary(defaults.find(f"{q('pPrDefault')}/{q('pPr')}")),
    }


def inventory_docx(path: Path) -> dict:
    parts, names = read_zip_parts(path)
    document_raw = parts.get("word/document.xml")
    styles_root = xml_root(parts, "word/styles.xml")
    document_root = xml_root(parts, "word/document.xml")
    info: dict = {
        "path": str(path),
        "kind": "docx",
        "bytes": path.stat().st_size,
        "package_sha256": sha256_file(path),
        "document_xml_sha256": sha256_bytes(document_raw or b""),
        "parts": sorted(names),
        "part_count": len(names),
        "missing_required_parts": [p for p in DOCX_PARTS if p not in parts],
        "has_macros": "word/vbaProject.bin" in parts,
    }
    if document_root is None:
        info["error"] = "word/document.xml missing or unparsable"
        return info
    body = document_root.find(q("body"))
    paragraphs = list(document_root.iter(q("p")))
    tables = list(document_root.iter(q("tbl")))
    info.update({
        "styles": describe_styles(styles_root),
        "doc_defaults": describe_doc_defaults(styles_root),
        "section": describe_section(document_root),
        "paragraph_count": len(paragraphs),
        "table_count": len(tables),
        "image_relationships": len([n for n in names if n.startswith("word/media/")]),
        "has_footnotes": "word/footnotes.xml" in parts,
        "has_endnotes": "word/endnotes.xml" in parts,
        "has_comments": "word/comments.xml" in parts,
        "has_tracked_changes": bool(list(document_root.iter(q("ins"))) or
                                    list(document_root.iter(q("del")))),
        "has_equations": bool(list(document_root.iter(f"{{{M}}}oMath"))),
        "has_fields": bool(list(document_root.iter(q("fldChar")))),
        "has_toc_field": "TOC" in (document_raw or b"").decode("utf-8", "replace"),
        "headers": sorted(n for n in names if re.match(r"word/header\d*\.xml", n)),
        "footers": sorted(n for n in names if re.match(r"word/footer\d*\.xml", n)),
        "text_chars": sum(len(paragraph_text(p)) for p in paragraphs),
        "first_paragraph_texts": [paragraph_text(p)[:80] for p in paragraphs[:8]],
        "body_present": body is not None,
    })
    used: dict = {}
    for paragraph in paragraphs:
        style_id = paragraph_style_id(paragraph)
        used[style_id] = used.get(style_id, 0) + 1
    info["paragraph_style_usage"] = used
    return info


def inventory_text(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return {
        "path": str(path),
        "kind": path.suffix.lower().lstrip(".") or "text",
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "line_count": len(lines),
        "heading_lines": [ln.strip()[:100] for ln in lines if ln.lstrip().startswith("#")][:40],
        "preview": lines[:10],
    }


def inventory(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return inventory_docx(path)
    if suffix in TEXT_LIKE:
        return inventory_text(path)
    return {
        "path": str(path),
        "kind": suffix.lstrip(".") or "unknown",
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "note": "Binary or unsupported container; extract text with the case's own supplied "
                "tool before claiming adaptation.",
    }


# --------------------------------------------------------------------------- spec

def heading_level(entry: dict):
    """Level of a heading-ish style, from its name first and its outline level second."""
    for candidate in (entry.get("name") or "", entry.get("style_id") or ""):
        text = candidate.strip()
        match = (HEADING_RE.match(text) or HEADING_SHORT_RE.match(text)
                 or HEADING_LOOSE_RE.search(text))
        if match:
            return int(match.group(1))
        cn = HEADING_CN_RE.search(text)
        if cn:
            return CN_NUMERALS[cn.group(1)]
        if re.fullmatch(r"标题|heading|titre", text, re.I):
            return 1
    level = entry.get("outline_level")
    if level is not None:
        try:
            return int(level) + 1
        except (TypeError, ValueError):
            return None
    return None


def classify_style(entry: dict) -> str:
    name = entry.get("name") or ""
    style_id = entry.get("style_id") or ""
    haystack = f"{name} {style_id}"
    if heading_level(entry) is not None:
        return "heading"
    if TITLE_RE.search(name.strip()) or TITLE_RE.search(style_id.strip()):
        return "title"
    if CAPTION_RE.search(haystack):
        return "caption"
    if REFERENCE_RE.search(haystack):
        return "reference"
    if ABSTRACT_RE.search(haystack):
        return "abstract"
    if KEYWORD_RE.search(haystack):
        return "keyword"
    if entry.get("default") or BODY_RE.search(name):
        return "body"
    return "other"


def target_style_for(source_entry: dict, template_styles: dict):
    """Pick the template style a source paragraph style should map onto."""
    role = classify_style(source_entry)
    level = heading_level(source_entry)
    by_role = {sid: e for sid, e in template_styles.items() if classify_style(e) == role}
    if role == "heading" and level is not None:
        for style_id, entry in by_role.items():
            if heading_level(entry) == level:
                return style_id, f"template heading style for level {level}"
        levels = {heading_level(e): sid for sid, e in by_role.items() if heading_level(e)}
        if levels:
            nearest = min(levels, key=lambda candidate: (abs(candidate - level), candidate))
            return (levels[nearest],
                    f"template has no heading level {level}; nearest available level {nearest} "
                    f"is used and recorded as an approximation")
        return None, f"template has no heading style for level {level}"
    if role == "body" and by_role:
        explicit = [sid for sid, e in by_role.items()
                    if not e.get("default") and BODY_RE.search(e.get("name") or "")]
        default = [sid for sid, e in by_role.items() if e.get("default")]
        chosen = (sorted(explicit) + sorted(default) + sorted(by_role))[0]
        return chosen, f"template body style name '{template_styles[chosen].get('name')}'"
    if role in ("title", "caption", "reference", "abstract", "keyword") and by_role:
        style_id = sorted(by_role)[0]
        return style_id, f"template {role} style name '{template_styles[style_id].get('name')}'"
    same_name = [sid for sid, entry in template_styles.items()
                 if entry.get("name") and (entry.get("name") or "").lower() == (source_entry.get("name") or "").lower()]
    if same_name:
        return same_name[0], "identical style name in template"
    return None, f"no template counterpart for role '{role}'"


def build_spec(template_info: dict, source_info: dict) -> dict:
    template_styles = template_info.get("styles", {})
    source_styles = source_info.get("styles", {})
    template_roles: dict = {}
    for style_id, entry in template_styles.items():
        template_roles.setdefault(classify_style(entry), []).append({
            "style_id": style_id, "name": entry.get("name"),
            "outline_level": entry.get("outline_level"),
            "size_half_points": entry.get("size_half_points"),
            "fonts": entry.get("fonts"),
            "spacing": entry.get("spacing"),
            "align": entry.get("align"),
        })
    items: list = []

    def add(item_id, category, requirement, value, locator, status="extracted"):
        items.append({
            "id": item_id, "category": category, "requirement": requirement,
            "value": value, "evidence_locator": locator, "status": status,
        })

    section = template_info.get("section") or {}
    add("page_size", "geometry", "page width/height/orientation follow the template",
        section.get("page_size"), "template word/document.xml body/sectPr/pgSz",
        "extracted" if section.get("page_size") else "not_found")
    add("margins", "geometry", "page margins follow the template",
        section.get("margins"), "template word/document.xml body/sectPr/pgMar",
        "extracted" if section.get("margins") else "not_found")
    add("columns", "geometry", "column count and spacing follow the template",
        section.get("columns"), "template word/document.xml body/sectPr/cols",
        "extracted" if section.get("columns") else "not_found")
    defaults = template_info.get("doc_defaults") or {}
    add("default_font", "fonts", "default document font family follows the template",
        (defaults.get("run") or {}).get("fonts"), "template word/styles.xml docDefaults/rPrDefault",
        "extracted" if (defaults.get("run") or {}).get("fonts") else "not_found")
    add("default_size", "fonts", "default document font size follows the template",
        (defaults.get("run") or {}).get("size_half_points"),
        "template word/styles.xml docDefaults/rPrDefault",
        "extracted" if (defaults.get("run") or {}).get("size_half_points") else "not_found")
    for role in ("title", "heading", "body", "caption", "reference", "abstract", "keyword"):
        entries = template_roles.get(role, [])
        add(f"styles_{role}", "styles", f"template defines the {role} style family",
            entries, f"template word/styles.xml styles classified as {role}",
            "extracted" if entries else "not_found")

    mapping, unmapped = {}, []
    for style_id, entry in source_styles.items():
        target, evidence = target_style_for(entry, template_styles)
        record = {
            "source_style_id": style_id, "source_style_name": entry.get("name"),
            "role": classify_style(entry), "source_outline_level": entry.get("outline_level"),
            "target_style_id": target, "evidence": evidence,
        }
        if target:
            mapping[style_id] = record
        else:
            unmapped.append(record)
    add("style_mapping", "styles", "every source paragraph style maps to a template style",
        {"mapped": len(mapping), "unmapped": len(unmapped)},
        "source styles.xml x template styles.xml",
        "extracted" if mapping else "not_found")

    usage = source_info.get("paragraph_style_usage") or {}
    add("source_styles_in_use", "content", "paragraph styles actually used by the manuscript",
        {sid: usage.get(sid, 0) for sid in source_styles}, "source word/document.xml pStyle usage")
    add("content_units", "content", "manuscript text, tables, figures and notes stay unchanged",
        {
            "paragraph_count": source_info.get("paragraph_count"),
            "table_count": source_info.get("table_count"),
            "image_relationships": source_info.get("image_relationships"),
            "text_chars": source_info.get("text_chars"),
            "has_footnotes": source_info.get("has_footnotes"),
            "has_endnotes": source_info.get("has_endnotes"),
            "has_comments": source_info.get("has_comments"),
            "has_tracked_changes": source_info.get("has_tracked_changes"),
            "has_equations": source_info.get("has_equations"),
            "has_fields": source_info.get("has_fields"),
        }, "source word/document.xml structure + package part inventory")
    return {
        "schema": "template-adaptation-spec/v1",
        "template": {"path": template_info.get("path"), "sha256": template_info.get("package_sha256")},
        "source": {"path": source_info.get("path"), "sha256": source_info.get("package_sha256")},
        "items": items,
        "style_mapping": mapping,
        "unmapped_source_styles": unmapped,
        "limits": [
            "Style roles are inferred from style names, outline levels and template structure; an "
            "unusual template may need an explicit mapping override that is recorded as such.",
            "Numbering, cross-reference fields and TOC content are preserved from the source and are "
            "not renumbered; a template that requires its own numbering scheme is reported as a "
            "limitation instead of being rebuilt silently.",
            "A PDF or prose template has to be expressed as a style profile by reading the stated "
            "requirements; this helper does not guess styles from raster layout.",
        ],
    }


def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- apply

def import_template_styles(template_styles_root, source_styles_root) -> list:
    """Copy template style definitions the manuscript lacks. Returns the actions taken."""
    existing = {s.get(q("styleId")) for s in source_styles_root.findall(q("style"))}
    names = {style_name(s) for s in source_styles_root.findall(q("style"))}
    actions = []
    for style in template_styles_root.findall(q("style")):
        style_id = style.get(q("styleId"))
        style_type = style.get(q("type")) or "paragraph"
        if style_id in existing or (style_name(style) and style_name(style) in names):
            continue
        clone = _copy.deepcopy(style)
        source_styles_root.append(clone)
        existing.add(style_id)
        names.add(style_name(style))
        actions.append({"imported_style_id": style_id, "name": style_name(style),
                        "type": style_type, "reason": "template style missing in manuscript"})
    return actions


def import_doc_defaults(template_styles_root, source_styles_root) -> dict:
    """Adopt the template's document-wide default run/paragraph properties."""
    template_defaults = template_styles_root.find(q("docDefaults"))
    if template_defaults is None:
        return {"applied": False, "reason": "template styles.xml has no docDefaults"}
    source_defaults_existing = source_styles_root.find(q("docDefaults"))
    before_run = rpr_summary(
        source_defaults_existing.find(f"{q('rPrDefault')}/{q('rPr')}")
        if source_defaults_existing is not None else None)
    source_defaults = source_defaults_existing
    if source_defaults is None:
        source_defaults = ET.Element(q("docDefaults"))
        source_styles_root.insert(0, source_defaults)
    for tag in ("rPrDefault", "pPrDefault"):
        template_node = template_defaults.find(q(tag))
        if template_node is None:
            continue
        existing = source_defaults.find(q(tag))
        if existing is not None:
            source_defaults.remove(existing)
        source_defaults.insert(0, _copy.deepcopy(template_node))
    after_run = rpr_summary(source_styles_root.find(f"{q('docDefaults')}/{q('rPrDefault')}/{q('rPr')}"))
    return {"applied": True, "run_defaults_before": before_run, "run_defaults_after": after_run}


def table_formatting(template_root) -> dict:
    """Formatting-only properties of the template's first table (never its widths)."""
    if template_root is None:
        return {}
    table = template_root.find(f"{q('body')}/{q('tbl')}")
    if table is None:
        table = next(iter(template_root.iter(q("tbl"))), None)
    if table is None:
        return {}
    props = table.find(q("tblPr"))
    if props is None:
        return {}
    keep = ("tblStyle", "tblBorders", "tblLayout", "jc", "tblCellMar", "tblInd", "shd")
    return {tag: _copy.deepcopy(props.find(q(tag))) for tag in keep if props.find(q(tag)) is not None}


def apply_table_formatting(document_root, template_root) -> list:
    """Give source tables the template's table style/borders without touching widths."""
    formatting = table_formatting(template_root)
    if not formatting:
        return []
    actions = []
    for index, table in enumerate(document_root.iter(q("tbl"))):
        props = table.find(q("tblPr"))
        if props is None:
            props = ET.Element(q("tblPr"))
            table.insert(0, props)
        applied = []
        for tag, node in formatting.items():
            existing = props.find(q(tag))
            if existing is not None:
                props.remove(existing)
            position = 0 if tag == "tblStyle" else len(list(props))
            props.insert(position, _copy.deepcopy(node))
            applied.append(tag)
        actions.append({"table_index": index, "applied": applied})
    return actions


def set_paragraph_style(paragraph, style_id: str) -> None:
    ppr = paragraph.find(q("pPr"))
    if ppr is None:
        ppr = ET.Element(q("pPr"))
        paragraph.insert(0, ppr)
    pstyle = ppr.find(q("pStyle"))
    if pstyle is None:
        pstyle = ET.SubElement(ppr, q("pStyle"))
    pstyle.set(q("val"), style_id)


def replace_section_geometry(document_root, template_root) -> dict:
    """Copy page size, margins, columns and grid from the template's sectPr."""
    source_body = document_root.find(q("body"))
    template_body = template_root.find(q("body")) if template_root is not None else None
    if source_body is None or template_body is None:
        return {"applied": False, "reason": "missing body"}
    source_sect = source_body.find(q("sectPr"))
    template_sect = template_body.find(q("sectPr"))
    if template_sect is None:
        return {"applied": False, "reason": "template has no sectPr"}
    if source_sect is None:
        source_sect = ET.SubElement(source_body, q("sectPr"))
    changed = []
    for tag in ("pgSz", "pgMar", "cols", "docGrid"):
        template_node = template_sect.find(q(tag))
        if template_node is None:
            continue
        source_node = source_sect.find(q(tag))
        if source_node is None:
            source_sect.append(_copy.deepcopy(template_node))
            changed.append(f"{tag}: added from template")
            continue
        before = dict(source_node.attrib)
        for key, value in template_node.attrib.items():
            source_node.set(key, value)
        after = dict(source_node.attrib)
        if before != after:
            changed.append(f"{tag}: {before} -> {after}")
    return {"applied": True, "changes": changed}


def content_stream(document_root) -> list:
    return [paragraph_text(p) for p in document_root.iter(q("p"))]


def refuse(outdir: Path, reason: str, **extra) -> dict:
    """Record a refusal with its reason instead of returning silently."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "template-adaptation-apply/v1", "applied": False, "reason": reason, **extra}
    write_json(outdir / "apply-report.json", report)
    return report


def apply_adaptation(source: Path, template: Path, outdir: Path, spec) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() != ".docx":
        return refuse(outdir, f"unsupported source container {source.suffix}; convert the supplied "
                              "manuscript to DOCX with the case's own tool first")
    if template.suffix.lower() != ".docx":
        return refuse(outdir, f"template container {template.suffix} is not DOCX; a style profile "
                              "has to be authored from the stated requirements instead of being "
                              "guessed")
    parts, names = read_zip_parts(source)
    template_parts, _ = read_zip_parts(template)
    styles_root = xml_root(parts, "word/styles.xml")
    document_root = xml_root(parts, "word/document.xml")
    template_styles_root = xml_root(template_parts, "word/styles.xml")
    template_document_root = xml_root(template_parts, "word/document.xml")
    if styles_root is None or document_root is None or template_styles_root is None:
        return refuse(outdir, "source or template lacks styles/document parts")

    import_actions = import_template_styles(template_styles_root, styles_root)
    defaults_action = import_doc_defaults(template_styles_root, styles_root)
    before = content_stream(document_root)
    mapping = (spec or {}).get("style_mapping") or {}
    restyled, unmapped, unstyled = [], [], 0
    for paragraph in document_root.iter(q("p")):
        current = paragraph_style_id(paragraph)
        target = (mapping.get(current) or {}).get("target_style_id") if mapping else None
        if target:
            set_paragraph_style(paragraph, target)
            restyled.append({"source_style": current, "target_style": target})
        elif current:
            unmapped.append(current)
        elif paragraph_text(paragraph).strip():
            # No pStyle: the imported template docDefaults now govern this paragraph.
            unstyled += 1
    table_actions = apply_table_formatting(document_root, template_document_root)
    section_result = replace_section_geometry(document_root, template_document_root)
    after = content_stream(document_root)

    parts["word/styles.xml"] = ET.tostring(styles_root, encoding="UTF-8", xml_declaration=True)
    parts["word/document.xml"] = ET.tostring(document_root, encoding="UTF-8", xml_declaration=True)
    adapted = outdir / "adapted.docx"
    with zipfile.ZipFile(adapted, "w", zipfile.ZIP_DEFLATED) as package:
        for name in names:
            package.writestr(name, parts[name])
    report = {
        "schema": "template-adaptation-apply/v1",
        "applied": True,
        "source": {"path": str(source), "sha256": sha256_file(source)},
        "template": {"path": str(template), "sha256": sha256_file(template)},
        "adapted": {"path": str(adapted), "sha256": sha256_file(adapted)},
        "imported_styles": import_actions,
        "document_defaults": defaults_action,
        "table_formatting": table_actions,
        "restyled_paragraphs": len(restyled),
        "restyled_style_pairs": sorted({(r["source_style"], r["target_style"]) for r in restyled}),
        "unmapped_styles": sorted(set(unmapped)),
        "directly_formatted_paragraphs": unstyled,
        "section_geometry": section_result,
        "content_units_before": len(before),
        "content_units_after": len(after),
        "content_stream_preserved": before == after,
        "not_rebuilt": [
            "document text", "tables", "figures", "footnotes/endnotes", "comments",
            "tracked changes", "fields", "numbering definitions", "headers/footers",
        ],
    }
    write_json(outdir / "apply-report.json", report)
    return report


# --------------------------------------------------------------------------- verify

def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def docx_text_units(path: Path) -> list:
    parts, _ = read_zip_parts(path)
    root = xml_root(parts, "word/document.xml")
    if root is None:
        return []
    return [normalise(paragraph_text(p)) for p in root.iter(q("p"))]


def check(checks: list, check_id: str, requirement: str, ok, evidence: str, locator: str) -> None:
    checks.append({
        "id": check_id,
        "requirement": requirement,
        "status": "pass" if ok else "fail",
        "evidence": evidence,
        "locator": locator,
    })


def verify(source: Path, output: Path, spec, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    checks: list = []
    try:
        out_info = inventory_docx(output)
        well_formed = not out_info.get("missing_required_parts") and not out_info.get("error")
    except (zipfile.BadZipFile, OSError) as error:
        out_info = {"error": repr(error)}
        well_formed = False
    check(checks, "openable_package", "output opens as a DOCX package with the required parts",
          well_formed,
          f"parts={out_info.get('part_count')} missing={out_info.get('missing_required_parts')}",
          str(output))

    source_units = [normalise(u) for u in docx_text_units(source)]
    output_units = [normalise(u) for u in docx_text_units(output)] if well_formed else []
    missing = [u for u in source_units if u and u not in output_units]
    check(checks, "content_coverage", "every manuscript text unit is present in the output",
          not missing,
          f"{len(source_units) - len(missing)}/{len(source_units)} units present; missing={missing[:5]}",
          str(output))
    check(checks, "content_order", "manuscript text units keep their original order",
          [u for u in output_units if u] == [u for u in source_units if u],
          "ordered sequence comparison", str(output))

    try:
        src_info = inventory_docx(source)
    except (zipfile.BadZipFile, OSError) as error:
        src_info = {"error": repr(error)}
    for key, label in (("table_count", "tables"), ("image_relationships", "image parts"),
                       ("has_footnotes", "footnotes"), ("has_endnotes", "endnotes"),
                       ("has_comments", "comments"), ("has_equations", "equations"),
                       ("has_tracked_changes", "tracked changes"), ("has_fields", "fields")):
        check(checks, f"preserved_{key}", f"{label} are preserved from the manuscript",
              src_info.get(key) == out_info.get(key),
              f"source={src_info.get(key)} output={out_info.get(key)}", str(output))

    if spec:
        template_path = (spec.get("template") or {}).get("path")
        template_section = None
        template_defaults = None
        if template_path and Path(template_path).exists():
            template_info = inventory_docx(Path(template_path))
            template_section = template_info.get("section")
            template_defaults = template_info.get("doc_defaults")
        if template_section:
            for key in ("page_size", "margins", "columns"):
                expected = template_section.get(key)
                actual = (out_info.get("section") or {}).get(key) or {}
                if not expected:
                    continue
                check(checks, f"template_{key}", f"{key} follow the template",
                      all(actual.get(k) == v for k, v in expected.items()),
                      f"template={expected} output={actual}",
                      "output word/document.xml body/sectPr")
        if template_defaults:
            for key, label in (("fonts", "default font family"), ("size_half_points", "default font size")):
                expected = (template_defaults.get("run") or {}).get(key)
                actual = ((out_info.get("doc_defaults") or {}).get("run") or {}).get(key)
                if not expected:
                    continue
                check(checks, f"template_default_{key}", f"{label} follows the template",
                      actual == expected, f"template={expected} output={actual}",
                      "output word/styles.xml docDefaults/rPrDefault")
        used = out_info.get("paragraph_style_usage") or {}
        output_styles = out_info.get("styles") or {}
        dangling = sorted({sid for sid in used if sid and sid not in output_styles})
        check(checks, "style_definitions_present",
              "every style used by the output is defined in the output package",
              not dangling, f"undefined style ids in use: {dangling}",
              "output word/styles.xml style ids")
        in_use = {}
        for item in spec.get("items") or []:
            if item.get("id") == "source_styles_in_use" and isinstance(item.get("value"), dict):
                in_use = item["value"]
        for source_style, record in (spec.get("style_mapping") or {}).items():
            target = record.get("target_style_id")
            if not target:
                continue
            expected_count = in_use.get(source_style, 0)
            if not expected_count:
                continue
            actual = used.get(target, 0)
            check(checks, f"style_applied_{source_style}",
                  f"'{source_style}' paragraphs use template style '{target}'",
                  actual >= expected_count,
                  f"target style used by {actual} paragraphs (source had {expected_count})",
                  "output word/document.xml pStyle usage")

    if template_path and Path(template_path).exists():
        template_table = table_formatting(xml_root(read_zip_parts(Path(template_path))[0],
                                                   "word/document.xml"))
        output_styles = out_info.get("styles") or {}
        for tag, node in (template_table or {}).items():
            if tag != "tblStyle":
                continue
            style_id = node.get(q("val")) if node is not None else None
            if not style_id:
                continue
            props = xml_root(read_zip_parts(output)[0], "word/document.xml")
            applied = [t.find(q("tblPr")) is not None and
                       (t.find(f"{q('tblPr')}/{q('tblStyle')}") is not None) and
                       t.find(f"{q('tblPr')}/{q('tblStyle')}").get(q("val")) == style_id
                       for t in props.iter(q("tbl"))] if props is not None else []
            check(checks, "template_table_style",
                  f"manuscript tables inherit the template table style '{style_id}'",
                  bool(applied) and all(applied),
                  f"tables using '{style_id}': {sum(1 for a in applied if a)}/{len(applied)}; "
                  f"style defined={style_id in output_styles}",
                  "output word/document.xml tblPr/tblStyle")

    failures = [c for c in checks if c["status"] == "fail"]
    report = {
        "schema": "template-adaptation-verify/v1",
        "source": str(source),
        "output": str(output),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "failed": len(failures),
        "status": "verified" if not failures else "needs_work",
        "scope_note": "These checks compare the produced package with the supplied manuscript and the "
                      "extracted template specification. They do not certify scientific meaning, "
                      "typesetting aesthetics or an official score.",
    }
    write_json(outdir / "verification.json", report)
    return report


# -------------------------------------------------------------------------- preview

def find_executable(*candidates: str):
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def preview(docx: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    soffice = find_executable("soffice", "libreoffice")
    pdftoppm = find_executable("pdftoppm")
    pdffonts = find_executable("pdffonts")
    pdftotext = find_executable("pdftotext")
    result = {
        "schema": "template-adaptation-preview/v1",
        "docx": str(docx),
        "renderer_available": bool(soffice),
        "pdf": None, "pngs": [], "pdf_font_report": None, "pdf_text_chars": None,
    }
    if not soffice:
        result["note"] = ("no LibreOffice/soffice on PATH: no PDF preview was rendered. The editable "
                          "DOCX remains the deliverable; do not claim a rendered preview or font "
                          "embedding that was not produced.")
        write_json(outdir / "preview-report.json", result)
        return result
    proc = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(docx)],
                          capture_output=True, text=True, timeout=420)
    pdf = outdir / (docx.stem + ".pdf")
    result["command"] = f"{soffice} --headless --convert-to pdf --outdir {outdir} {docx}"
    result["returncode"] = proc.returncode
    result["stdout_tail"] = (proc.stdout or "")[-800:]
    result["stderr_tail"] = (proc.stderr or "")[-800:]
    if pdf.exists():
        result["pdf"] = str(pdf)
        if pdftotext:
            text = subprocess.run([pdftotext, str(pdf), "-"], capture_output=True, text=True, timeout=180)
            result["pdf_text_chars"] = len(text.stdout or "")
        if pdffonts:
            fonts = subprocess.run([pdffonts, str(pdf)], capture_output=True, text=True, timeout=180)
            result["pdf_font_report"] = (fonts.stdout or "").strip().splitlines()[:40]
        if pdftoppm:
            subprocess.run([pdftoppm, "-png", "-r", "110", "-f", "1", "-l", "3", str(pdf),
                            str(outdir / "page")], capture_output=True, text=True, timeout=300)
            result["pngs"] = sorted(str(p) for p in outdir.glob("page*.png"))
    else:
        result["note"] = "renderer ran but produced no PDF; keep the DOCX and report the limitation"
    write_json(outdir / "preview-report.json", result)
    return result


# ----------------------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Dependency-free academic template adaptation")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("path")
    p_inspect.add_argument("--out")

    p_spec = sub.add_parser("specify")
    p_spec.add_argument("--template", required=True)
    p_spec.add_argument("--source", required=True)
    p_spec.add_argument("--out", required=True)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--source", required=True)
    p_apply.add_argument("--template", required=True)
    p_apply.add_argument("--spec")
    p_apply.add_argument("--outdir", required=True)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--source", required=True)
    p_verify.add_argument("--output", required=True)
    p_verify.add_argument("--spec")
    p_verify.add_argument("--outdir", required=True)

    p_preview = sub.add_parser("preview")
    p_preview.add_argument("--docx", required=True)
    p_preview.add_argument("--outdir", required=True)

    args = parser.parse_args(argv)
    if args.command == "inspect":
        payload = inventory(Path(args.path))
        if args.out:
            write_json(Path(args.out), payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:4000])
        return 0
    if args.command == "specify":
        spec = build_spec(inventory(Path(args.template)), inventory(Path(args.source)))
        write_json(Path(args.out), spec)
        print(json.dumps({"items": len(spec["items"]),
                          "unmapped_source_styles": len(spec["unmapped_source_styles"]),
                          "out": args.out}, ensure_ascii=False))
        return 0
    if args.command == "apply":
        spec = load_spec(Path(args.spec)) if args.spec else None
        report = apply_adaptation(Path(args.source), Path(args.template), Path(args.outdir), spec)
        print(json.dumps({k: report.get(k) for k in
                          ("applied", "reason", "adapted", "restyled_paragraphs",
                           "content_stream_preserved", "unmapped_styles")}, ensure_ascii=False))
        return 0 if report.get("applied") else 2
    if args.command == "verify":
        spec = load_spec(Path(args.spec)) if args.spec else None
        report = verify(Path(args.source), Path(args.output), spec, Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    if args.command == "preview":
        report = preview(Path(args.docx), Path(args.outdir))
        print(json.dumps({k: report.get(k) for k in
                          ("renderer_available", "pdf", "pngs", "note")}, ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
