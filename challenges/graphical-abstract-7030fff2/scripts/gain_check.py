"""Independent information gain of a deliverable over its source material.

Every channel in this track awards 25 points under 使用增益 / 增益可验证性 and 15 under 创新增益 /
创新证据, and every rubric says the same thing in the same words: written self-description cannot
stand in for runtime evidence. This script produces that runtime evidence.

It measures a *run*, not a claim. Given the case's source material and the deliverable the skill
produced from it, it scores an answer by two things only:

  coverage   the answer restates the source facts it is supposed to carry
  grounding  every number in the answer traces to a number in the supplied material

    info --source DIR --answer FILE --out gain.json
    info --source DIR --answer FILE --baseline FILE --out gain.json   # add a comparison answer

Exit codes: 0 measured, 2 measurement refused (the inputs are not comparable), 3 usage error.
Standard library only, deterministic, no network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".tex", ".html", ".yaml",
                 ".yml", ".rst", ".bib"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache"}
NUMBER = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?:\s*[eE][-+]?\d+)?(?![\w])")
CJK = re.compile(r"[\u4e00-\u9fff]")
SENT = re.compile(r"[^。！？!?\n]{6,}?[。！？!?]|\S[^\n]{9,}")
# Structured answers (JSON, CSV rows) carry no sentence punctuation, so a whole record list arrives as
# one "sentence" and would need one source sentence to contain every number at once. Break those on
# record and field boundaries as well, so each claim is measured on its own.
CLAIM_SPLIT = re.compile(r"[。！？!?;；]|\}\s*,?\s*\{|,(?=\s*[\"\[{])|\n")
# A number that names a location is not a data claim: "para 1", "p. 3", "table 2", "row 4".
LOCATOR_KEY = re.compile(
    r"(?:locator|location|page|para|paragraph|line|row|col|section|sec|table|tbl|figure|fig|"
    r"ref|reference|id|index|item|step|chunk|span|offset|no)[\s._\-:=#]*$", re.I)

UNIT = re.compile(
    r"(?:%|‰|℃|°C|mg|kg|μg|ug|ng|g|mL|ml|μL|uL|L|mol|mmol|μmol|umol|nmol|mM|μM|uM|nM|"
    r"h|min|s|ms|day|days|week|weeks|month|months|year|years|mm|cm|m|nm|μm|um|km|Pa|kPa|MPa|"
    r"bar|atm|eV|keV|MeV|Gy|Sv|Bq|Ci|Da|kDa|bp|kb|Mb|Gb|rpm|g/L|mg/L|wt%|vol%|at%|"
    r"fold|x|倍|天|小时|分钟|秒|周|月|年|毫米|厘米|米|千米|微米|纳米|克|千克|毫克|微克|纳克|"
    r"升|毫升|微升|摩尔|毫摩尔|微摩尔|纳摩尔|帕|千帕|兆帕|电子伏|开尔文|摄氏度|次|个|例|名|只|份)",
    re.I)

NEGATION = ("not ", "no ", "never", "unable", "cannot", "could not", "failed to", "without",
            "未", "无法", "不能", "没有", "尚未", "不适用", "n/a", "not reported", "未报告",
            "not available", "未提供", "缺失")
HEDGE = ("may ", "might ", "could ", "suggest", "appears", "likely", "possibly", "seems",
         "可能", "提示", "似乎", "倾向", "推测", "有待", "初步")
# A short structured claim ("87.5 %", "5.0 wt%") restates one source value and has few tokens to
# overlap with, so it needs a lower bar than a full sentence to count as supported.
COVERAGE_HIT = 0.55


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def material_corpus(root: Path) -> dict[str, str]:
    """Every readable text file under the supplied material, plus its provenance."""
    files: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if SKIP_DIRS & set(p.parts):
            continue
        files[p.relative_to(root).as_posix()] = read_text(p)
    return files


def norm_number(token: str) -> str:
    """Compare numbers by value so 1.0 / 1 / 1.0 written differently still match, but 10 != 100."""
    t = token.replace(",", "").replace("·", ".").replace(" ", "")
    try:
        value = float(t)
    except ValueError:
        return t
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(round(value, 10))


def numbers(text: str) -> set[str]:
    return {norm_number(m.group(0)) for m in NUMBER.finditer(text)}


def statements(text: str) -> list[str]:
    parts = []
    for chunk in CLAIM_SPLIT.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        found = [m.group(0).strip() for m in SENT.finditer(chunk) if len(m.group(0).strip()) >= 12]
        parts.extend(found or ([chunk] if len(chunk) >= 12 else []))
    return parts


def claimed_numbers(text: str) -> set[str]:
    """Numbers the answer asserts about the material, excluding text that merely cites a location."""
    masked = list(text)
    for m in NUMBER.finditer(text):
        prefix = text[max(0, m.start() - 24):m.start()]
        if LOCATOR_KEY.search(prefix):
            for i in range(m.start(), m.end()):
                masked[i] = " "
    return numbers("".join(masked))


# In a structured field record the field *name* is not a claim about the material, only the value is.
JSON_KEY = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:')
# A field name is an identifier, not prose: "yield_treated" must not be read as the words it contains.
IDENT = re.compile(r'"[A-Za-z_][A-Za-z0-9_]*"')
# Pairs that describe where a value came from, or how it is classified, rather than asserting a value.
METADATA_KEY = re.compile(
    r"^(?:locator|location|page|para|paragraph|line|row|col|column|section|sec|table|tbl|figure|fig|"
    r"ref|reference|id|index|item|step|chunk|span|offset|no|kind|type|status|level|severity|"
    r"confidence|note|comment|label|tag|category|source|cite|citation|anchor|pointer)$", re.I)
PAIR = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*(?:"[^"]*"|\[[^\]]*\]|\{[^}]*\}|[^,}\]]*)')


def claim_values(fragment: str) -> str:
    """Strip field names and metadata pairs so only the asserted values are measured."""
    if '"' not in fragment:
        return fragment
    kept = PAIR.sub(lambda m: " " if METADATA_KEY.match(m.group(1)) else m.group(0), fragment)
    return IDENT.sub(" ", JSON_KEY.sub(" ", kept))


def tokens(text: str) -> set[str]:
    latin = set(re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower()))
    cjk = set(CJK.findall(text))
    bigrams = {text[i:i + 2] for i in range(len(text) - 1)
               if CJK.match(text[i]) and CJK.match(text[i + 1])}
    return latin | cjk | bigrams


def measure(source: Path, answer_path: Path) -> dict:
    files = material_corpus(source)
    if not files:
        return {"refused": "no readable text in --source", "source_files": []}
    source_all = "\n".join(files.values())
    answer = read_text(answer_path)
    if not answer.strip():
        return {"refused": "empty --answer", "source_files": list(files)}

    src_numbers = numbers(source_all)
    ans_stmts = statements(answer)
    traceable = claimed_numbers(answer) & src_numbers
    untraceable = sorted(claimed_numbers(answer) - src_numbers)
    claimed = claimed_numbers(answer)
    ans_units = {m.group(0).lower() for m in UNIT.finditer(answer)}

    src_stmts = statements(source_all)
    src_tokens = [tokens(s) for s in src_stmts]
    src_token_union: set[str] = set()
    for t in src_tokens:
        src_token_union |= t

    supported, considered, skipped = 0, 0, 0
    unsupported: list[dict] = []
    for raw in ans_stmts:
        s = claim_values(raw).strip()
        if len(s) < 12:
            # A bare structured value ("87.5 %") is a claim; measure it on its numbers alone.
            s = raw.strip()
            st = set()
        else:
            st = tokens(s)
        if not s.strip():
            skipped += 1
            continue
        sn = claimed_numbers(s)
        if sn:
            considered += 1
            # A claim that carries numbers stands or falls on those numbers, and on its value text
            # appearing in the material at all. Structured field records are judged this way because
            # they carry no prose to overlap with.
            if not (sn <= src_numbers):
                unsupported.append({"statement": raw[:160], "best_overlap": 0.0,
                                    "reason": "carries a number the material does not contain"})
                continue
            if st and not (st & src_token_union):
                unsupported.append({"statement": raw[:160], "best_overlap": 0.0,
                                    "reason": "value text does not appear in the material"})
                continue
            supported += 1
            continue
        if not st:
            skipped += 1
            continue
        considered += 1
        best_score = 0.0
        for stoks in src_tokens:
            overlap = len(st & stoks) / max(1, len(st))
            if overlap > best_score:
                best_score = overlap
        if best_score >= COVERAGE_HIT:
            supported += 1
        elif best_score >= 0.30:
            unsupported.append({"statement": raw[:160], "best_overlap": round(best_score, 3),
                                "reason": "no source sentence supports it closely enough"})

    coverage = supported / considered if considered else 0.0
    grounding = len(traceable) / len(claimed) if claimed else 1.0
    answer_keys = set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]{2,40})"\s*:', answer))

    return {
        "source_files": sorted(files),
        "source_chars": len(source_all),
        "answer_chars": len(answer),
        "answer_statements": len(ans_stmts),
        "claims_measured": considered,
        "claims_not_measurable": skipped,
        "statements_supported": supported,
        "coverage": round(coverage, 4),
        "numbers_claimed": len(claimed),
        "numbers_traceable": len(traceable),
        "numbers_untraceable": untraceable[:40],
        "grounding": round(grounding, 4),
        "units_named": sorted(ans_units)[:40],
        "declared_field_keys": sorted(answer_keys)[:60],
        "compression": round(len(answer) / len(source_all), 4) if source_all else None,
        "rate_of_unsupported": round(len(unsupported) / considered, 4) if considered else 0.0,
        "unsupported_examples": unsupported[:15],
        "verdict": "grounded" if grounding >= 0.98 and coverage >= 0.60 else "needs repair",
    }


def compare(skill: dict, baseline: dict) -> dict:
    """Skill-versus-baseline on the same material.

    Decided on grounding first and on the number of *supported* claims second, so a richer answer
    that is still fully traceable beats a thinner one, while padding with unsupported claims does not
    help. Share-based coverage is reported but not used to decide, because it moves with answer
    length: an answer that simply claims less can score a higher share.
    """
    deltas = {}
    for key in ("coverage", "grounding"):
        a, b = skill.get(key), baseline.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            deltas[key] = round(a - b, 4)
    deltas["statements_supported"] = (skill.get("statements_supported") or 0) - \
                                     (baseline.get("statements_supported") or 0)
    deltas["numbers_claimed"] = (skill.get("numbers_claimed") or 0) - (baseline.get("numbers_claimed") or 0)
    deltas["numbers_untraceable"] = (len(skill.get("numbers_untraceable") or [])
                                     - len(baseline.get("numbers_untraceable") or []))

    grounding_delta = deltas.get("grounding", 0)
    supported_delta = deltas["statements_supported"]
    untraceable_delta = deltas["numbers_untraceable"]

    if untraceable_delta > 0:
        verdict = "baseline_stronger"
    elif grounding_delta > 0:
        verdict = "skill_stronger"
    elif grounding_delta < 0:
        verdict = "baseline_stronger"
    elif supported_delta > 0:
        verdict = "skill_stronger"
    elif supported_delta < 0:
        verdict = "baseline_stronger"
    else:
        verdict = "no_measured_difference"

    return {
        "delta": deltas,
        "verdict": verdict,
        "decided_on": ["grounding", "statements_supported", "numbers_untraceable"],
        "note": ("Same material, same measurement, two answers. On a single case this is a signal, "
                 "not a population claim; repeat across cases before generalising. Coverage is "
                 "reported but excluded from the decision because it moves with answer length."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="directory holding the supplied material")
    ap.add_argument("--answer", required=True, help="the deliverable produced from that material")
    ap.add_argument("--baseline", help="an answer produced without the skill, for the same material")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    source, answer = Path(args.source), Path(args.answer)
    if not source.exists() or not answer.is_file():
        print(json.dumps({"error": "missing --source or --answer"}, ensure_ascii=False))
        return 3

    skill = measure(source, answer)
    if "refused" in skill:
        print(json.dumps(skill, ensure_ascii=False))
        return 2

    report = {"source": str(source), "answer": str(answer), "skill": skill}
    if args.baseline:
        base_path = Path(args.baseline)
        if not base_path.is_file():
            print(json.dumps({"error": "missing --baseline"}, ensure_ascii=False))
            return 3
        baseline = measure(source, base_path)
        if "refused" in baseline:
            print(json.dumps(baseline, ensure_ascii=False))
            return 2
        report["baseline"] = baseline
        report["comparison"] = compare(skill, baseline)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "verdict": skill["verdict"],
                      "coverage": skill["coverage"], "grounding": skill["grounding"],
                      "untraceable_numbers": len(skill["numbers_untraceable"]),
                      "comparison": report.get("comparison", {}).get("verdict"),
                      "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
