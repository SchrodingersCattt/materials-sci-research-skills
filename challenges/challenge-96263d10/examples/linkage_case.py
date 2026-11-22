"""Build a realistic-size manuscript for the caption/cross-reference/reference apparatus test.

Everything here is invented for interface testing only. It is NOT a formal case, NOT an
official answer and NOT a score. The manuscript is deliberately paper-sized (about forty
paragraphs, three figures, two tables, two equations, a twelve-entry reference list) because
a five-row fixture does not exercise document order, caption families or a real reference
section. Two variants are written:

  manuscript-defective.docx  caption numbers out of sequence, a duplicated caption number, an
                             in-text reference that points at no caption, a duplicated
                             reference entry and a non-monotonic numeric reference label
  manuscript-clean.docx      the same document with every one of those defects removed

The DOCX parts are minimal but valid packages: a drawing is an empty ``w:drawing`` element and
an equation an ``m:oMath`` element, which is what a format audit reads.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def style(style_id: str, name: str, *, outline=None, size=None, bold=False, align=None,
          before=None, after=None, line=None, based_on=None, default=False) -> str:
    bits = [f'<w:style w:type="paragraph" w:styleId="{style_id}"'
            + (' w:default="1"' if default else "") + ">",
            f'<w:name w:val="{name}"/>']
    if based_on:
        bits.append(f'<w:basedOn w:val="{based_on}"/>')
    ppr = []
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    if before is not None or after is not None or line is not None:
        spacing = "<w:spacing"
        if before is not None:
            spacing += f' w:before="{before}"'
        if after is not None:
            spacing += f' w:after="{after}"'
        if line is not None:
            spacing += f' w:line="{line}" w:lineRule="auto"'
        ppr.append(spacing + "/>")
    if outline is not None:
        ppr.append(f'<w:outlineLvl w:val="{outline}"/>')
    if ppr:
        bits.append("<w:pPr>" + "".join(ppr) + "</w:pPr>")
    rpr = []
    if size:
        rpr.append(f'<w:sz w:val="{size}"/>')
    if bold:
        rpr.append("<w:b/>")
    if rpr:
        bits.append("<w:rPr>" + "".join(rpr) + "</w:rPr>")
    bits.append("</w:style>")
    return "".join(bits)


def styles_xml(entries: list, doc_default_font: str, doc_default_size: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles xmlns:w="{W}" xmlns:m="{M}">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            f'<w:rFonts w:ascii="{doc_default_font}" w:hAnsi="{doc_default_font}" '
            f'w:eastAsia="{doc_default_font}"/>'
            f'<w:sz w:val="{doc_default_size}"/></w:rPr></w:rPrDefault>'
            "<w:pPrDefault><w:pPr/></w:pPrDefault></w:docDefaults>"
            + "".join(entries) + "</w:styles>")


def paragraph(text: str, style_id: str = "", runs: str = "") -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style_id}"/></w:pPr>' if style_id else ""
    body = runs or f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'
    return f"<w:p>{ppr}{body}</w:p>"


def split_runs(parts: list) -> str:
    """Build one paragraph whose text is split across runs, the way Word writes edited text."""
    return "".join(f'<w:r><w:t xml:space="preserve">{part}</w:t></w:r>' for part in parts)


def drawing_paragraph(style_id: str = "") -> str:
    return paragraph("", style_id, runs=f'<w:r><w:drawing/></w:r>')


def equation_paragraph(style_id: str = "") -> str:
    return paragraph("", style_id, runs=f'<w:r><m:oMath/></w:r>')


def table(rows: list, style_id: str = "") -> str:
    style = f'<w:tblStyle w:val="{style_id}"/>' if style_id else ""
    xml = [f'<w:tbl><w:tblPr>{style}<w:tblW w:w="9000" w:type="dxa"/></w:tblPr>'
           '<w:tblGrid><w:gridCol w:w="4500"/><w:gridCol w:w="4500"/></w:tblGrid>']
    for values in rows:
        cells = "".join(f'<w:tc><w:tcPr><w:tcW w:w="4500" w:type="dxa"/></w:tcPr>'
                        f'<w:p><w:r><w:t>{value}</w:t></w:r></w:p></w:tc>' for value in values)
        xml.append(f"<w:tr>{cells}</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def document_xml(body: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{W}" xmlns:m="{M}"><w:body>{body}'
            '<w:sectPr>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417" '
            'w:header="708" w:footer="708" w:gutter="0"/>'
            '<w:cols w:num="1" w:space="708"/>'
            '<w:docGrid w:type="lines" w:linePitch="312"/>'
            "</w:sectPr></w:body></w:document>")


def write_docx(path: Path, document: str, styles: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", RELS)
        package.writestr("word/_rels/document.xml.rels", DOC_RELS)
        package.writestr("word/document.xml", document)
        package.writestr("word/styles.xml", styles)


FIGURE_TEXT = ("Filled specimens reached {value} MPa, against {other} MPa for the unfilled "
               "reference set (Table 1).")
SECTION_TITLES = ["Introduction", "Materials and methods", "Results", "Discussion", "Conclusion"]


def manuscript_body(defective: bool) -> str:
    """The full manuscript body; ``defective`` plants the caption/reference defects."""
    blocks = [
        paragraph("Strengthening of filled polymer specimens under cyclic loading", "Title"),
        paragraph("Abstract", "Heading1"),
        paragraph("Filled and unfilled specimens are compared across three loading regimes. "
                  "No significance test is reported in the supplied material."),
        paragraph("Keywords", "Heading1"),
        paragraph("filled polymer; cyclic loading; strength", "BodyText"),
    ]
    section = 0
    figure_index = 0
    table_index = 0
    for index in range(1, 41):
        if index in (1, 6, 20, 30, 36):
            section += 1
            blocks.append(paragraph(SECTION_TITLES[section - 1], "Heading1"))
        if index == 24:
            blocks.append(paragraph("A subsection of the results.", "Heading2"))
        text = (f"Paragraph {index} of the synthetic manuscript. "
                f"Specimen batch {index} was prepared as described and the measured response is "
                f"recorded in the supplied material.")
        if index in (4, 12, 22):
            figure_index += 1
            reference = figure_index
            if defective and figure_index == 3:
                reference = 9  # points at a figure that does not exist
            text += f" The response follows the trend in Figure {reference}."
        if index in (9, 26):
            table_index += 1
            text += f" The composition is listed in Table {table_index}."
        if index == 16:
            text += " Equation 1 gives the fitted relation."
        blocks.append(paragraph(text))
        if index in (4, 12, 22):
            blocks.append(paragraph("", "", runs=split_runs(["The measured ", "response for ",
                                                             "batch ", str(index), "."])))
        if index in (10, 27):
            blocks.append(table([["Batch", "Strength (MPa)"], [f"B{index}", "31.2"]]))
        if index in (4, 12, 22):
            blocks.append(drawing_paragraph())
            declared = figure_index
            if defective:
                declared = {1: 2, 2: 3, 3: 5}[figure_index]
            blocks.append(paragraph(f"Figure {declared}. Measured response for batch {index}.",
                                    "Caption"))
        if index in (9, 26):
            caption_number = table_index
            blocks.append(paragraph(f"Table {caption_number}. Composition of batch {index}.", "Caption"))
        if index == 16:
            blocks.append(equation_paragraph())
            blocks.append(paragraph("Equation 1. Fitted relation between load and response.",
                                    "Caption"))
    blocks.append(paragraph("References", "Heading1"))
    entries = [
        "[1] A. Author. Filled polymers under load. Journal of Synthetic Studies, 2019.",
        "[2] B. Author and C. Author. Cyclic loading of polymer composites. Synthetic Reviews, 2020.",
        "[3] D. Author. Strength of filled specimens. Synthetic Reports, 2018.",
        "[4] E. Author et al. Preparation of unloaded reference sets. Synthetic Methods, 2021.",
        "[5] F. Author. Statistical treatment of two-specimen comparisons. Synthetic Notes, 2017.",
        "[6] G. Author. Filler dispersion and mechanical response. Synthetic Letters, 2022.",
        "[7] H. Author. Fatigue in filled systems. Synthetic Reviews, 2020.",
        "[8] I. Author. Batch-to-batch variability. Synthetic Reports, 2019.",
        "[9] J. Author. Testing standards for filled polymers. Synthetic Standards, 2016.",
        "[10] K. Author. Long-term stability of filled specimens. Synthetic Reports, 2023.",
        "[11] L. Author. Filler content and strength. Synthetic Letters, 2021.",
        "[12] M. Author. A review of filled polymer strength. Synthetic Reviews, 2024.",
    ]
    if defective:
        entries[3] = entries[2]  # duplicated entry
        entries[6], entries[7] = "[8] H. Author. Fatigue in filled systems. Synthetic Reviews, 2020.", \
                                 "[7] I. Author. Batch-to-batch variability. Synthetic Reports, 2019."
    blocks += [paragraph(entry, "Bibliography") for entry in entries]
    return "".join(blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Realistic apparatus fixture")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    styles = styles_xml([
        style("Normal", "Normal", default=True, size="21", after="120"),
        style("Title", "Title", size="32", bold=True, align="center"),
        style("Heading1", "heading 1", outline=0, size="28", bold=True),
        style("Heading2", "heading 2", outline=1, size="24", bold=True),
        style("BodyText", "Body Text", size="21", align="both", line="360"),
        style("Caption", "Caption", size="18", align="center", before="60", after="180"),
        style("Bibliography", "Bibliography", size="18", after="60"),
    ], doc_default_font="Liberation Serif", doc_default_size="21")

    for name, defective in (("manuscript-defective.docx", True),
                            ("manuscript-clean.docx", False)):
        write_docx(out / name, document_xml(manuscript_body(defective)), styles)

    print(f"realistic apparatus fixture written to {out}: manuscript-defective.docx, "
          f"manuscript-clean.docx")
    print("This fixture is not a formal case and is not an official answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
