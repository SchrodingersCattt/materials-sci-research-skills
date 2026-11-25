"""Candidate passage retrieval and mechanical citation audit. Lexical rules do not prove source identity, entailment or scientific truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

for _prefix, _uri in (("w", W), ("m", M)):
    ET.register_namespace(_prefix, _uri)

TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst", ".tex", ".json", ".csv", ".tsv", ".yaml", ".yml"}

# --- claim and evidence vocabulary ------------------------------------------------

CAUSAL = re.compile(r"\b(causes?|caused|causing|leads? to|led to|results? in|resulted in|induces?|"
                    r"induced|drives?|driven by|due to|because of|attributable to|accounts? for|"
                    r"responsible for|promotes?|inhibits?|triggers?|mediates?|regulates?)\b|"
                    r"(导致|引起|造成|促使|归因于|因为|由于|驱动)", re.I)
ASSOCIATION = re.compile(r"\b(correlates? with|correlated with|associated with|association|"
                         r"co-?occurs?|predicts?|linked to|relat(?:es|ed) to|enriched in)\b|"
                         r"(相关|关联|伴随|预测)", re.I)
CONSENSUS = re.compile(r"\b(established|well[- ]known|widely (?:accepted|reported|recognized)|"
                       r"consensus|generally (?:accepted|agreed)|it is known that|proven|"
                       r"universally|in general|typically)\b|(公认|众所周知|普遍认为|已经证明)", re.I)
HEDGE = re.compile(r"\b(may|might|could|appears?|seems?|suggests?|indicates?|likely|possibly|"
                   r"putative|potential|candidate|remains? unclear|we hypothesi[sz]e|"
                   r"is thought to|has been proposed)\b|(可能|推测|提示|似乎|有待|尚不|或许)", re.I)
ABSOLUTE = re.compile(r"\b(proves?|proven|conclusively|definitively|always|never|all cases|"
                      r"guarantees?|demonstrates? that|confirms? that|establishes? that|shows? that)\b|"
                      r"(证实|证明|总是|从不|必然|毫无疑问)", re.I)
STATISTIC = re.compile(r"\b(p\s*[<=>]\s*0?\.\d+|p\s*[- ]?value|CI\b|confidence interval|"
                       r"t-?test|ANOVA|Mann[- ]Whitney|Kruskal|chi-?squared?|χ2|Wilcoxon|"
                       r"Spearman|Pearson|FDR|Bonferroni|hazard ratio|odds ratio|effect size|"
                       r"n\s*=\s*\d+|cohort|randomi[sz]ed|placebo|double[- ]blind|"
                       r"meta[- ]analys|systematic review|case report|in vitro|in vivo)\b|"
                       r"(显著性|置信区间|随机对照|元分析|系统综述)", re.I)
QUANTITY = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:\s*[±+/-]\s*\d+(?:\.\d+)?)?\s*"
                      r"(?:%|‰|mg|kg|µg|ug|ng|mL|ml|L|µL|uL|mM|µM|uM|nM|mol|nm|µm|um|mm|cm|km|"
                      r"ms|min|h|hr|Hz|kHz|MHz|K|°C|°F|Pa|kPa|MPa|GPa|kJ|eV|mV|rpm|Da|kDa|bp|kb|"
                      r"fold|×|x)\b", re.I)
SCALE_WORDS = re.compile(r"\b(single|one|small|pilot|preliminary|n\s*=\s*[1-9]\b|case study|"
                         r"exploratory|feasibility)\b|(初步|小样本|单个|探索性)", re.I)
LIMIT_WORD = re.compile(r"(limitation|limited by|caveat|constraint|cannot (?:exclude|rule out)|"
                        r"does not (?:allow|permit|establish)|remains to be|conflicting|"
                        r"contradict|inconsistent|局限|不足|受限|存在冲突|不一致)", re.I)
CITATION = re.compile(r"(\[(?:\d+(?:\s*[-,–]\s*\d+)*)\](?:\s*[,;]?\s*\[\d+(?:\s*[-,–]\s*\d+)*\])*"
                      r"|\(\s*[A-Z][A-Za-z'\-]+(?:\s+(?:et al\.?|and\s+[A-Z][A-Za-z'\-]+))?,?\s*"
                      r"\d{4}[a-z]?(?:\s*[,;]\s*[A-Z][A-Za-z'\-]+(?:\s+et al\.?)?,?\s*\d{4}[a-z]?)*\s*\)"
                      r"|\bet al\.|\bdoi:\s*\S+|arXiv:\s*\S+|\bPMID:?\s*\d+)")
BRACKET_NUM = re.compile(r"\[(\d+(?:\s*[-,–]\s*\d+)*)\]")
YEAR = re.compile(r"\b(19|20)\d{2}[a-z]?\b")
DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+(?=[A-Z0-9\u4e00-\u9fff“\"(])|\n+")
WORD = re.compile(r"[A-Za-z][A-Za-z'\-]{2,}|[\u4e00-\u9fff]")
STOPWORDS = {"the", "and", "for", "with", "that", "this", "from", "were", "was", "are", "was",
             "has", "have", "had", "not", "but", "which", "these", "those", "than", "then",
             "into", "such", "also", "been", "they", "their", "there", "here", "when", "where",
             "while", "more", "most", "less", "least", "may", "might", "can", "could", "would",
             "should", "our", "its", "it", "we", "as", "at", "by", "in", "of", "on", "to", "is"}


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_docx_text(path: Path) -> list:
    """Paragraph list with 1-based indices, plus package facts."""
    if path.suffix.lower() in {".md",".markdown",".txt",".rst"}:
        text=path.read_text(encoding="utf-8")
        paragraphs=[{"index":i,"text":line.strip(),"style_id":""} for i,line in enumerate(text.splitlines(),1) if line.strip()]
        return paragraphs,{"parts":[],"package_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    import zipfile
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        raw = package.read("word/document.xml")
    for prefix, uri in re.findall(r'xmlns:([A-Za-z0-9_.-]+)="([^"]+)"',
                                 raw[:8192].decode("utf-8", "replace")):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass
    document = ET.fromstring(raw)
    paragraphs = []
    for index, paragraph in enumerate(document.iter(q("p")), start=1):
        text = "".join(node.text or "" for node in paragraph.iter(q("t")))
        style = paragraph.find(f"{q('pPr')}/{q('pStyle')}")
        paragraphs.append({
            "index": index,
            "text": text.strip(),
            "style_id": (style.get(q("val")) if style is not None else "") or "",
        })
    return paragraphs, {"parts": sorted(names), "package_sha256": sha(path.read_bytes().hex())}


def load_source(path: Path) -> dict:
    """Read one source file into passages with deterministic ids."""
    if path.suffix.lower() == ".docx":
        paragraphs, meta = read_docx_text(path)
        passages = [{"id": f"p{p['index']}", "text": p["text"]} for p in paragraphs if p["text"]]
        return {"path": str(path), "kind": "docx", "sha256": meta["package_sha256"],
                "passages": passages}
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            passages = []
            for key, value in payload.items():
                if isinstance(value, str) and len(value.strip()) > 20:
                    passages.append({"id": str(key), "text": value.strip()})
                elif isinstance(value, list):
                    for position, item in enumerate(value, start=1):
                        if isinstance(item, str) and len(item.strip()) > 20:
                            passages.append({"id": f"{key}[{position}]", "text": item.strip()})
                        elif isinstance(item, dict):
                            joined = " ".join(str(v) for v in item.values() if isinstance(v, (str, int, float)))
                            if len(joined.strip()) > 20:
                                passages.append({"id": f"{key}[{position}]", "text": joined.strip()})
            return {"path": str(path), "kind": "json", "sha256": sha(text), "passages": passages}
    paragraphs = []
    for index, block in enumerate(re.split(r"\n\s*\n", text), start=1):
        block = block.strip()
        if block:
            paragraphs.append({"id": f"p{index}", "text": block})
    return {"path": str(path), "kind": path.suffix.lstrip(".") or "text", "sha256": sha(text),
            "passages": paragraphs}


def collect_sources(root: Path) -> list:
    sources = []
    if root.is_file():
        candidates = [root]
    else:
        candidates = sorted(p for p in root.rglob("*")
                            if p.is_file() and (p.suffix.lower() in TEXT_SUFFIXES
                                                or p.suffix.lower() == ".docx"))
    for path in candidates:
        try:
            sources.append(load_source(path))
        except Exception as error:  # noqa: BLE001 - a failed read is evidence too
            sources.append({"path": str(path), "kind": "error", "error": repr(error),
                            "passages": []})
    return sources


def reference_entry(reference_text: str) -> dict:
    """Parse a reference-list entry into whatever metadata it actually contains."""
    doi = DOI.search(reference_text)
    year = YEAR.search(reference_text)
    title_guess = None
    parts = [p.strip() for p in re.split(r"[.\n]", reference_text) if len(p.strip()) > 12]
    if len(parts) >= 2:
        title_guess = parts[1]
    return {
        "text": reference_text.strip(),
        "doi": doi.group(0).rstrip(".") if doi else None,
        "year": year.group(0) if year else None,
        "title_guess": title_guess,
        "sha256_16": sha(reference_text.strip())[:16],
    }


def split_reference_list(paragraphs: list) -> dict:
    """Find the reference section and its numbered entries."""
    start = None
    for index, paragraph in enumerate(paragraphs):
        if re.match(r"^\s*(references|bibliography|参考文献|文献)\s*$", paragraph["text"], re.I) or \
           re.match(r"^\s*\d+(\.\d+)*\s*(references|bibliography|参考文献)\s*$",
                    paragraph["text"], re.I) or \
           re.match(r"^\s*(#{1,3}\s*)?(references|bibliography|参考文献)\s*$",
                    paragraph["text"], re.I):
            start = index + 1
            break
    if start is None:
        return {"found": False, "entries": [], "start_paragraph": None}
    entries = []
    for paragraph in paragraphs[start:]:
        text = paragraph["text"]
        if not text:
            continue
        if re.match(r"^\s*(appendix|supplementary|附录|补充材料)\b", text, re.I):
            break
        match = re.match(r"^\s*(?:\[(\d+)\]|(\d+)[.)])\s+(.*)$", text)
        if match:
            number = int(match.group(1) or match.group(2))
            entries.append({"number": number, "paragraph_index": paragraph["index"],
                            **reference_entry(match.group(3))})
        elif entries:
            entries[-1]["text"] += " " + text
    return {"found": True, "entries": entries, "start_paragraph": paragraphs[start - 1]["index"],
            "entry_count": len(entries)}


def sentence_split(text: str) -> list:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s and s.strip()]


NEGATED_CAUSAL = re.compile(r"(cannot (?:establish|show|demonstrate|prove|exclude|rule out)[^.;]*"
                            r"(?:caus|cause|determin)|does not (?:establish|show|demonstrate|prove)|"
                            r"no evidence (?:that|for)|not (?:establish|causal|a cause)|"
                            r"无法(?:证明|确定)|不能(?:证明|说明))", re.I)


def positive_causal(text: str) -> bool:
    """True when the text asserts causation rather than denying or limiting it."""
    stripped = NEGATED_CAUSAL.sub(" ", text)
    return bool(CAUSAL.search(stripped))


def keywords(text: str) -> set:
    tokens = {w.lower() for w in WORD.findall(text) if w.lower() not in STOPWORDS}
    numbers = {m.group(0) for m in re.finditer(r"\d+(?:\.\d+)?", text)}
    return tokens | numbers


def overlapping(passage: str, claim: str) -> float:
    claim_words = keywords(claim)
    if not claim_words:
        return 0.0
    passage_words = keywords(passage)
    return len(claim_words & passage_words) / len(claim_words)


def citation_numbers(text):
    numbers=set()
    for match in re.finditer(r"\[([0-9,\s\-–]+)\]",text):
        for token in match.group(1).split(","):
            parts=re.split(r"[-–]",token.strip())
            if len(parts)==1 and parts[0].isdigit(): numbers.add(int(parts[0]))
            elif len(parts)==2 and all(x.strip().isdigit() for x in parts):
                a,b=map(int,parts)
                if b<a or b-a>1000: raise ValueError("invalid citation range")
                numbers.update(range(a,b+1))
    return sorted(numbers)


def extract_claims(paragraphs: list) -> list:
    claims = []
    for paragraph in paragraphs:
        text = paragraph["text"]
        if not text or re.match(r"^\s*(#{1,6}\s|\d+(\.\d+)*\s+\S)", text) and len(text) < 80:
            continue
        if re.match(r"^\s*(references|bibliography|参考文献)\s*$", text, re.I):
            break
        for position, sentence in enumerate(sentence_split(text), start=1):
            if len(WORD.findall(sentence)) < 5:
                continue
            flags = []
            if CAUSAL.search(sentence):
                flags.append("causal")
            if ASSOCIATION.search(sentence):
                flags.append("association")
            if CONSENSUS.search(sentence):
                flags.append("consensus_claim")
            if ABSOLUTE.search(sentence):
                flags.append("absolute")
            if HEDGE.search(sentence):
                flags.append("hedged")
            if STATISTIC.search(sentence):
                flags.append("statistic")
            if QUANTITY.search(sentence):
                flags.append("quantity")
            if SCALE_WORDS.search(sentence):
                flags.append("small_scale")
            if LIMIT_WORD.search(sentence):
                flags.append("limitation")
            citations = CITATION.findall(sentence)
            if not flags and not citations:
                continue
            if not flags and citations and len(WORD.findall(sentence)) < 8:
                continue
            claims.append({
                "claim_id": f"C{len(claims) + 1:03d}",
                "locator": f"p{paragraph['index']}s{position}",
                "paragraph_index": paragraph["index"],
                "sentence_index": position,
                "text": sentence,
                "flags": flags,
                "citations": [c if isinstance(c, str) else c[0] for c in citations],
                "citation_numbers": citation_numbers(sentence),
                "keywords": sorted(keywords(sentence)),
            })
    return claims


def best_evidence(claim: dict, sources: list, threshold: float = 0.5) -> list:
    scored = []
    for source in sources:
        for passage in source.get("passages") or []:
            score = overlapping(passage["text"], claim["text"])
            if score >= 0.2:
                scored.append({
                    "source": source["path"],
                    "source_sha256": source.get("sha256"),
                    "passage_id": passage["id"],
                    "score": round(score, 3),
                    "excerpt": passage["text"][:600],
                    "excerpt_sha256_16": sha(passage["text"][:600])[:16],
                    "full_passage_sha256_16": sha(passage["text"])[:16],
                })
    scored.sort(key=lambda item: (-item["score"], item["source"], item["passage_id"]))
    return scored[:5]


def judge(claim: dict, evidence: list) -> dict:
    """Strength verdict for one claim against its best evidence, with the reason spelled out."""
    flags = set(claim["flags"])
    if not evidence:
        return {
            "verdict": "no_supplied_evidence",
            "strongest_score": 0.0,
            "reasons": ["no supplied passage shares enough content words with this sentence"],
            "rule": "evidence_linkage",
        }
    best = evidence[0]
    score = best["score"]
    passage = best["excerpt"]
    reasons = [f"best passage {best['source']}#{best['passage_id']} shares "
               f"{score:.0%} of the claim's content words"]
    verdict = "requires_semantic_review"

    passage_flags = set()
    if positive_causal(passage):
        passage_flags.add("causal")
    if ASSOCIATION.search(passage):
        passage_flags.add("association")
    if STATISTIC.search(passage):
        passage_flags.add("statistic")
    if HEDGE.search(passage):
        passage_flags.add("hedged")
    if SCALE_WORDS.search(passage):
        passage_flags.add("small_scale")
    if LIMIT_WORD.search(passage) or NEGATED_CAUSAL.search(passage):
        passage_flags.add("limitation")

    if "causal" in flags and "causal" not in passage_flags:
        verdict = "claim_stronger_than_source"
        reasons.append("the sentence asserts causation; the passage has neither causal wording "
                       "and a statistic alone does not license causation")
    elif "consensus_claim" in flags and "small_scale" in passage_flags:
        verdict = "claim_stronger_than_source"
        reasons.append("the sentence states a general/consensus result; the passage describes a "
                       "single, small or preliminary study")
    elif "absolute" in flags and ("hedged" in passage_flags or "limitation" in passage_flags):
        verdict = "claim_stronger_than_source"
        reasons.append("the sentence uses proof-level wording; the passage is hedged or names a "
                       "limitation instead")
    elif "causal" in flags and "association" in passage_flags and "causal" not in passage_flags:
        verdict = "claim_stronger_than_source"
        reasons.append("the passage reports an association; the sentence upgrades it to a cause")
    elif score < 0.5:
        verdict = "weakly_linked"
        reasons.append("content-word overlap is below 50%, so the link needs a human check")
    elif "hedged" in flags and not passage_flags:
        verdict = "requires_semantic_review"
        reasons.append("Different hedging is a review cue, not evidence to strengthen the claim.")

    if LIMIT_WORD.search(passage) and "limitation" not in flags:
        reasons.append("the passage itself names a limitation or conflict that the sentence "
                       "does not carry")
    if "statistic" in flags and "statistic" not in passage_flags:
        reasons.append("the sentence carries a statistic or design term the linked passage does "
                       "not contain; check the number against its own source")

    return {
        "verdict": verdict,
        "strongest_score": score,
        "strongest_evidence": best,
        "reasons": reasons,
        "rule": "content_overlap + strength_alignment",
        "passage_flags": sorted(passage_flags),
    }


def narrow_suggestion(claim: dict, judgement: dict) -> str:
    """A concrete rewrite direction for a claim the evidence cannot carry."""
    text = claim["text"]
    if judgement["verdict"] == "no_supplied_evidence":
        return ("Cite the source that actually contains this result, or delete the sentence; no "
                "candidate passage was retrieved; inspect the source manually before deciding absence.")
    if judgement["verdict"] == "claim_stronger_than_source":
        softened = text
        replacements = [
            (r"\bcauses?\b|\bcaused\b|\bcausing\b", "is associated with"),
            (r"\bleads? to\b|\bled to\b", "coincides with"),
            (r"\bresults? in\b|\bresulted in\b", "is accompanied by"),
            (r"\bproves?\b|\bproven\b", "supports"),
            (r"\bconclusively\b|\bdefinitively\b", "in this dataset"),
            (r"\balways\b", "in the reported conditions"),
            (r"\bnever\b", "not in the reported conditions"),
            (r"\bestablishes?\b", "supports"),
            (r"\bcauses?\b", "is associated with"),
            (r"导致|引起|造成", "与…相关"),
            (r"证实|证明", "支持"),
            (r"总是", "在所报告条件下"),
        ]
        for pattern, replacement in replacements:
            softened, count = re.subn(pattern, replacement, softened, flags=re.I)
            if count:
                break
        return (f"Weaken the wording to what the source shows, for example: "
                f"\"{softened}\" — then state the design/statistic that limits it.")
    if judgement["verdict"] == "weakly_linked":
        return ("Point at the exact passage (section, page, paragraph) that carries this claim, "
                "or quote it; the current link is only word overlap.")
    if judgement["verdict"] == "source_stronger_than_claim":
        return "The source is more definite than the sentence; either cite it directly or keep "
    return "Inspect the full cited source and decide entailment, direction, population and conditions. Lexical overlap does not establish support."


def build_ledger(doc: Path, sources_dir: Path, citation_map: dict | None = None) -> dict:
    paragraphs, meta = read_docx_text(doc)
    references = split_reference_list(paragraphs)
    claims = extract_claims([p for p in paragraphs if references.get("start_paragraph") is None or p["index"] < references["start_paragraph"]])
    sources = collect_sources(sources_dir)
    citation_map=citation_map or {}
    for claim in claims:
        bound_paths=[]
        for number in claim["citation_numbers"]:
            value=citation_map.get(str(number),[])
            if isinstance(value,str): value=[value]
            bound_paths.extend(str((sources_dir/name).resolve()) for name in value)
        bound=[source for source in sources if str(Path(source["path"]).resolve()) in bound_paths]
        # Without an explicit verified citation/source map, retrieval is only a candidate.
        evidence = best_evidence(claim, bound if bound else sources)
        claim["source_identity_verified"]=bool(bound) and all(any(str(Path(source["path"]).resolve())==str((sources_dir/name).resolve()) for source in sources for name in ([citation_map[str(n)]] if isinstance(citation_map.get(str(n)),str) else citation_map.get(str(n),[]))) for n in claim["citation_numbers"])
        claim["retrieval_scope"]="explicit_cited_source_map" if bound else "unbound_candidate_only"
        judgement = judge(claim, evidence)
        judgement["suggestion"] = narrow_suggestion(claim, judgement)
        claim["evidence"] = evidence
        judgement["semantic_support_verified"]=False
        judgement["reasons"].append("Lexical rules only; agent must inspect source entailment and verify cited-source identity.")
        claim["judgement"] = judgement
        cited = [e for e in references.get("entries", []) if e["number"] in claim["citation_numbers"]]
        claim["cited_references"] = [
            {"number": e["number"], "doi": e["doi"], "year": e["year"],
             "title_guess": e["title_guess"], "paragraph_index": e["paragraph_index"]}
            for e in cited
        ]
        claim["citation_support"] = ("cited_reference_present" if cited else
                                     ("citation_without_reference_entry"
                                      if claim["citation_numbers"] or claim["citations"]
                                      else "no_citation_marker"))
    summary = {}
    for claim in claims:
        summary[claim["judgement"]["verdict"]] = summary.get(claim["judgement"]["verdict"], 0) + 1
    return {
        "schema": "evidence-ledger/v1",
        "document": {"path": str(doc), "sha256": meta["package_sha256"],
                     "paragraph_count": len(paragraphs)},
        "sources": [{"path": s["path"], "kind": s.get("kind"), "sha256": s.get("sha256"),
                     "passages": len(s.get("passages") or []), "error": s.get("error")}
                    for s in sources],
        "references": {"found": references["found"],
                       "entry_count": references.get("entry_count", 0),
                       "start_paragraph": references.get("start_paragraph"),
                       "entries": references.get("entries", [])},
        "claims": claims,
        "claim_count": len(claims),
        "verdict_summary": summary,
        "determinism": "Rule-based extraction and scoring over the supplied files; the same "
                       "inputs reproduce this ledger byte-for-byte.",
    }


def audit_citations(ledger: dict) -> dict:
    findings = []
    numbers = {e["number"] for e in ledger["references"].get("entries", [])}
    used = set()
    for claim in ledger["claims"]:
        used |= set(claim["citation_numbers"])
        if claim["citation_support"] == "citation_without_reference_entry":
            findings.append({
                "id": f"K{len(findings) + 1:03d}", "kind": "citation_without_entry",
                "locator": claim["locator"], "evidence": claim["text"][:200],
                "detail": f"citation markers {claim['citations']} have no numbered reference entry",
                "action": "Add the missing reference entry or correct the citation number.",
                "severity": "high"})
        for reference in claim["cited_references"]:
            if not reference["doi"]:
                findings.append({
                    "id": f"K{len(findings) + 1:03d}", "kind": "reference_missing_doi",
                    "locator": claim["locator"],
                    "evidence": f"reference [{reference['number']}] has no DOI",
                    "detail": "A reference without a DOI is harder to re-check; the entry may be "
                              "a secondary citation.",
                    "action": "Add the DOI/identifier, or record that the source only exists in "
                              "print.",
                    "severity": "low"})
        for reference in claim["cited_references"]:
            if not reference["year"]:
                findings.append({
                    "id": f"K{len(findings) + 1:03d}", "kind": "reference_missing_year",
                    "locator": claim["locator"],
                    "evidence": f"reference [{reference['number']}] has no year",
                    "detail": "Reference metadata is incomplete.", "severity": "low",
                    "action": "Complete the entry."})

    unused = sorted(numbers - used)
    if unused:
        findings.append({
            "id": f"K{len(findings) + 1:03d}", "kind": "reference_never_cited",
            "locator": f"references p{ledger['references'].get('start_paragraph')}",
            "evidence": f"entries {unused} are never cited in the inspected body",
            "detail": "Reference-list entries with no in-text citation.",
            "action": "Cite them where they belong or remove them.",
            "severity": "medium"})

    duplicates = {}
    for entry in ledger["references"].get("entries", []):
        if entry["doi"]:
            duplicates.setdefault(entry["doi"].lower(), []).append(entry["number"])
    for doi, nums in duplicates.items():
        if len(nums) > 1:
            findings.append({
                "id": f"K{len(findings) + 1:03d}", "kind": "duplicate_reference",
                "locator": f"references {nums}",
                "evidence": f"DOI {doi} appears in entries {nums}",
                "detail": "The same source is listed more than once, so numbering is ambiguous.",
                "action": "Merge the duplicate entries and renumber.",
                "severity": "medium"})

    order = [entry["number"] for entry in ledger["references"].get("entries", [])]
    if order != sorted(order) or len(set(order)) != len(order):
        findings.append({
            "id": f"K{len(findings) + 1:03d}", "kind": "reference_numbering",
            "locator": "references", "evidence": f"entry numbers in file order: {order[:24]}",
            "detail": "Entry numbers are not strictly ascending and unique.",
            "action": "Renumber the list, or confirm the style intends a different order.",
            "severity": "low"})

    return {
        "schema": "citation-audit/v1",
        "findings": findings,
        "finding_count": len(findings),
        "references_used": sorted(used),
        "references_unused": unused,
        "scope_note": "Metadata consistency inside the supplied document and reference list. It "
                      "cannot prove a source exists externally; that needs a database lookup the "
                      "case must allow.",
    }


def write_report(ledger: dict, audit: dict, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "claim-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    (outdir / "citation-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    lines = ["# Evidence ledger", "",
             f"Document: `{ledger['document']['path']}` (sha256 {ledger['document']['sha256'][:16]}…)",
             f"Claims extracted: {ledger['claim_count']}",
             f"Supplied sources: {len(ledger['sources'])}",
             f"Reference entries: {ledger['references'].get('entry_count', 0)}", "",
             "Verdict summary: " + ", ".join(f"{k}={v}" for k, v in sorted(ledger["verdict_summary"].items())),
             "", "## Claims, evidence and reasons", "",
             "| claim | locator | verdict | strongest evidence | reasons | suggestion |",
             "|---|---|---|---|---|---|"]
    for claim in ledger["claims"]:
        judgement = claim["judgement"]
        best = judgement.get("strongest_evidence") or {}
        evidence = f"{Path(best.get('source', '-')).name}#{best.get('passage_id', '-')} ({best.get('score', 0):.2f})"
        reasons = "; ".join(judgement["reasons"])
        suggestion = judgement["suggestion"].replace("|", "/")
        lines.append(f"| {claim['claim_id']} `{claim['text'][:70]}` | {claim['locator']} | "
                     f"{judgement['verdict']} | {evidence} | {reasons} | {suggestion} |")
    lines += ["", "## Sources and hashes", "",
              "| source | kind | sha256 | passages |", "|---|---|---|---|"]
    for source in ledger["sources"]:
        lines.append(f"| `{source['path']}` | {source['kind']} | "
                     f"{(source['sha256'] or '')[:16]}… | {source['passages']} |")
    lines += ["", "## Citation findings", "",
              "| id | kind | locator | detail | action |", "|---|---|---|---|---|"]
    for finding in audit["findings"]:
        lines.append(f"| {finding['id']} | {finding['kind']} | {finding['locator']} | "
                     f"{finding['detail']} | {finding['action']} |")
    lines += ["", "This ledger is rule-based over the supplied files. It records what the "
                  "supplied evidence can and cannot carry; it does not certify that a source is "
                  "correct or that a claim is scientifically true."]
    (outdir / "EVIDENCE_LEDGER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ledger": str(outdir / "claim-ledger.json"),
            "audit": str(outdir / "citation-audit.json"),
            "report": str(outdir / "EVIDENCE_LEDGER.md"),
            "claims": ledger["claim_count"], "findings": audit["finding_count"]}


def verify_sources(ledger_path: Path, sources_dir: Path) -> dict:
    """Re-run the extraction and prove the ledger still matches the files it names."""
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    checks = []
    doc_path = Path(ledger["document"]["path"])
    if doc_path.exists():
        _, meta = read_docx_text(doc_path)
        checks.append({"id": "document_hash", "status": "pass"
                       if meta["package_sha256"] == ledger["document"]["sha256"] else "fail",
                       "evidence": f"document sha256 {meta['package_sha256'][:16]}…"})
    else:
        checks.append({"id": "document_hash", "status": "fail",
                       "evidence": f"{doc_path} not found"})
    fresh_sources = {s["path"]: s for s in collect_sources(sources_dir)}
    for source in ledger["sources"]:
        current = fresh_sources.get(source["path"])
        ok = bool(current) and current.get("sha256") == source.get("sha256")
        checks.append({"id": f"source_hash:{Path(source['path']).name}",
                       "status": "pass" if ok else "fail",
                       "evidence": f"recorded {(source['sha256'] or '')[:16]}… vs current "
                                   f"{((current or {}).get('sha256') or 'missing')[:16]}…"})
    failures = [c for c in checks if c["status"] == "fail"]
    return {"checks": checks, "passed": len(checks) - len(failures), "failed": len(failures),
            "status": "verified" if not failures else "needs_work",
            "scope_note": "Re-reads the named files and compares hashes, so another person (or "
                          "another run) can reproduce the ledger from the same inputs."}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Claim/evidence ledger and citation audit")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract"); p.add_argument("--doc", required=True)
    p.add_argument("--sources", required=True); p.add_argument("--out", required=True); p.add_argument("--citation-map")
    p = sub.add_parser("audit"); p.add_argument("--ledger", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("report"); p.add_argument("--ledger", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("verify"); p.add_argument("--ledger", required=True); p.add_argument("--sources", required=True)
    p.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    if args.command == "extract":
        ledger = build_ledger(Path(args.doc), Path(args.sources),json.loads(Path(args.citation_map).read_text(encoding="utf-8")) if args.citation_map else None)
        Path(args.out).write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"claims": ledger["claim_count"], "sources": len(ledger["sources"]),
                          "references": ledger["references"].get("entry_count", 0),
                          "verdicts": ledger["verdict_summary"]}, ensure_ascii=False))
        return 0
    if args.command == "audit":
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
        audit = audit_citations(ledger)
        Path(args.out).write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"findings": audit["finding_count"],
                          "unused_references": len(audit["references_unused"])}, ensure_ascii=False))
        return 0
    if args.command == "report":
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
        audit = audit_citations(ledger)
        result = write_report(ledger, audit, Path(args.out))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "verify":
        report = verify_sources(Path(args.ledger), Path(args.sources))
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"passed": report["passed"], "failed": report["failed"],
                          "status": report["status"]}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
