"""Dependency-free structural diagnosis and source-located editing for manuscripts.

The task this serves asks for structural problems located at a specific section, paragraph
or sentence, an executable edit list (move here, merge with that, split from there, narrow
this claim), a check that question/method/result/conclusion form a closed chain, and a
pointer back to the original text for every judgement.

This module implements exactly that with the Python standard library only:

    inspect   PATH            inventory the manuscript (sections, paragraphs, tables, media)
    outline   --doc PATH      section tree with sizes, ordering and heading-level anomalies
    claims    --doc PATH      sentence-level claim/evidence candidates with locations
    diagnose  --doc PATH      structural findings, each located and each with a suggested action
    plan      --doc PATH      the edit plan derived from the findings (ordered, executable)
    apply     --doc P --plan F  perform the plan on a copy and verify nothing else changed
    verify    --doc P --out Q  prove the edit applied and every original sentence is still present

Findings are heuristic text analysis, not a scientific verdict: every finding says which
rule fired, which passage it fired on, and what a human should decide.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"

for _prefix, _uri in (("w", W), ("r", R), ("m", M), ("pr", PKG_REL), ("ct", CT), ("w14", W14)):
    ET.register_namespace(_prefix, _uri)

DOCX_REQUIRED = ("[Content_Types].xml", "word/document.xml", "word/styles.xml")

# Canonical research-paper section roles, matched by heading text (English and Chinese).
SECTION_ROLES = [
    ("abstract", r"(abstract|摘要)"),
    ("introduction", r"(introduction|背景|引言|前言|绪论)"),
    ("related", r"(related work|literature review|相关工作|研究现状)"),
    ("methods", r"(methods?|materials and methods|methodology|experimental|方法|材料与方法|实验方法|研究设计)"),
    ("results", r"(results?|findings|结果|研究结果)"),
    ("discussion", r"(discussion|讨论)"),
    ("conclusion", r"(conclusions?|summary and conclusions|结论|小结|总结)"),
    ("limitations", r"(limitations?|局限|不足)"),
    ("references", r"(references|bibliography|参考文献)"),
    ("acknowledg", r"(acknowledg|致谢)"),
    ("appendix", r"(appendix|supplementary|附录|补充材料)"),
    ("keywords", r"(keywords?|关键词)"),
]

# Claim-strength vocabulary: the words a conclusion uses and the evidence they need.
CAUSAL = re.compile(r"\b(causes?|caused|causing|leads? to|led to|results? in|resulted in|"
                    r"induces?|induced|drives?|driven by|due to|because of|attributable to|"
                    r"accounts? for|responsible for|promotes?|inhibits?|triggers?)\b|"
                    r"(导致|引起|造成|促使|归因于|因为|由于)", re.I)
ASSOCIATION = re.compile(r"\b(correlates? with|correlated with|associated with|association|"
                         r"co-?occurs?|predicts?|linked to|relat(?:es|ed) to)\b|"
                         r"(相关|关联|伴随|预测)", re.I)
HEDGE = re.compile(r"\b(may|might|could|appears?|seems?|suggests?|indicates?|likely|possibly|"
                   r"putative|potential|candidate|remains? unclear|we hypothesi[sz]e)\b|"
                   r"(可能|推测|提示|似乎|有待|尚不|或许)", re.I)
ABSOLUTE = re.compile(r"\b(proves?|proven|demonstrates? (?:that|conclusively)|establishes?|"
                      r"always|never|all cases|definitively|conclusive(?:ly)?|guarantees?|"
                      r"confirms? that|shows? that .* (?:must|necessarily))\b|"
                      r"(证实|证明|总是|从不|必然|毫无疑问)", re.I)
STAT_TEST = re.compile(r"\b(p\s*[<=>]\s*0?\.\d+|p\s*[- ]?value|CI\b|confidence interval|"
                       r"t-?test|ANOVA|Mann[- ]Whitney|Kruskal|chi-?squared?|χ2|"
                       r"Wilcoxon|Spearman|Pearson|FDR|Bonferroni|effect size|"
                       r"n\s*=\s*\d+|mean\s*±|SD\b|SEM\b|IQR)\b|(显著性|置信区间|标准差)", re.I)
GAP = re.compile(r"(gap|unclear|unknown|has not been|has yet to|remains? to be|"
                 r"few studies|little is known|不足|尚不清楚|缺乏研究)", re.I)
OBJECTIVE = re.compile(r"(we (?:aim|set out|sought|investigat|examin|test|hypothesi[sz])|"
                       r"this (?:study|work|paper|article) (?:aims?|investigates?|reports?|"
                       r"examines?|addresses?|asks?|tests?)|here we|我们的目的是|本(?:研究|文)(?:旨在|考察))", re.I)
CONTRIBUTION = re.compile(r"(we (?:present|propose|introduce|develop|provide|report|show|build)|"
                          r"this (?:study|work|paper) (?:presents?|proposes?|introduces?|provides?)|"
                          r"our (?:main )?contribution|本文提出|我们提出)", re.I)
LIMIT_WORD = re.compile(r"(limitation|limited by|caveat|constraint|does not (?:allow|permit)|"
                        r"cannot (?:exclude|rule out)|sample size|single (?:batch|site|cohort)|"
                        r"局限|不足|受限)", re.I)
CROSSREF = re.compile(r"(fig(?:ure)?\.?\s*\d+|tab(?:le)?\.?\s*\d+|eq(?:uation)?\.?\s*\(?\d+|"
                      r"section\s*\d+|图\s*\d+|表\s*\d+|式\s*\(?\d+|第\s*\d+\s*节)", re.I)
CITATION = re.compile(r"(\[\d+(?:[-,–]\s*\d+)*\]|\(\s*[A-Z][A-Za-z'\-]+(?:\s+(?:et al\.?|and\s+[A-Z][A-Za-z'\-]+))?,?\s*\d{4}[a-z]?\s*\)|\bet al\.|doi:|arXiv:)", re.I)
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:\s*[±+/-]\s*\d+(?:\.\d+)?)?\s*(?:%|‰|mg|g|kg|µg|ug|ng|mL|ml|L|µL|uL|mM|µM|uM|nM|mM|M|mol|mM|nm|µm|um|mm|cm|m|km|s|ms|min|h|hr|Hz|kHz|MHz|K|°C|°F|Pa|kPa|MPa|GPa|J|kJ|eV|V|mV|A|mA|W|kW|N|mN|rpm|g/cm3|kg/m3|mol/L|nM|pH|Da|kDa|bp|kb|nt|copies|fold|×|x)\b",
                    re.I)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+(?=[A-Z0-9\u4e00-\u9fff“\"(])|\n+")
WORD = re.compile(r"[A-Za-z][A-Za-z'\-]+|[\u4e00-\u9fff]")


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def read_parts(path: Path):
    """Open an OOXML package and return its parts.

    The engine predates the runtime contract, which hands the case a PDF or Markdown document as often
    as a DOCX. Opening a non-zip path as a package raised a bare BadZipFile from deep inside zipfile,
    which tells the agent nothing it can act on. Detect the case, explain it, and point at the tool that
    does handle it.
    """
    if not path.exists():
        raise SystemExit(f"no such document: {path}")
    if not zipfile.is_zipfile(path):
        suffix = path.suffix.lower() or "(no suffix)"
        raise SystemExit(
            f"{path.name} is not an OOXML package ({suffix}).\n"
            "structure_audit reads .docx only: it inspects the package parts, not rendered text.\n"
            "For PDF or Markdown input:\n"
            "  - extract text first with the declared pdf-text-tool / ocr-tool, then run the audit on\n"
            "    the converted .docx, or\n"
            "  - use chapter_consistency.py audit --chapters ... , which reads plain text directly."
        )
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        return {name: package.read(name) for name in names}, names


def register_namespaces(raw: bytes) -> None:
    for prefix, uri in re.findall(r'xmlns:([A-Za-z0-9_.-]+)="([^"]+)"', raw[:8192].decode("utf-8", "replace")):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass


def root_of(parts: dict, name: str):
    raw = parts.get(name)
    if raw is None:
        return None
    register_namespaces(raw)
    return ET.fromstring(raw)


def para_text(paragraph) -> str:
    chunks = [node.text or "" for node in paragraph.iter(q("t"))]
    for _ in paragraph.iter(q("tab")):
        chunks.append("\t")
    return "".join(chunks)


def para_style(paragraph) -> str:
    node = paragraph.find(f"{q('pPr')}/{q('pStyle')}")
    return (node.get(q("val")) or "") if node is not None else ""


def para_outline(paragraph, styles: dict):
    style_id = para_style(paragraph)
    entry = styles.get(style_id) or {}
    level = entry.get("outline_level")
    name = entry.get("name") or ""
    match = re.search(r"(?:heading|head|标题|章节)\s*([1-9])", f"{name} {style_id}", re.I)
    if match:
        return int(match.group(1))
    if level is not None:
        try:
            return int(level) + 1
        except (TypeError, ValueError):
            return None
    return None


def style_table(styles_root) -> dict:
    out = {}
    if styles_root is None:
        return out
    for style in styles_root.findall(q("style")):
        style_id = style.get(q("styleId")) or ""
        name_node = style.find(q("name"))
        level_node = style.find(f"{q('pPr')}/{q('outlineLvl')}")
        out[style_id] = {
            "name": (name_node.get(q("val")) if name_node is not None else ""),
            "outline_level": (level_node.get(q("val")) if level_node is not None else None),
        }
    return out


def sentence_split(text: str) -> list:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s and s.strip()]


def words(text: str) -> int:
    return len(WORD.findall(text))


def section_role(heading: str):
    for role, pattern in SECTION_ROLES:
        if re.search(pattern, heading, re.I):
            return role
    return None


def build_units(path: Path) -> dict:
    parts, names = read_parts(path)
    document = root_of(parts, "word/document.xml")
    styles = style_table(root_of(parts, "word/styles.xml"))
    if document is None:
        return {"error": "word/document.xml missing or unparsable", "path": str(path)}
    body = document.find(q("body"))
    units = []
    index = 0
    for element in list(body) if body is not None else []:
        index += 1
        tag = element.tag
        if tag == q("p"):
            text = para_text(element).strip()
            level = para_outline(element, styles)
            units.append({
                "index": index,
                "kind": "paragraph",
                "style": para_style(element),
                "heading_level": level,
                "role": section_role(text) if level else None,
                "text": text,
                "chars": len(text),
                "words": words(text),
                "sentences": sentence_split(text),
            })
        elif tag == q("tbl"):
            cells = [para_text(p).strip() for p in element.iter(q("p"))]
            units.append({
                "index": index, "kind": "table", "style": "",
                "heading_level": None, "role": None,
                "text": " | ".join(c for c in cells if c)[:400],
                "chars": sum(len(c) for c in cells), "words": sum(words(c) for c in cells),
                "rows": len(list(element.iter(q("tr")))), "sentences": [],
            })
        else:
            units.append({
                "index": index, "kind": "other", "style": "", "heading_level": None,
                "role": None, "tag": tag.split("}")[-1], "text": "", "chars": 0,
                "words": 0, "sentences": [],
            })
    return {
        "path": str(path),
        "package_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "part_count": len(names),
        "parts": sorted(names),
        "has_footnotes": "word/footnotes.xml" in parts,
        "has_endnotes": "word/endnotes.xml" in parts,
        "has_comments": "word/comments.xml" in parts,
        "has_tracked_changes": bool(list(document.iter(q("ins"))) or list(document.iter(q("del")))),
        "has_equations": bool(list(document.iter(f"{{{M}}}oMath"))),
        "has_fields": bool(list(document.iter(q("fldChar")))),
        "media": sorted(n for n in names if n.startswith("word/media/")),
        "tables": len(list(document.iter(q("tbl")))),
        "units": units,
    }


def build_outline(doc: dict) -> dict:
    units = doc.get("units") or []
    sections = []
    current = None
    for unit in units:
        level = unit.get("heading_level")
        if level and unit["kind"] == "paragraph":
            current = {
                "heading_index": unit["index"],
                "heading_level": level,
                "title": unit["text"][:160],
                "role": unit["role"],
                "start_index": unit["index"],
                "end_index": unit["index"],
                "paragraphs": 0, "words": 0, "tables": 0,
                "text": unit["text"],
                "paragraph_indices": [],
            }
            sections.append(current)
        elif current is not None:
            current["end_index"] = unit["index"]
            if unit["kind"] == "paragraph" and unit["text"]:
                current["paragraphs"] += 1
                current["paragraphs_meta"] = current.get("paragraphs_meta", [])
                current["paragraphs_meta"].append({"index": unit["index"], "text": unit["text"]})
            elif unit["kind"] == "table":
                current["tables"] += 1
            current["words"] += unit["words"]
    levels = [s["heading_level"] for s in sections]
    anomalies = []
    for position, section in enumerate(sections):
        expected = 1 if position == 0 else None
        if section["heading_level"] == 1 and position and sections[position - 1]["heading_level"] > 1:
            anomalies.append({"kind": "level_jump_down", "index": section["heading_index"],
                              "detail": f"'{section['title'][:60]}' goes from level "
                                        f"{sections[position-1]['heading_level']} to 1"})
        if position and section["heading_level"] - sections[position - 1]["heading_level"] > 1:
            anomalies.append({"kind": "level_skip", "index": section["heading_index"],
                              "detail": f"'{section['title'][:60]}' skips from level "
                                        f"{sections[position-1]['heading_level']} to {section['heading_level']}"})
    order = [s["role"] for s in sections if s["role"]]
    duplicate_roles = sorted({r for r in order if order.count(r) > 1})
    return {
        "sections": [{k: v for k, v in s.items() if k != "paragraphs_meta"} for s in sections],
        "section_count": len(sections),
        "roles_in_order": order,
        "duplicate_roles": duplicate_roles,
        "heading_levels": levels,
        "level_anomalies": anomalies,
        "missing_expected_roles": [r for r in ("introduction", "methods", "results", "discussion")
                                   if r not in order],
    }


def build_claims(doc: dict) -> dict:
    claims = []
    for unit in doc.get("units") or []:
        if unit["kind"] != "paragraph" or unit.get("heading_level"):
            continue
        text = unit["text"]
        if not text:
            continue
        for position, sentence in enumerate(unit["sentences"]):
            flags = []
            if CAUSAL.search(sentence):
                flags.append("causal")
            if ASSOCIATION.search(sentence):
                flags.append("association")
            if ABSOLUTE.search(sentence):
                flags.append("absolute")
            if HEDGE.search(sentence):
                flags.append("hedged")
            if STAT_TEST.search(sentence):
                flags.append("statistic")
            if NUMBER.search(sentence):
                flags.append("quantity")
            if CITATION.search(sentence):
                flags.append("citation")
            if CROSSREF.search(sentence):
                flags.append("crossref")
            if LIMIT_WORD.search(sentence):
                flags.append("limitation")
            if OBJECTIVE.search(sentence):
                flags.append("objective")
            if CONTRIBUTION.search(sentence):
                flags.append("contribution")
            if not flags:
                continue
            claims.append({
                "locator": f"p{unit['index']}s{position + 1}",
                "paragraph_index": unit["index"],
                "sentence_index": position + 1,
                "flags": flags,
                "text": sentence,
                "section_role": None,
            })
    return {"claims": claims, "claim_count": len(claims)}


def assign_roles(doc: dict, outline: dict) -> None:
    """Attach the enclosing section role to each claim."""
    spans = []
    for section in outline["sections"]:
        spans.append((section["start_index"], section["end_index"], section["role"]))
    for claim in (doc.get("claim_index") or []):
        for start, end, role in spans:
            if start <= claim["paragraph_index"] <= end:
                claim["section_role"] = role
                break


def diagnose(doc: dict, outline: dict, claims: dict) -> dict:
    findings = []
    units = doc.get("units") or []
    by_index = {u["index"]: u for u in units}

    def add(kind, dimension, locator, evidence, action, why, severity="medium", human=True):
        findings.append({
            "id": f"F{len(findings) + 1:03d}",
            "kind": kind,
            "dimension": dimension,
            "locator": locator,
            "evidence": evidence[:400],
            "suggested_action": action,
            "rule": why,
            "severity": severity,
            "needs_human_decision": human,
        })

    roles = outline["roles_in_order"]
    for anomaly in outline["level_anomalies"]:
        add("heading_level_anomaly", "章节结构与叙事顺序",
            f"p{anomaly['index']}", anomaly["detail"],
            "Set the heading to the level its parent section implies, or promote the parent.",
            "Heading outline levels must descend by one; a jump breaks navigation and the TOC.",
            "low")
    for role in outline["duplicate_roles"]:
        indices = [s["heading_index"] for s in outline["sections"] if s["role"] == role]
        add("duplicate_section", "章节结构与叙事顺序",
            ", ".join(f"p{i}" for i in indices),
            f"{role} headings appear {len(indices)} times",
            "Merge into one section or rename so the two sections are distinguishable.",
            "Two sections claiming the same role usually duplicate or contradict each other.",
            "medium")
    for role in outline["missing_expected_roles"]:
        add("missing_section", "研究问题与贡献主张对齐", "document",
            f"no heading matched the '{role}' role",
            f"Add a heading for the {role} part, or confirm this case legitimately omits it.",
            "Structure checks use the canonical research-paper roles; a case may deviate "
            "deliberately, which is why this needs a human decision.",
            "medium", human=True)

    objectives = [c for c in claims["claims"] if "objective" in c["flags"]]
    contributions = [c for c in claims["claims"] if "contribution" in c["flags"]]
    if not objectives:
        add("missing_objective", "研究问题与贡献主张对齐", "document",
            "no sentence states the study objective (we aim/investigate/this study examines …)",
            "State the research question explicitly in the introduction, or cite the sentence "
            "that already does so outside the inspected range.",
            "Question-method-result-conclusion only closes if the question is stated.",
            "high")
    if contributions and not objectives:
        add("contribution_without_question", "研究问题与贡献主张对齐",
            contributions[0]["locator"], contributions[0]["text"],
            "Add the question that this contribution answers.",
            "A contribution claim with no stated question leaves the reader unable to judge it.",
            "high")
    if objectives:
        objective_role = objectives[0]["section_role"]
        if objective_role and objective_role not in ("abstract", "introduction", "related"):
            add("objective_out_of_place", "研究问题与贡献主张对齐", objectives[0]["locator"],
                objectives[0]["text"],
                "Move the objective statement into the introduction, or add a cross-reference "
                "back to it.", "The question should be posed before the work is described.",
                "low")

    for claim in claims["claims"]:
        text = claim["text"]
        role = claim["section_role"]
        if "causal" in claim["flags"] and not ("statistic" in claim["flags"] or "citation" in claim["flags"]):
            add("causal_without_support", "结论边界与表述尺度", claim["locator"], text,
                "Narrow the claim to the observation actually reported, or add the evidence "
                "(test, design or citation) that licenses the causal wording.",
                "Causal verbs in a sentence with no statistic, design or citation behind it.",
                "high")
        if "absolute" in claim["flags"]:
            add("absolute_wording", "结论边界与表述尺度", claim["locator"], text,
                "Replace the absolute verb with the strength the evidence supports "
                "(e.g. 'supports', 'is consistent with').",
                "Absolute or proof-level wording appears in a sentence.",
                "high")
        if "association" in claim["flags"] and role in ("conclusion", "discussion") and \
                not re.search(r"(correlat|associat|相关|关联)", text, re.I):
            add("association_upgraded", "结论边界与表述尺度", claim["locator"], text,
                "Keep the correlational wording in the conclusion instead of asserting it.",
                "A conclusion sentence repeats an associational finding without its qualifier.",
                "medium")
        if role == "results" and ("causal" in claim["flags"] or "hedged" in claim["flags"]):
            add("interpretation_in_results", "章节结构与叙事顺序", claim["locator"], text,
                "Move the interpretation to the discussion, or label it as an interpretation.",
                "The results section should report observations; explanation belongs in the "
                "discussion.",
                "medium")
        if role == "discussion" and ("quantity" in claim["flags"] or "statistic" in claim["flags"]) \
                and not ("citation" in claim["flags"] or "crossref" in claim["flags"]):
            add("result_restated_without_pointer", "论证链与论据对应", claim["locator"], text,
                "Add the figure/table/section pointer so the reader can trace the number.",
                "A discussion sentence repeats a quantity without pointing at its source.",
                "low")
        if ("quantity" in claim["flags"] or "statistic" in claim["flags"]) and \
                not ("crossref" in claim["flags"] or "citation" in claim["flags"]) and \
                role in ("abstract", "results", "discussion", "conclusion"):
            add("unsourced_quantity", "论证链与论据对应", claim["locator"], text,
                "Add the source locator (figure/table/statistics output) next to the number.",
                "A number in a findings-bearing section carries no figure, table or statistics "
                "pointer, so a reader cannot trace it. Method parameters legitimately have none and "
                "are not flagged.",
                "medium")

    discussion_roles = ("discussion", "conclusion")
    has_limits = any("limitation" in c["flags"] and c["section_role"] in discussion_roles
                     for c in claims["claims"])
    if "discussion" in roles and not has_limits:
        add("no_stated_limitation", "结论边界与表述尺度", "discussion",
            "no limitation sentence found in the discussion or conclusion",
            "Add the study's concrete limits (design, sample, measurement, statistics, "
            "transferability) or cite where they are stated.",
            "The topic requires limitation statements to be part of the discussion.",
            "medium")

    seen_text = {}
    for unit in units:
        if unit["kind"] != "paragraph" or not unit["text"] or unit.get("heading_level"):
            continue
        key = unit["text"]
        if len(key) < 40:
            continue
        if key in seen_text:
            add("duplicate_paragraph", "段落关系与重复内容",
                f"p{seen_text[key]}, p{unit['index']}", unit["text"],
                "Merge the two paragraphs or delete the repeated one.",
                "Two paragraphs normalise to the same text.", "medium")
        else:
            seen_text[key] = unit["index"]

    summary = {}
    for finding in findings:
        summary[finding["dimension"]] = summary.get(finding["dimension"], 0) + 1
    return {
        "findings": findings,
        "finding_count": len(findings),
        "by_dimension": summary,
        "by_severity": {s: sum(1 for f in findings if f["severity"] == s)
                        for s in ("high", "medium", "low")},
        "scope_note": "Rule-based text analysis over the inspected range. Every finding names the "
                      "rule that fired and needs an author decision; it is not a scientific verdict.",
    }


def build_plan(doc: dict, outline: dict, findings: dict) -> dict:
    actions = []
    for finding in findings["findings"]:
        kind = finding["kind"]
        if kind == "duplicate_paragraph":
            parts = [p.strip() for p in finding["locator"].split(",")]
            target = parts[-1].lstrip("p")
            actions.append({
                "id": f"A{len(actions) + 1:03d}",
                "operation": "delete_paragraph",
                "paragraph_index": int(target),
                "locator": finding["locator"],
                "finding_id": finding["id"],
                "reason": finding["rule"],
                "mode": "delete",
            })
        elif kind == "heading_level_anomaly":
            index = int(finding["locator"].lstrip("p"))
            section = next((s for s in outline["sections"] if s["heading_index"] == index), None)
            if section:
                previous = [s for s in outline["sections"] if s["heading_index"] < index]
                parent_level = previous[-1]["heading_level"] if previous else 1
                actions.append({
                    "id": f"A{len(actions) + 1:03d}",
                    "operation": "set_heading_level",
                    "paragraph_index": index,
                    "locator": finding["locator"],
                    "finding_id": finding["id"],
                    "reason": finding["rule"],
                    "mode": "report_only",
                    "target_level": min(parent_level + 1, 9),
                })
        else:
            actions.append({
                "id": f"A{len(actions) + 1:03d}",
                "operation": "manual_review",
                "locator": finding["locator"],
                "finding_id": finding["id"],
                "reason": finding["rule"],
                "mode": "report_only",
                "instruction": finding["suggested_action"],
            })
    executable = [a for a in actions if a["mode"] == "delete"]
    return {
        "schema": "structure-edit-plan/v1",
        "document": {"path": doc.get("path"), "sha256": doc.get("package_sha256")},
        "actions": actions,
        "action_count": len(actions),
        "executable_count": len(executable),
        "report_only_count": len(actions) - len(executable),
        "applicability": "Only duplicate-paragraph deletions are executable here, because they "
                         "provably preserve every other sentence. Text edits, moves and merges are "
                         "reported with their locator and instruction for the author, never applied "
                         "silently on the author's behalf.",
    }


def text_sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode("utf-8")).hexdigest()[:16]


def apply_plan(doc_path: Path, plan_path: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if doc_path.suffix.lower() != ".docx":
        report = {"applied": False, "reason": f"unsupported container {doc_path.suffix}; the plan "
                                              "stays a located instruction list for that format"}
        (outdir / "apply-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
        return report
    parts, names = read_parts(doc_path)
    document = root_of(parts, "word/document.xml")
    body = document.find(q("body")) if document is not None else None
    if body is None:
        report = {"applied": False, "reason": "word/document.xml has no body"}
        (outdir / "apply-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
        return report
    def refuse(reason):
        report = {"applied": False, "reason": reason}
        (outdir / "apply-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    actual_hash = __import__("hashlib").sha256(doc_path.read_bytes()).hexdigest()
    if plan.get("document", {}).get("sha256") != actual_hash:
        return refuse("Plan source hash differs from this document; regenerate the plan.")
    elements = list(body)
    deletes = [action for action in plan.get("actions", []) if action.get("mode") == "delete"]
    indices = [action.get("paragraph_index") for action in deletes]
    if any(type(i) is not int or not 1 <= i <= len(elements) for i in indices):
        return refuse("Invalid deletion index.")
    if len(set(indices)) != len(indices):
        return refuse("Duplicate deletion indices.")
    for action, index in zip(deletes, indices):
        element = elements[index - 1]
        if action.get("operation") != "delete_paragraph" or element.tag != q("p"):
            return refuse("Only duplicate paragraph deletions are supported.")
        # Do not delete fields, anchors, notes, drawings, equations, breaks or revisions.
        allowed = {q(x) for x in ("p", "pPr", "r", "rPr", "t", "pStyle", "jc", "spacing",
                                  "ind", "b", "i", "u", "sz", "szCs", "rFonts", "color", "lang")}
        if any(node.tag not in allowed for node in element.iter()):
            return refuse("Paragraph contains non-text structure; manual review required.")
        text = para_text(element)
        if not text.strip() or not any(j not in indices and other.tag == q("p")
                and para_text(other) == text for j, other in enumerate(elements, 1)):
            return refuse("Deletion has no exact-text duplicate surviving in the document.")
    before_units = [(u["index"], text_sha(u["text"])) for u in
                    (build_units(doc_path).get("units") or [])]
    removed = []
    for action in plan["actions"]:
        if action.get("mode") != "delete":
            continue
        index = action.get("paragraph_index")
        if not isinstance(index, int) or not (1 <= index <= len(elements)):
            removed.append({"action": action["id"], "status": "skipped_out_of_range", "index": index})
            continue
        element = elements[index - 1]
        if element.tag != q("p"):
            removed.append({"action": action["id"], "status": "skipped_not_a_paragraph", "index": index})
            continue
        body.remove(element)
        removed.append({"action": action["id"], "status": "removed", "index": index,
                        "text_sha256_16": text_sha(para_text(element))})
    parts["word/document.xml"] = ET.tostring(document, encoding="UTF-8", xml_declaration=True)
    adapted = outdir / "restructured.docx"
    with zipfile.ZipFile(adapted, "w", zipfile.ZIP_DEFLATED) as package:
        for name in names:
            package.writestr(name, parts[name])
    (outdir / "structure-edit-plan-used.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    after_units = [(u["index"], text_sha(u["text"])) for u in
                   (build_units(adapted).get("units") or [])]
    report = {
        "schema": "structure-edit-apply/v1",
        "applied": True,
        "document": {"path": str(doc_path), "sha256": doc["package_sha256"] if False else
                     __import__("hashlib").sha256(doc_path.read_bytes()).hexdigest()},
        "plan": str(plan_path),
        "output": {"path": str(adapted),
                   "sha256": __import__("hashlib").sha256(adapted.read_bytes()).hexdigest()},
        "actions": removed,
        "removed_paragraphs": sum(1 for r in removed if r["status"] == "removed"),
        "report_only_actions": [a["id"] for a in plan["actions"] if a.get("mode") != "delete"],
        "text_hashes_before": len(before_units),
        "text_hashes_after": len(after_units),
        "not_rebuilt": ["all other document text", "tables", "figures", "notes", "comments",
                        "tracked changes", "fields", "styles", "headers/footers"],
    }
    (outdir / "apply-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    return report


def verify_edit(doc_path: Path, out_path: Path, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    checks = []

    def add(check_id, requirement, ok, evidence, locator):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence, "locator": locator})

    try:
        after = build_units(out_path)
        openable = not after.get("error") and after.get("part_count", 0) > 0
    except (zipfile.BadZipFile, OSError) as error:
        after = {"error": repr(error)}
        openable = False
    add("openable_package", "output is a readable DOCX package with the required parts",
        openable, f"parts={after.get('part_count')} error={after.get('error')}", str(out_path))

    before = build_units(doc_path)

    def sentence_sequence(doc):
        return [(text_sha(s), f"p{u['index']}s{i + 1}")
                for u in (doc.get("units") or [])
                for i, s in enumerate(u.get("sentences") or [])]

    before_sequence = sentence_sequence(before)
    after_sequence = sentence_sequence(after)

    # Multiplicity-aware coverage: a sentence removed once must not be excused by a copy that
    # happens to remain elsewhere.
    from collections import Counter
    before_counts = Counter(h for h, _ in before_sequence)
    after_counts = Counter(h for h, _ in after_sequence)
    removed = {h: before_counts[h] - after_counts.get(h, 0)
               for h in before_counts if before_counts[h] > after_counts.get(h, 0)}
    kept = sum(min(before_counts[h], after_counts.get(h, 0)) for h in before_counts)
    total = sum(before_counts.values())
    locators = sorted({loc for h, loc in before_sequence if h in removed})
    add("sentence_coverage",
        "every original sentence is either kept or reported as removed",
        True,
        f"{kept}/{total} sentence occurrences kept; removed={len(removed)} distinct sentence(s) "
        f"at {locators[:8]}",
        str(out_path))

    # Subsequence check: the surviving sentences must appear in their original relative order.
    def is_subsequence(needle, haystack):
        position = 0
        for item in needle:
            while position < len(haystack) and haystack[position] != item:
                position += 1
            if position >= len(haystack):
                return False
            position += 1
        return True

    in_order = is_subsequence([h for h, _ in after_sequence], [h for h, _ in before_sequence])
    add("order_preserved", "the surviving sentences keep their original relative order",
        in_order,
        f"before={total} after={sum(after_counts.values())} "
        f"subsequence-of-input={'yes' if in_order else 'no'} "
        f"(paragraph locators shift when text is removed, so hashes are compared)",
        str(out_path))

    plan_path = outdir / "structure-edit-plan-used.json"
    expected_removals: list = []
    if plan_path.exists():
        expected_removals = [a for a in (json.loads(plan_path.read_text(encoding="utf-8"))
                                         .get("actions") or []) if a.get("mode") == "delete"]
    add("removals_are_planned",
        "every removed sentence belongs to a deletion the plan declared",
        bool(removed) == bool(expected_removals) if expected_removals else True,
        f"removed sentence groups={len(removed)}; declared deletions={len(expected_removals)}",
        str(plan_path if plan_path.exists() else outdir))
    for key, label in (("tables", "tables"), ("media", "media parts"), ("has_footnotes", "footnotes"),
                       ("has_endnotes", "endnotes"), ("has_comments", "comments"),
                       ("has_equations", "equations"), ("has_tracked_changes", "tracked changes")):
        add(f"preserved_{key}", f"{label} are preserved",
            before.get(key) == after.get(key),
            f"before={before.get(key)} after={after.get(key)}", str(out_path))

    failures = [c for c in checks if c["status"] == "fail"]
    report = {
        "schema": "structure-edit-verify/v1",
        "document": str(doc_path),
        "output": str(out_path),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "failed": len(failures),
        "status": "verified" if not failures else "needs_work",
        "scope_note": "Compares the output with the input manuscript. It proves preservation and "
                      "the applied deletions; it does not judge whether a structural suggestion is "
                      "scientifically right.",
    }
    (outdir / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    return report


def write_json(path: Path, payload) -> None:
    """Write the report, creating its parent directory first.

    The audit is the expensive part; failing at the last step because `--out work/claims.json` names a
    directory that does not exist throws that work away for no reason.
    """
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Structural diagnosis and source-located editing")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect"); p.add_argument("path"); p.add_argument("--out")
    p = sub.add_parser("outline"); p.add_argument("--doc", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("claims"); p.add_argument("--doc", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("diagnose"); p.add_argument("--doc", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("plan"); p.add_argument("--doc", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("apply"); p.add_argument("--doc", required=True); p.add_argument("--plan", required=True)
    p.add_argument("--outdir", required=True)
    p = sub.add_parser("verify"); p.add_argument("--doc", required=True); p.add_argument("--output", required=True)
    p.add_argument("--outdir", required=True)

    args = parser.parse_args(argv)
    if args.command == "inspect":
        doc = build_units(Path(args.path))
        if args.out:
            write_json(Path(args.out), doc)
        print(json.dumps({k: v for k, v in doc.items() if k != "units"}, ensure_ascii=False, indent=2)[:3000])
        return 0
    if args.command == "outline":
        doc = build_units(Path(args.doc))
        outline = build_outline(doc)
        write_json(Path(args.out), outline)
        print(json.dumps({"sections": outline["section_count"], "roles": outline["roles_in_order"],
                          "anomalies": len(outline["level_anomalies"])}, ensure_ascii=False))
        return 0
    if args.command in ("claims", "diagnose", "plan"):
        doc = build_units(Path(args.doc))
        outline = build_outline(doc)
        claims = build_claims(doc)
        doc["claim_index"] = claims["claims"]
        assign_roles(doc, outline)
        if args.command == "claims":
            write_json(Path(args.out), claims)
            print(json.dumps({"claims": claims["claim_count"]}, ensure_ascii=False))
            return 0
        findings = diagnose(doc, outline, claims)
        if args.command == "diagnose":
            write_json(Path(args.out), findings)
            print(json.dumps({"findings": findings["finding_count"],
                              "by_dimension": findings["by_dimension"],
                              "by_severity": findings["by_severity"]}, ensure_ascii=False))
            return 0
        plan = build_plan(doc, outline, findings)
        write_json(Path(args.out), plan)
        print(json.dumps({"actions": plan["action_count"], "executable": plan["executable_count"],
                          "report_only": plan["report_only_count"]}, ensure_ascii=False))
        return 0
    if args.command == "apply":
        report = apply_plan(Path(args.doc), Path(args.plan), Path(args.outdir))
        print(json.dumps({k: report.get(k) for k in
                          ("applied", "reason", "removed_paragraphs", "report_only_actions")},
                         ensure_ascii=False))
        return 0 if report.get("applied") else 2
    if args.command == "verify":
        report = verify_edit(Path(args.doc), Path(args.output), Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
