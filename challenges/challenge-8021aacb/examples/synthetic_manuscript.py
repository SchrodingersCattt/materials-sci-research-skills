"""Synthetic manuscript fixture for the structural diagnosis self-test.

Invented text only: it exercises a heading level skip, a duplicated paragraph, a causal claim
with no statistic or citation, an absolute claim, an unsourced quantity, a results section
containing interpretation, and no stated limitation.
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

STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Liberation Serif" w:hAnsi="Liberation Serif"/><w:sz w:val="22"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr/></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/><w:pPr><w:spacing w:after="120"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="0"/><w:spacing w:before="240" w:after="120"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="1"/><w:spacing w:before="200" w:after="100"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
</w:styles>"""


def para(text: str, style: str = "Normal") -> str:
    return (f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')


def document(body: str) -> str:
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{W}"><w:body>{body}'
            '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417"/>'
            '<w:cols w:num="1" w:space="708"/></w:sectPr></w:body></w:document>')


DUPLICATE = ("Specimens were printed at 0.2 mm layer height and filled with resin before testing, "
             "and the same print settings were used for every group in this synthetic fixture.")

BODY = [
    para("Synthetic manuscript for structural self-testing", "Heading1"),
    para("Abstract", "Heading1"),
    para("This synthetic abstract states the fixture purpose only. It reports no measurement "
         "and cites nothing, because the fixture has no real data.", "Normal"),
    para("Introduction", "Heading1"),
    para("Additive manufacturing has grown quickly, and the strength of filled parts is often "
         "reported without the printing conditions attached to it.", "Normal"),
    para("Methods", "Heading2"),
    para(DUPLICATE, "Normal"),
    para("Strength was measured on a universal testing machine at a crosshead speed of 5 mm/min.", "Normal"),
    para("Results", "Heading1"),
    para(DUPLICATE, "Normal"),
    para("Filled specimens reached 31.2 MPa, which is larger than the unfilled group.", "Normal"),
    para("This increase causes the improvement in load bearing capacity, because the resin "
         "carries part of the load.", "Normal"),
    para("Discussion", "Heading1"),
    para("The measured strength is consistent with other reports of filled specimens, although "
         "the comparison is limited by the fixture.", "Normal"),
    para("These results prove that filling always improves strength.", "Normal"),
    para("The synthetic discussion reports 31.2 MPa again without a figure pointer.", "Normal"),
    para("References", "Heading1"),
    para("1. Synthetic fixture entry, no DOI.", "Normal"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "manuscript.docx"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", RELS)
        package.writestr("word/_rels/document.xml.rels", DOC_RELS)
        package.writestr("word/document.xml", document("".join(BODY)))
        package.writestr("word/styles.xml", STYLES)
    print(f"synthetic manuscript written to {path}")
    print("Fixture only: no formal case, no official answer, no measurement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
