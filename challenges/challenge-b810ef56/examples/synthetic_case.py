"""Synthetic manuscript + source pack for the evidence-ledger self-test.

The manuscript contains, on purpose: a supported claim, a causal claim whose source only
reports an association, a consensus claim resting on a single small study, an absolute claim
whose source is hedged, a claim with no matching supplied passage, a citation with no
reference entry, an unused reference, and a duplicate DOI entry. All text is invented.
"""

from __future__ import annotations

import argparse
import json
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
<w:docDefaults><w:rPrDefault><w:rPr><w:sz w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr/></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:outlineLvl w:val="0"/></w:pPr></w:style>
</w:styles>"""

SENTENCES = [
    ("Heading1", "Results"),
    ("Normal", "Filled specimens reached 31.2 MPa while unfilled specimens reached 24.0 MPa, "
               "which is a difference of 7.2 MPa in this synthetic fixture [1]."),
    ("Normal", "Resin filling causes the increase in load bearing capacity, because the resin "
               "carries part of the applied load [2]."),
    ("Normal", "It is well known that fill compositing improves mechanical performance in "
               "additive manufacturing [3]."),
    ("Normal", "The procedure proves that printing temperature determines every strength "
               "difference observed here [1]."),
    ("Normal", "The filler content reached 42 % in the synthetic batch described by the "
               "phantom source [9]."),
    ("Heading1", "References"),
    ("Normal", "[1] Fixture A, Example B. A synthetic study of filled specimens. Journal of "
               "Synthetic Studies. 2020. doi:10.1000/synthetic.0001"),
    ("Normal", "[2] Fixture C. A synthetic association between resin filling and load bearing. "
               "Synthetic Reports. 2021. doi:10.1000/synthetic.0002"),
    ("Normal", "[3] Fixture D. A synthetic single-case report of fill compositing. Synthetic "
               "Case Notes. 2019. doi:10.1000/synthetic.0003"),
    ("Normal", "[4] Fixture E. A synthetic review that is never cited. Synthetic Reviews. 2018. "
               "doi:10.1000/synthetic.0004"),
    ("Normal", "[5] Fixture F. A duplicate listing of the association report. Synthetic "
               "Reports. 2021. doi:10.1000/synthetic.0002"),
]


def para(text: str, style: str) -> str:
    return (f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    body = "".join(para(text, style) for style, text in SENTENCES)
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{W}"><w:body>{body}'
                '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>')
    manuscript = out / "manuscript.docx"
    with zipfile.ZipFile(manuscript, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", RELS)
        package.writestr("word/_rels/document.xml.rels", DOC_RELS)
        package.writestr("word/document.xml", document)
        package.writestr("word/styles.xml", STYLES)

    sources = out / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    pack = {
        "paper-01": [
            "Filled specimens reached 31.2 MPa while unfilled specimens reached 24.0 MPa, a "
            "difference of 7.2 MPa measured in a single synthetic batch.",
            "Filler content in the measured batch was 42 % by mass.",
        ],
        "paper-02": [
            "Resin filling was associated with an increase in load bearing capacity in this "
            "synthetic sample; the design cannot establish that the filling causes the increase.",
        ],
        "paper-03": [
            "This single-case report describes one printed specimen, so the observation is "
            "preliminary and cannot support a general claim about mechanical performance.",
        ],
        "paper-04": [
            "Printing temperature varied across the synthetic runs, but the study cannot exclude "
            "other contributions to the measured strength differences.",
        ],
    }
    for name, passages in pack.items():
        (sources / f"{name}.json").write_text(
            json.dumps({"title": name, "passages": passages}, ensure_ascii=False, indent=2),
            encoding="utf-8")

    print(f"synthetic fixture written to {out}: manuscript.docx + sources/")
    print("Fixture only: no formal case, no official answer, no real measurement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
