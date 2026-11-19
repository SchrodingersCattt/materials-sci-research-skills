"""Dependency-free manuscript delivery: Markdown in, genuine DOCX/PPTX/PDF out.

Writing cases ask for an editable deliverable (DOCX, PPTX or SVG), a source map and a
verification record, and they explicitly warn that a renamed text file is not the target
format and that a partial result must name its limits. This module does exactly that with the
Python standard library only, so it works in a container with no doc-forge, no Office suite and
no network.

    build-docx  --md FILE [--md FILE ...] --out FILE     real minimal OOXML wordprocessing package
    build-pptx  --plan FILE --out FILE                   real minimal OOXML presentation package
    build-svg   --plan FILE --out FILE                   deterministic SVG diagram
    inspect     PATH                                     parts, media, text, structure, hashes
    verify      --out FILE [--md FILE ...]               proves the artifact is the real format
    preview     --docx FILE --outdir DIR                 real PDF/PNG through an Office renderer,
                                                         or an explicit note that none exists

The DOCX/PPTX writers emit small but genuine OOXML packages (content types, relationships,
styles, masters) that Word and PowerPoint open and that `inspect`/`verify` re-read. Markdown
support covers headings, paragraphs, bullet and numbered lists, GFM tables, block quotes,
horizontal rules and inline bold/italic/code — nothing more, and the walk over unsupported
constructs is reported rather than dropped silently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
SVG = "http://www.w3.org/2000/svg"

RELS_DOC = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

RELS_DOCX_INNER = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/styles" Target="styles.xml"/>
</Relationships>"""

RELS_PPTX = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/officeDocument" Target="ppt/presentation.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

CORE_PROPS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title></dc:title><dc:creator>skill runtime</dc:creator><cp:lastModifiedBy>skill runtime</cp:lastModifiedBy>
<dcterms:created xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z</dcterms:modified>
</cp:coreProperties>"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def x(text: str) -> str:
    return escape(str(text), {'"': "&quot;", "'": "&apos;"})


# --------------------------------------------------------------------------- markdown

BLOCK_FENCE = re.compile(r"^(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET = re.compile(r"^\s*[-*+]\s+(.*)$")
NUMBERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
QUOTE = re.compile(r"^\s*>\s?(.*)$")
RULE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def inline_runs(text: str) -> list:
    """Split a paragraph into (text, bold, italic, code, link) runs."""
    runs = []
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
            runs.append({"text": piece[2:-2], "bold": True})
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            runs.append({"text": piece[1:-1], "italic": True})
        elif piece.startswith("`") and piece.endswith("`") and len(piece) > 2:
            runs.append({"text": piece[1:-1], "code": True})
        elif piece.startswith("[") and "](" in piece:
            label, target = piece[1:-1].split("](", 1)
            runs.append({"text": label, "link": target})
        else:
            runs.append({"text": piece})
    return runs


def parse_markdown(text: str) -> dict:
    """Blocks for the writer plus an inventory of everything that is not supported."""
    blocks = []
    unsupported = []
    lines = text.replace("\r\n", "\n").split("\n")
    index = 0
    in_fence = False
    fence_blocks = 0
    while index < len(lines):
        line = lines[index]
        if BLOCK_FENCE.match(line.strip()):
            in_fence = not in_fence
            if in_fence:
                fence_blocks += 1
                unsupported.append({"kind": "code_fence", "line": index + 1,
                                    "detail": "code blocks are not laid out; the text is kept "
                                              "as a paragraph"})
            index += 1
            continue
        if in_fence:
            if line.strip():
                blocks.append({"type": "paragraph", "runs": [{"text": line}]})
            index += 1
            continue
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        heading = HEADING.match(stripped)
        if heading:
            blocks.append({"type": "heading", "level": len(heading.group(1)),
                           "runs": inline_runs(heading.group(2).strip())})
            index += 1
            continue
        if RULE.match(stripped):
            blocks.append({"type": "rule"})
            index += 1
            continue
        if TABLE_ROW.match(stripped) and index + 1 < len(lines) and TABLE_SEP.match(lines[index + 1]):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            index += 2
            rows = []
            while index < len(lines) and TABLE_ROW.match(lines[index].strip()):
                rows.append([c.strip() for c in lines[index].strip().strip("|").split("|")])
                index += 1
            blocks.append({"type": "table", "header": header, "rows": rows})
            continue
        bullet = BULLET.match(line)
        if bullet:
            items = []
            while index < len(lines) and BULLET.match(lines[index]):
                items.append(BULLET.match(lines[index]).group(1).strip())
                index += 1
            blocks.append({"type": "bullet_list", "items": items})
            continue
        numbered = NUMBERED.match(line)
        if numbered:
            items = []
            while index < len(lines) and NUMBERED.match(lines[index]):
                items.append(NUMBERED.match(lines[index]).group(1).strip())
                index += 1
            blocks.append({"type": "number_list", "items": items})
            continue
        if QUOTE.match(line):
            quoted = []
            while index < len(lines) and QUOTE.match(lines[index]):
                quoted.append(QUOTE.match(lines[index]).group(1).strip())
                index += 1
            blocks.append({"type": "quote", "runs": inline_runs(" ".join(quoted))})
            continue
        if stripped.startswith("<") and stripped.endswith(">"):
            unsupported.append({"kind": "raw_html", "line": index + 1,
                                "detail": "raw HTML/XML is treated as text"})
        paragraph = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not (
                HEADING.match(lines[index].strip()) or BULLET.match(lines[index])
                or NUMBERED.match(lines[index]) or QUOTE.match(lines[index])
                or TABLE_ROW.match(lines[index].strip()) or RULE.match(lines[index].strip())
                or BLOCK_FENCE.match(lines[index].strip())):
            paragraph.append(lines[index].strip())
            index += 1
        blocks.append({"type": "paragraph", "runs": inline_runs(" ".join(paragraph))})
    return {"blocks": blocks, "unsupported": unsupported, "code_fences": fence_blocks}


# --------------------------------------------------------------------------- docx writer

def run_xml(run: dict) -> str:
    properties = []
    if run.get("bold"):
        properties.append("<w:b/>")
    if run.get("italic"):
        properties.append("<w:i/>")
    if run.get("code"):
        properties.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>')
        properties.append('<w:shd w:val="clear" w:fill="F2F2F2"/>')
    if run.get("link"):
        properties.append('<w:color w:val="0563C1"/><w:u w:val="single"/>')
    pr = f"<w:rPr>{''.join(properties)}</w:rPr>" if properties else ""
    text = x(run.get("text", ""))
    return f'<w:r>{pr}<w:t xml:space="preserve">{text}</w:t></w:r>'


def paragraph_xml(block: dict, style: str, numbering: str = "") -> str:
    runs = "".join(run_xml(r) for r in block.get("runs") or [])
    if not runs:
        runs = "<w:r><w:t></w:t></w:r>"
    pr = []
    if style:
        pr.append(f'<w:pStyle w:val="{style}"/>')
    if numbering:
        pr.append(numbering)
    prefix = f"<w:pPr>{''.join(pr)}</w:pPr>" if pr else ""
    return f"<w:p>{prefix}{runs}</w:p>"


def table_xml(header: list, rows: list) -> str:
    columns = max([len(header)] + [len(r) for r in rows]) if rows or header else 1
    width = 9360 // max(columns, 1)
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for _ in range(columns))

    def cell(value: str, bold: bool) -> str:
        runs = [{"text": part.get("text", "")} for part in inline_runs(value)]
        if bold:
            runs = [{**r, "bold": True} for r in runs] or [{"text": "", "bold": True}]
        body = "".join(run_xml(r) for r in runs)
        return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:pPr><w:pStyle w:val="TableText"/></w:pPr>{body}</w:p></w:tc>')

    body = ["<w:tr>" + "".join(cell(header[i] if i < len(header) else "", True)
                              for i in range(columns)) + "</w:tr>"]
    for row in rows:
        body.append("<w:tr>" + "".join(cell(row[i] if i < len(row) else "", False)
                                      for i in range(columns)) + "</w:tr>")
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
            f'<w:tblW w:w="9360" w:type="dxa"/><w:tblBorders>'
            '<w:top w:val="single" w:sz="8" w:color="000000"/>'
            '<w:left w:val="single" w:sz="4" w:color="000000"/>'
            '<w:bottom w:val="single" w:sz="8" w:color="000000"/>'
            '<w:right w:val="single" w:sz="4" w:color="000000"/>'
            '<w:insideH w:val="single" w:sz="4" w:color="000000"/>'
            '<w:insideV w:val="single" w:sz="4" w:color="000000"/>'
            '</w:tblBorders></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{"".join(body)}</w:tbl>')


def docx_styles(font: str, size_half_points: int) -> str:
    def style(style_id: str, name: str, *, outline=None, size=None, bold=False,
              align=None, before=None, after=None, default=False, quote=False, based="Normal"):
        props = [f'<w:pStyle w:val="{style_id}"/>'] if False else []
        return (
            f'<w:style w:type="paragraph" w:styleId="{style_id}"'
            + (' w:default="1"' if default else "") + ">"
            f'<w:name w:val="{name}"/>'
            + ("" if default else f'<w:basedOn w:val="{based}"/>')
            + "<w:pPr>"
            + (f'<w:jc w:val="{align}"/>' if align else "")
            + (f'<w:spacing w:before="{before}" w:after="{after}"/>'
               if before is not None or after is not None else "")
            + (f'<w:outlineLvl w:val="{outline}"/>' if outline is not None else "")
            + (f'<w:ind w:left="720"/>' if quote else "")
            + "</w:pPr><w:rPr>"
            + (f'<w:sz w:val="{size}"/>' if size else "")
            + ("<w:b/>" if bold else "")
            + "</w:rPr></w:style>")

    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles xmlns:w="{W}">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>'
            f'<w:sz w:val="{size_half_points}"/></w:rPr></w:rPrDefault>'
            "<w:pPrDefault><w:pPr><w:spacing w:after=\"120\" w:line=\"276\" "
            'w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
            + style("Normal", "Normal", default=True, size=size_half_points)
            + style("Title", "Title", size=36, bold=True, align="center", before="0", after="240")
            + "".join(style(f"Heading{i}", f"heading {i}", outline=i - 1, bold=True,
                            size=max(size_half_points, 28 - 2 * (i - 1)), before="240", after="120")
                      for i in range(1, 7))
            + style("Quote", "Quote", quote=True, align="both", before="120", after="120")
            + style("TableText", "Table Text", size=max(size_half_points - 2, 16))
            + style("ListItem", "List Paragraph", before="0", after="60")
            + '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
            '<w:tblPr><w:tblCellMar><w:top w:w="60" w:type="dxa"/>'
            '<w:left w:w="90" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/>'
            '<w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
            "</w:styles>")


def build_docx(markdown_files: list, out_path: Path, *, font: str = "Liberation Serif",
               size_half_points: int = 22, page=(11906, 16838),
               margins=("1417", "1417", "1417", "1417")) -> dict:
    body_parts = []
    inventory = []
    for path, markdown in markdown_files:
        parsed = parse_markdown(markdown)
        inventory.append({"path": str(path), "sha256": sha256_bytes(markdown.encode("utf-8")),
                          "blocks": len(parsed["blocks"]),
                          "unsupported": parsed["unsupported"]})
        for block in parsed["blocks"]:
            kind = block["type"]
            if kind == "heading":
                level = min(max(block["level"], 1), 6)
                body_parts.append(paragraph_xml(block, "Title" if level == 1 else f"Heading{min(level, 6)}"))
            elif kind == "paragraph":
                body_parts.append(paragraph_xml(block, "Normal"))
            elif kind == "quote":
                body_parts.append(paragraph_xml(block, "Quote"))
            elif kind == "rule":
                body_parts.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" '
                                  'w:space="1" w:color="808080"/></w:pBdr></w:pPr></w:p>')
            elif kind == "table":
                body_parts.append(table_xml(block["header"], block["rows"]))
                body_parts.append(paragraph_xml({"runs": [{"text": ""}]}, "Normal"))
            elif kind in ("bullet_list", "number_list"):
                for item in block["items"]:
                    numbering = ('<w:numPr><w:ilvl w:val="0"/>'
                                 f'<w:numId w:val="{1 if kind == "bullet_list" else 2}"/></w:numPr>')
                    body_parts.append(paragraph_xml({"runs": inline_runs(item)}, "ListItem", numbering))
    body = "".join(body_parts)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{W}"><w:body>{body}'
                f'<w:sectPr><w:pgSz w:w="{page[0]}" w:h="{page[1]}"/>'
                f'<w:pgMar w:top="{margins[0]}" w:right="{margins[1]}" w:bottom="{margins[2]}" '
                f'w:left="{margins[3]}" w:header="708" w:footer="708" w:gutter="0"/>'
                '<w:cols w:num="1" w:space="708"/></w:sectPr></w:body></w:document>')
    numbering = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 f'<w:numbering xmlns:w="{W}">'
                 '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>'
                 '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
                 '<w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
                 '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
                 '<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/>'
                 '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
                 '<w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>'
                 '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
                 '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
                 '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num></w:numbering>')
    rels_inner = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  f'<Relationships xmlns="{PKG_REL}">'
                  f'<Relationship Id="rId1" Type="{R}/styles" Target="styles.xml"/>'
                  f'<Relationship Id="rId2" Type="{R}/numbering" Target="numbering.xml"/>'
                  "</Relationships>")
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     f'<Types xmlns="{CT}">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                     '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                     "</Types>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", content_types)
        package.writestr("_rels/.rels", RELS_DOC)
        package.writestr("word/_rels/document.xml.rels", rels_inner)
        package.writestr("word/document.xml", document)
        package.writestr("word/styles.xml", docx_styles(font, size_half_points))
        package.writestr("word/numbering.xml", numbering)
        package.writestr("docProps/core.xml", CORE_PROPS)
    report = {
        "schema": "manuscript-build/v1",
        "kind": "docx",
        "out": str(out_path),
        "sha256": sha256_file(out_path),
        "bytes": out_path.stat().st_size,
        "inputs": inventory,
        "font": font,
        "size_half_points": size_half_points,
        "page_size": {"w": str(page[0]), "h": str(page[1])},
        "margins": {"top": margins[0], "right": margins[1], "bottom": margins[2], "left": margins[3]},
        "features": ["headings 1-6", "paragraphs with inline bold/italic/code/link runs",
                     "GFM tables", "bullet and numbered lists", "block quotes",
                     "horizontal rules", "document defaults, page size, margins, numbering"],
        "limitations": ["This writer lays out text, tables and lists. It does not embed images, "
                        "footnotes, equations, tracked changes or a TOC field; a case that "
                        "requires them must supply a template path instead."],
        "unsupported_constructs": [u for entry in inventory for u in entry["unsupported"]],
    }
    (out_path.parent / "build-docx-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# --------------------------------------------------------------------------- pptx writer

def slide_xml(title_runs: list, bullets: list) -> str:
    def runs_xml(items) -> str:
        return "".join(
            f'<a:r><a:rPr lang="en-US" b="{"1" if item.get("bold") else "0"}"/>'
            f'<a:t>{x(item.get("text", ""))}</a:t></a:r>' for item in items)

    body = [f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/>'
            '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="457200" y="274638"/><a:ext cx="8229600" cy="1143000"/>'
            '</a:xfrm></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>'
            f'<a:p>{runs_xml(title_runs or [{"text": ""}])}</a:p></p:txBody></p:sp>']
    if bullets:
        paragraphs = []
        for item in bullets:
            runs = inline_runs(item)
            paragraphs.append(f'<a:p><a:pPr lvl="0" marL="342900" indent="-342900">'
                              f'<a:buChar char="•"/></a:pPr>{runs_xml(runs)}</a:p>')
        body.append('<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content"/>'
                    '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
                    '<p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr>'
                    '<p:spPr><a:xfrm><a:off x="457200" y="1600200"/>'
                    '<a:ext cx="8229600" cy="4525963"/></a:xfrm></p:spPr>'
                    '<p:txBody><a:bodyPr/><a:lstStyle/>'
                    + "".join(paragraphs) + "</p:txBody></p:sp>")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sld xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + "".join(body) + "</p:spTree></p:cSld>"
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def build_pptx(plan_path: Path, out_path: Path) -> dict:
    """plan: {"slides": [{"title": "...", "bullets": ["..."]}]}"""
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    slides = plan.get("slides") or []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     f'<Types xmlns="{CT}">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
                     '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
                     '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
                     '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>']
    for index in range(1, len(slides) + 1):
        content_types.append(f'<Override PartName="/ppt/slides/slide{index}.xml" '
                             'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    content_types.append("</Types>")

    slide_ids = []
    for index, _slide in enumerate(slides, start=1):
        slide_ids.append(f'<p:sldId id="{255 + index}" r:id="rId{index + 1}"/>')
    presentation = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    f'<p:presentation xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">'
                    '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                    f'<p:sldIdLst>{"".join(slide_ids)}</p:sldIdLst>'
                    '<p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>'
                    '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
    presentation_rels = [f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                         f'<Relationships xmlns="{PKG_REL}">'
                         '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for index in range(1, len(slides) + 1):
        presentation_rels.append(
            f'<Relationship Id="rId{index + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
            f'Target="slides/slide{index}.xml"/>')
    presentation_rels.append('<Relationship Id="rId%d" '
                             'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" '
                             'Target="theme/theme1.xml"/></Relationships>'
                             % (len(slides) + 2))

    master = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              f'<p:sldMaster xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">'
              '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
              '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
              '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
              '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
              '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title Placeholder"/>'
              '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
              '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
              '<p:spPr><a:xfrm><a:off x="457200" y="274638"/>'
              '<a:ext cx="8229600" cy="1143000"/></a:xfrm></p:spPr>'
              '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
              '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content Placeholder"/>'
              '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
              '<p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr>'
              '<p:spPr><a:xfrm><a:off x="457200" y="1600200"/>'
              '<a:ext cx="8229600" cy="4525963"/></a:xfrm></p:spPr>'
              '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
              "</p:spTree></p:cSld>"
              '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
              'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
              'accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
              '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
              '<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>'
              "</p:sldMaster>")
    master_rels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<Relationships xmlns="{PKG_REL}">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
                   "</Relationships>")
    layout = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              f'<p:sldLayout xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}" type="titleAndContent">'
              '<p:cSld name="Title and Content"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
              '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
              '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
              '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
              '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/>'
              '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
              '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
              '<p:spPr><a:xfrm><a:off x="457200" y="274638"/>'
              '<a:ext cx="8229600" cy="1143000"/></a:xfrm></p:spPr>'
              '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
              '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content"/>'
              '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
              '<p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr>'
              '<p:spPr><a:xfrm><a:off x="457200" y="1600200"/>'
              '<a:ext cx="8229600" cy="4525963"/></a:xfrm></p:spPr>'
              '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
              "</p:spTree></p:cSld>"
              '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
    layout_rels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<Relationships xmlns="{PKG_REL}">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
                   "</Relationships>")
    theme = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             f'<a:theme xmlns:a="{A}" name="Office Theme">'
             '<a:themeElements><a:clrScheme name="Office">'
             + "".join(f'<a:{slot}><a:srgbClr val="{color}"/></a:{slot}>' for slot, color in (
                 ("dk1", "000000"), ("lt1", "FFFFFF"), ("dk2", "44546A"), ("lt2", "E7E6E6"),
                 ("accent1", "4472C4"), ("accent2", "ED7D31"), ("accent3", "A5A5A5"),
                 ("accent4", "FFC000"), ("accent5", "5B9BD5"), ("accent6", "70AD47"),
                 ("hlink", "0563C1"), ("folHlink", "954F72")))
             + '</a:clrScheme>'
             '<a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri Light"/>'
             '<a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
             '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/>'
             '</a:minorFont></a:fontScheme>'
             '<a:fmtScheme name="Office">'
             + "".join(f'<a:{group}><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:{group}>'
                       for group in ("fillStyleLst", "lnStyleLst", "effectStyleLst",
                                     "bgFillStyleLst"))
             + "</a:fmtScheme></a:themeElements></a:theme>")
    slide_rels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  f'<Relationships xmlns="{PKG_REL}">'
                  '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
                  "</Relationships>")

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", "".join(content_types))
        package.writestr("_rels/.rels", RELS_PPTX)
        package.writestr("docProps/core.xml", CORE_PROPS)
        package.writestr("ppt/presentation.xml", presentation)
        package.writestr("ppt/_rels/presentation.xml.rels", "".join(presentation_rels))
        package.writestr("ppt/slideMasters/slideMaster1.xml", master)
        package.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", master_rels)
        package.writestr("ppt/slideLayouts/slideLayout1.xml", layout)
        package.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", layout_rels)
        package.writestr("ppt/theme/theme1.xml", theme)
        for index, slide in enumerate(slides, start=1):
            package.writestr(f"ppt/slides/slide{index}.xml",
                             slide_xml(inline_runs(slide.get("title") or ""),
                                       slide.get("bullets") or []))
            package.writestr(f"ppt/slides/_rels/slide{index}.xml.rels", slide_rels)
    report = {
        "schema": "manuscript-build/v1",
        "kind": "pptx",
        "out": str(out_path),
        "sha256": sha256_file(out_path),
        "bytes": out_path.stat().st_size,
        "plan": str(plan_path),
        "slides": len(slides),
        "slide_titles": [s.get("title") for s in slides],
        "features": ["true OOXML presentation package", "title and content placeholders",
                     "slide master, layout and theme parts", "bullet paragraphs with inline runs",
                     "4:3 9144000x6858000 slide size"],
        "limitations": ["No images, charts, speaker notes or transitions are written; a case that "
                        "requires them must supply its own template or the agent must add them "
                        "with a real tool."],
    }
    (out_path.parent / "build-pptx-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# --------------------------------------------------------------------------- svg writer

def build_svg(plan_path: Path, out_path: Path) -> dict:
    """plan: {"width":.., "height":.., "nodes":[{"id","x","y","w","h","label","kind"}],
              "edges":[{"from","to","label"}]}"""
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    width = int(plan.get("width") or 960)
    height = int(plan.get("height") or 540)
    nodes = plan.get("nodes") or []
    edges = plan.get("edges") or []
    positions = {node["id"]: node for node in nodes}
    parts = [f'<svg xmlns="{SVG}" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" role="img">',
             '<rect width="100%" height="100%" fill="#ffffff"/>']
    for edge in edges:
        source, target = positions.get(edge.get("from")), positions.get(edge.get("to"))
        if not source or not target:
            continue
        x1 = float(source["x"]) + float(source.get("w", 0)) / 2
        y1 = float(source["y"]) + float(source.get("h", 0)) / 2
        x2 = float(target["x"]) + float(target.get("w", 0)) / 2
        y2 = float(target["y"]) + float(target.get("h", 0)) / 2
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     'stroke="#4b5563" stroke-width="1.6" marker-end="url(#arrow)"/>')
        if edge.get("label"):
            parts.append(f'<text x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2 - 6:.1f}" '
                         'font-family="Helvetica, Arial, sans-serif" font-size="12" '
                         'text-anchor="middle" fill="#374151">'
                         f'{x(edge["label"])}</text>')
    parts.insert(2, '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
                    'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
                    '<path d="M 0 0 L 10 5 L 0 10 z" fill="#4b5563"/></marker></defs>')
    palette = {"input": "#e0f2fe", "process": "#f1f5f9", "decision": "#fef9c3",
               "output": "#dcfce7", "note": "#fae8ff"}
    for node in nodes:
        fill = palette.get(node.get("kind") or "process", "#f1f5f9")
        parts.append(f'<rect x="{node["x"]}" y="{node["y"]}" width="{node.get("w", 180)}" '
                     f'height="{node.get("h", 64)}" rx="8" fill="{fill}" stroke="#334155" '
                     'stroke-width="1.2"/>')
        parts.append(f'<text x="{float(node["x"]) + float(node.get("w", 180)) / 2:.1f}" '
                     f'y="{float(node["y"]) + float(node.get("h", 64)) / 2 + 5:.1f}" '
                     'font-family="Helvetica, Arial, sans-serif" font-size="14" '
                     f'text-anchor="middle" fill="#0f172a">{x(node.get("label", node["id"]))}</text>')
    if plan.get("caption"):
        parts.append(f'<text x="{width / 2:.0f}" y="{height - 14}" '
                     'font-family="Helvetica, Arial, sans-serif" font-size="13" '
                     f'text-anchor="middle" fill="#334155">{x(plan["caption"])}</text>')
    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    report = {
        "schema": "manuscript-build/v1",
        "kind": "svg",
        "out": str(out_path),
        "sha256": sha256_file(out_path),
        "bytes": out_path.stat().st_size,
        "plan": str(plan_path),
        "nodes": len(nodes),
        "edges": len(edges),
        "features": ["vector source with explicit node/edge coordinates", "arrow markers",
                     "legend-free flat palette", "caption text"],
        "limitations": ["Text metrics are not measured: a label longer than its box overflows. "
                        "Check the rendered PNG and shorten labels rather than guessing."],
    }
    (out_path.parent / "build-svg-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# --------------------------------------------------------------------------- inspection

def inspect_office(path: Path) -> dict:
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        parts = {name: package.read(name) for name in names}
    kind = "docx" if "word/document.xml" in parts else (
        "pptx" if "ppt/presentation.xml" in parts else "unknown")
    info = {
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "kind": kind,
        "parts": sorted(names),
        "part_count": len(names),
        "has_content_types": "[Content_Types].xml" in parts,
        "has_root_rels": "_rels/.rels" in parts,
        "media": sorted(n for n in names if "/media/" in n),
    }
    if kind == "docx":
        raw = parts["word/document.xml"]
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", raw.decode("utf-8", "replace")))
        info.update({
            "text_chars": len(text),
            "paragraphs": raw.count(b"<w:p>") + raw.count(b"<w:p "),
            "tables": raw.count(b"<w:tbl>"),
            "headings": len(re.findall(r'w:val="Heading\d"', raw.decode("utf-8", "replace"))),
            "has_styles": "word/styles.xml" in parts,
            "has_numbering": "word/numbering.xml" in parts,
            "has_footnotes": "word/footnotes.xml" in parts,
            "first_text": text[:200],
        })
    elif kind == "pptx":
        slides = sorted(n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n))
        info.update({
            "slides": len(slides),
            "has_master": any(n.startswith("ppt/slideMasters/") and n.endswith(".xml") for n in names),
            "has_layout": any(n.startswith("ppt/slideLayouts/") and n.endswith(".xml") for n in names),
            "has_theme": "ppt/theme/theme1.xml" in parts,
        })
        texts = []
        for name in slides:
            texts.extend(re.findall(r"<a:t>([^<]*)</a:t>", parts[name].decode("utf-8", "replace")))
        info["slide_texts"] = texts[:12]
        info["slide_text_chars"] = sum(len(t) for t in texts)
    return info


def verify_outputs(out_paths: list, markdown_files: list, outdir: Path) -> dict:
    checks = []

    def add(check_id, requirement, ok, evidence, locator):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence, "locator": locator})

    for path in out_paths:
        path = Path(path)
        if not path.exists():
            add(f"exists:{path.name}", f"{path.name} exists", False, "missing", str(path))
            continue
        suffix = path.suffix.lower()
        if suffix in (".docx", ".pptx"):
            try:
                info = inspect_office(path)
                ok = info["kind"] == suffix.lstrip(".") and info["has_content_types"] \
                    and info["has_root_rels"]
                add(f"format:{path.name}", f"{path.name} is a real {suffix.lstrip('.').upper()} package",
                    ok, f"kind={info['kind']} parts={info['part_count']} "
                        f"content_types={info['has_content_types']}", str(path))
                if suffix == ".docx":
                    text = info.get("first_text") or ""
                    add(f"text:{path.name}", "the document carries its text (not an empty shell)",
                        (info.get("text_chars") or 0) > 0,
                        f"text_chars={info.get('text_chars')} tables={info.get('tables')} "
                        f"headings={info.get('headings')} preview={text[:60]!r}", str(path))
                else:
                    add(f"slides:{path.name}", "the deck has slides with text",
                        (info.get("slides") or 0) > 0 and (info.get("slide_text_chars") or 0) > 0,
                        f"slides={info.get('slides')} text_chars={info.get('slide_text_chars')}",
                        str(path))
            except (zipfile.BadZipFile, KeyError, OSError) as error:
                add(f"format:{path.name}", f"{path.name} opens as an OOXML package", False,
                    repr(error), str(path))
        elif suffix == ".svg":
            text = path.read_text(encoding="utf-8", errors="replace")
            add(f"format:{path.name}", f"{path.name} is an SVG document",
                text.lstrip().startswith("<svg") and "</svg>" in text,
                f"bytes={len(text)} elements={text.count('<')}", str(path))
        else:
            add(f"exists:{path.name}", f"{path.name} is present",
                path.stat().st_size > 0, f"bytes={path.stat().st_size}", str(path))

    for path, markdown in markdown_files:
        words = [w for w in re.findall(r"[A-Za-z\u4e00-\u9fff]{3,}", markdown)]
        sample = words[:40]
        joined = "".join(inspect_office(Path(out_paths[0])).get("first_text", "")
                         if Path(out_paths[0]).suffix.lower() == ".docx" else "")
        present = sum(1 for w in sample if w in joined)
        add(f"input_kept:{Path(path).name}",
            "the first part of the source text is present in the deliverable",
            not sample or present > 0,
            f"{present}/{len(sample)} sampled source words appear in the document preview",
            str(path))

    failures = [c for c in checks if c["status"] == "fail"]
    report = {
        "schema": "manuscript-verify/v1",
        "checks": checks,
        "passed": len(checks) - len(failures),
        "failed": len(failures),
        "status": "verified" if not failures else "needs_work",
        "scope_note": "Proves the artifacts are the real container formats and carry text that "
                      "comes from the supplied Markdown. It does not certify scientific content or "
                      "an official score.",
    }
    Path(outdir).mkdir(parents=True, exist_ok=True)
    (Path(outdir) / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def preview(docx: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    result = {"schema": "manuscript-preview/v1", "docx": str(docx),
              "renderer_available": bool(soffice), "pdf": None, "pngs": []}
    if not soffice:
        result["note"] = ("no LibreOffice/soffice on PATH: no PDF preview was rendered. The "
                          "editable artifact remains the deliverable, and the missing preview is "
                          "an explicit limitation.")
    else:
        proc = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir",
                               str(outdir), str(docx)], capture_output=True, text=True, timeout=420)
        pdf = outdir / (Path(docx).stem + ".pdf")
        result["returncode"] = proc.returncode
        result["stdout_tail"] = (proc.stdout or "")[-600:]
        result["stderr_tail"] = (proc.stderr or "")[-600:]
        if pdf.exists():
            result["pdf"] = str(pdf)
            pdftoppm = shutil.which("pdftoppm")
            if pdftoppm:
                subprocess.run([pdftoppm, "-png", "-r", "110", "-f", "1", "-l", "3", str(pdf),
                                str(outdir / "page")], capture_output=True, text=True, timeout=300)
                result["pngs"] = sorted(str(p) for p in outdir.glob("page*.png"))
            pdffonts = shutil.which("pdffonts")
            if pdffonts:
                fonts = subprocess.run([pdffonts, str(pdf)], capture_output=True, text=True,
                                       timeout=180)
                result["pdf_font_report"] = (fonts.stdout or "").strip().splitlines()[:40]
        else:
            result["note"] = "the renderer ran but produced no PDF; keep the editable artifact"
    (outdir / "preview-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    return result


# --------------------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Dependency-free manuscript delivery")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build-docx"); p.add_argument("--md", action="append", required=True)
    p.add_argument("--out", required=True); p.add_argument("--font", default="Liberation Serif")
    p.add_argument("--size-half-points", type=int, default=22)

    p = sub.add_parser("build-pptx"); p.add_argument("--plan", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("build-svg"); p.add_argument("--plan", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("inspect"); p.add_argument("path"); p.add_argument("--out")
    p = sub.add_parser("verify"); p.add_argument("--out-file", action="append", required=True)
    p.add_argument("--md", action="append", default=[]); p.add_argument("--outdir", required=True)
    p = sub.add_parser("preview"); p.add_argument("--docx", required=True); p.add_argument("--outdir", required=True)

    args = parser.parse_args(argv)
    if args.command == "build-docx":
        files = [(Path(p), Path(p).read_text(encoding="utf-8", errors="replace")) for p in args.md]
        report = build_docx(files, Path(args.out), font=args.font,
                            size_half_points=args.size_half_points)
        print(json.dumps({k: report[k] for k in ("out", "sha256", "bytes", "font")},
                         ensure_ascii=False))
        return 0
    if args.command == "build-pptx":
        report = build_pptx(Path(args.plan), Path(args.out))
        print(json.dumps({k: report[k] for k in ("out", "sha256", "slides")}, ensure_ascii=False))
        return 0
    if args.command == "build-svg":
        report = build_svg(Path(args.plan), Path(args.out))
        print(json.dumps({k: report[k] for k in ("out", "sha256", "nodes", "edges")},
                         ensure_ascii=False))
        return 0
    if args.command == "inspect":
        payload = inspect_office(Path(args.path))
        if args.out:
            Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:3000])
        return 0
    if args.command == "verify":
        files = [(Path(p), Path(p).read_text(encoding="utf-8", errors="replace")) for p in args.md]
        report = verify_outputs(args.out_file, files, Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    if args.command == "preview":
        result = preview(Path(args.docx), Path(args.outdir))
        print(json.dumps({k: result.get(k) for k in ("renderer_available", "pdf", "pngs", "note")},
                         ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
