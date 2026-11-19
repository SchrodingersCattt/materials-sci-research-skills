"""Build a synthetic manuscript + journal template pair for self-testing.

Everything here is invented for interface testing only. It is NOT a formal case,
NOT an official answer, and it must never be presented as one. The pair exists so
that the adaptation pipeline can be executed and checked without network access,
doc-forge, or an Office suite.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

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
            + (' w:default="1"' if default else "") + ">"]
    bits.append(f'<w:name w:val="{name}"/>')
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
            f'<w:styles xmlns:w="{W}">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            f'<w:rFonts w:ascii="{doc_default_font}" w:hAnsi="{doc_default_font}" w:eastAsia="{doc_default_font}"/>'
            f'<w:sz w:val="{doc_default_size}"/></w:rPr></w:rPrDefault>'
            "<w:pPrDefault><w:pPr/></w:pPrDefault></w:docDefaults>"
            + "".join(entries) + "</w:styles>")


def paragraph(text: str, style_id: str = "") -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style_id}"/></w:pPr>' if style_id else ""
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'


def header_row(values: list) -> str:
    cells = "".join(f'<w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr>'
                    f'<w:p><w:r><w:t>{v}</w:t></w:r></w:p></w:tc>' for v in values)
    return f'<w:tr>{cells}</w:tr>'


def document_xml(body: str, *, page: tuple, margins: tuple, columns: int) -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{W}"><w:body>{body}'
            + '<w:sectPr>'
            + f'<w:pgSz w:w="{page[0]}" w:h="{page[1]}"/>'
            + '<w:pgMar w:top="%s" w:right="%s" w:bottom="%s" w:left="%s" w:header="708" w:footer="708" w:gutter="0"/>'
            % margins
            + f'<w:cols w:num="{columns}" w:space="708"/>'
            + '<w:docGrid w:type="lines" w:linePitch="312"/>'
            + "</w:sectPr></w:body></w:document>")


def write_docx(path: Path, document: str, styles: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", RELS)
        package.writestr("word/_rels/document.xml.rels", DOC_RELS)
        package.writestr("word/document.xml", document)
        package.writestr("word/styles.xml", styles)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic template/manuscript fixture")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    template_styles = styles_xml([
        style("Normal", "Normal", default=True, size="21", before="0", after="120",
              based_on=None),
        style("Title", "Title", size="32", bold=True, align="center", before="0", after="240"),
        style("Heading1", "heading 1", outline=0, size="28", bold=True, before="240", after="120"),
        style("Heading2", "heading 2", outline=1, size="24", bold=True, before="200", after="100"),
        style("BodyText", "Body Text", size="21", align="both", before="0", after="120", line="360"),
        style("FigureCaption", "Caption", size="18", align="center", before="60", after="180"),
        style("Bibliography", "Bibliography", size="18", before="0", after="60"),
        '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
        '<w:tblPr><w:tblBorders>'
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        "</w:tblBorders></w:tblPr></w:style>",
    ], doc_default_font="Liberation Serif", doc_default_size="21")
    template_table = ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
                      '<w:tblW w:w="9000" w:type="dxa"/></w:tblPr>'
                      '<w:tblGrid><w:gridCol w:w="4500"/><w:gridCol w:w="4500"/></w:tblGrid>'
                      + header_row(["Template column", "Value"]) + "</w:tbl>")
    template_doc = document_xml(
        paragraph("Journal of Synthetic Studies (template)", "Title")
        + paragraph("此模板仅用于接口自测。", "BodyText")
        + paragraph("Table 1. Template table styling example.", "FigureCaption")
        + template_table,
        page=("11906", "16838"), margins=("1417", "1417", "1417", "1417"), columns=1)
    write_docx(out / "template.docx", template_doc, template_styles)

    source_styles = styles_xml([
        style("Normal", "Normal", default=True, size="24", after="120"),
        style("MyTitle", "My Title", size="36", bold=True, align="center"),
        style("MyHead1", "My Head 1", size="30", bold=True),
        style("MyHead2", "My Head 2", size="26", bold=True),
        style("MyBody", "My Body", size="24"),
        style("MyCaption", "My Caption", size="20", align="center"),
        style("MyRefs", "My References", size="20"),
    ], doc_default_font="Times New Roman", doc_default_size="24")
    table = ("<w:tbl><w:tblPr><w:tblW w:w=\"9000\" w:type=\"dxa\"/></w:tblPr>"
             + header_row(["Specimen", "Strength (MPa)"]) + header_row(["A", "31.2"])
             + "</w:tbl>")
    source_doc = document_xml(
        paragraph("Strengthening of synthetic specimens", "MyTitle")
        + paragraph("Method", "MyHead1")
        + paragraph("Specimens were printed and then filled. Strength was measured at 25 degC.",
                    "MyBody")
        + paragraph("Results", "MyHead1")
        + paragraph("Filled specimens reached 31.2 MPa in the synthetic fixture.", "MyBody")
        + paragraph("Table 1. Synthetic strength summary.", "MyCaption")
        + table
        + paragraph("Discussion", "MyHead1")
        + paragraph("The synthetic number is a fixture value, not a reported measurement.", "MyBody")
        + paragraph("References", "MyHead1")
        + paragraph("Fixture reference entry, synthetic, no DOI.", "MyRefs"),
        page=("12240", "15840"), margins=("1440", "1440", "1440", "1440"), columns=1)
    write_docx(out / "manuscript.docx", source_doc, source_styles)

    print(f"synthetic fixture written to {out}: template.docx, manuscript.docx")
    print("This fixture is not a formal case and is not an official answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
