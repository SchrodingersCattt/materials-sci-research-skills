"""Synthetic template deck + merge plan for the slide-editor self-test.

The deck is built the way a real organizer template is: a master, one title-and-content layout
and two slides whose slides carry no direct formatting of their own. The plan then edits one
slide and adds one from the layout, so both code paths are exercised.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"

CONTENT_TYPES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CT}">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
<Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
</Types>"""

ROOT_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""

PRESENTATION = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
<p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId3"/></p:sldIdLst>
<p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>
<p:notesSz cx="6858000" cy="9144000"/></p:presentation>"""

PRESENTATION_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rId2" Type="{R}/slide" Target="slides/slide1.xml"/>
<Relationship Id="rId3" Type="{R}/slide" Target="slides/slide2.xml"/>
<Relationship Id="rId4" Type="{R}/theme" Target="theme/theme1.xml"/>
</Relationships>"""

THEME = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{A}" name="Synthetic Thesis Theme">
<a:themeElements>
<a:clrScheme name="Synthetic">
{"".join(f'<a:{slot}><a:srgbClr val="{colour}"/></a:{slot}>' for slot, colour in (
    ("dk1", "1A1A1A"), ("lt1", "FFFFFF"), ("dk2", "333F50"), ("lt2", "E8E8E8"),
    ("accent1", "0F4C81"), ("accent2", "B7472A"), ("accent3", "6B8E23"),
    ("accent4", "7B5EA7"), ("accent5", "2E7D8F"), ("accent6", "C88A2B"),
    ("hlink", "0F4C81"), ("folHlink", "7B5EA7")))}
</a:clrScheme>
<a:fontScheme name="Synthetic"><a:majorFont><a:latin typeface="Synthetic Sans"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="Synthetic Serif"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>
<a:fmtScheme name="Synthetic">
<a:fillStyleLst><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:fillStyleLst>
<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:bgFillStyleLst>
</a:fmtScheme></a:themeElements></a:theme>"""

MASTER = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title Placeholder"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="838200" y="365125"/><a:ext cx="10515600" cy="1325563"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="3200" b="1"/><a:t>Master title</a:t></a:r></a:p></p:txBody></p:sp>
<p:sp><p:nvSpPr><p:cNvPr id="3" name="Body Placeholder"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="838200" y="1825625"/><a:ext cx="10515600" cy="4351338"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1800"/><a:t>Master body</a:t></a:r></a:p></p:txBody></p:sp>
</p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>"""

MASTER_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="{R}/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

LAYOUT = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}" type="titleAndContent">
<p:cSld name="Synthetic Title and Content"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="838200" y="365125"/><a:ext cx="10515600" cy="1325563"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="3200" b="1"/><a:t>Click to add title</a:t></a:r></a:p></p:txBody></p:sp>
<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="838200" y="1825625"/><a:ext cx="10515600" cy="4351338"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr lvl="0"><a:buChar char="&#8226;"/></a:pPr><a:r><a:rPr lang="en-US" sz="1800"/><a:t>Click to add text</a:t></a:r></a:p></p:txBody></p:sp>
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"""

LAYOUT_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def slide(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="838200" y="365125"/><a:ext cx="10515600" cy="1325563"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="3200" b="1"/><a:t>{title}</a:t></a:r></a:p></p:txBody></p:sp>
<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="838200" y="1825625"/><a:ext cx="10515600" cy="4351338"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr lvl="0"><a:buChar char="&#8226;"/></a:pPr><a:r><a:rPr lang="en-US" sz="1800"/><a:t>{body}</a:t></a:r></a:p></p:txBody></p:sp>
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""


def slide_rels() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PKG_REL}">
<Relationship Id="rId1" Type="{R}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    deck = out / "template-deck.pptx"
    with zipfile.ZipFile(deck, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES)
        package.writestr("_rels/.rels", ROOT_RELS)
        package.writestr("ppt/presentation.xml", PRESENTATION)
        package.writestr("ppt/_rels/presentation.xml.rels", PRESENTATION_RELS)
        package.writestr("ppt/theme/theme1.xml", THEME)
        package.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
        package.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", MASTER_RELS)
        package.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
        package.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", LAYOUT_RELS)
        package.writestr("ppt/slides/slide1.xml", slide("Template slide one", "Template body one"))
        package.writestr("ppt/slides/_rels/slide1.xml.rels", slide_rels())
        package.writestr("ppt/slides/slide2.xml", slide("Template slide two", "Template body two"))
        package.writestr("ppt/slides/_rels/slide2.xml.rels", slide_rels())

    plan = {
        "schema": "deck-merge-plan/v1",
        "slides": [
            {"id": "edit-1", "target_slide": 1,
             "title": {"text": "Results overview", "source_locator": "manuscript p12"},
             "body": {"lines": ["Filled group reached 31.2 MPa",
                                "Unfilled group reached 24.0 MPa",
                                "Difference of 7.2 MPa in the fixture"],
                      "source_locator": "data.csv rows A, B"}},
            {"id": "add-1", "layout": "Synthetic Title and Content",
             "title": {"text": "Limitations", "source_locator": "manuscript p16"},
             "body": {"lines": ["No uncertainty is reported in the fixture",
                                "No significance test is reported"],
                      "source_locator": "manuscript p16"}},
        ],
    }
    (out / "merge-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    print(f"synthetic deck fixture written to {out}: template-deck.pptx + merge-plan.json")
    print("Fixture only: no formal case, no official answer, no real result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
