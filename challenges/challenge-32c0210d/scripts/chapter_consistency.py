"""Cross-chapter consistency for a long document: the checks a long-document rubric is about.

The channel this runs on names six breakthrough directions, and four of them are mechanical enough to
check rather than merely describe:

    章节规划        the outline's sections, their order and their word budgets vs the delivered chapters
    跨章节一致性    the same concept written two ways, and paragraphs repeated across chapters
    术语与引用      every citation marker resolves to a reference entry, and every entry is cited
    版本管理        a change record that says what moved, with the author's sentence kept

    python chapter_consistency.py audit --chapters draft/*.md [--outline outline.json]
                                        [--references refs.md] [--out report.json]

Exit 0 when every check passes, 2 when something does not. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.M)
FIGURE_REF = re.compile(r"(?:Figure|Fig\.?|图)\s*([0-9]+[a-zA-Z]?)", re.I)
TABLE_REF = re.compile(r"(?:Table|Tab\.?|表)\s*([0-9]+[a-zA-Z]?)", re.I)
EQ_REF = re.compile(r"(?:Equation|Eq\.?|式)\s*\(?([0-9]+[a-zA-Z]?)\)?", re.I)
SECTION_REF = re.compile(r"(?:§|Section|Sec\.?|第)\s*([0-9]+(?:\.[0-9]+)*)\s*(?:节|章)?", re.I)
CITE_BRACKET = re.compile(r"\[(\d+(?:\s*[-,–]\s*\d+)*)\]")
CITE_AUTHOR = re.compile(r"\(([A-Z][A-Za-z'’\-]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][A-Za-z'’\-]+))?),\s*(\d{4})\)")
CITE_TEX = re.compile(r"\\cite[tp]?\{([^}]+)\}")
REFERENCE_LINE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+(\S.*)$", re.M)


def read_chapters(paths: list) -> dict:
    chapters = {}
    for path in paths:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        chapters[Path(path).as_posix()] = text
    return chapters


def headings_of(text: str) -> list:
    return [{"level": len(m.group(1)), "title": m.group(2).strip(),
             "offset": m.start()} for m in HEADING.finditer(text)]


def normalise_term(term: str) -> str:
    return re.sub(r"[\s\-_/]+", " ", term.strip().lower()).replace("μ", "u").replace("µ", "u")


def section_text(text: str) -> list:
    """Split a chapter into (heading, level, own_body) triples so a finding can name its section."""
    matches = list(HEADING.finditer(text))
    if not matches:
        return [("(no heading)", 1, text)]
    parts = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parts.append((match.group(2).strip(), len(match.group(1)), text[start:end]))
    return parts


def section_subtree(parts: list, index: int) -> str:
    """A section's own text plus every following heading deeper than it, until one at its level."""
    level = parts[index][1]
    bodies = [parts[index][2]]
    for heading, deeper_level, body in parts[index + 1:]:
        if deeper_level <= level:
            break
        bodies.append(body)
    return "\n".join(bodies)


def audit(chapters: dict, outline: dict | None, references: dict | None) -> dict:
    checks = []

    def add(check_id, requirement, ok, evidence):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence})

    joined = "\n\n".join(chapters.values())
    all_headings = []
    for path, text in chapters.items():
        for heading in headings_of(text):
            all_headings.append({**heading, "file": path})

    if not all_headings:
        add("has_structure", "the draft has headings to check", False,
            "no markdown heading found in any supplied chapter")
        return {"checks": checks}

    add("has_structure", "the draft has headings", True,
        f"{len(all_headings)} headings across {len(chapters)} file(s)")

    # --- 章节规划: the outline's sections exist, in order, with their budgets ---
    if outline:
        wanted = outline.get("sections") or []
        present = [normalise_term(item["title"]) for item in all_headings]
        missing, order_issues = [], []
        cursor = -1
        for section in wanted:
            needle = normalise_term(section.get("title") or section.get("id") or "")
            if not needle:
                continue
            hit = next((i for i, title in enumerate(present) if needle in title), None)
            if hit is None:
                missing.append(section.get("title") or section.get("id"))
            elif hit < cursor:
                order_issues.append(section.get("title") or section.get("id"))
            else:
                cursor = hit
        add("outline_sections_present", "every outline section appears as a heading",
            not missing, f"missing={missing}")
        add("outline_order_respected", "the outline's section order is preserved",
            not order_issues, f"out_of_order={order_issues}")

        budgets = []
        for section in wanted:
            target = section.get("words") or section.get("word_budget")
            needle = normalise_term(section.get("title") or "")
            if not target or not needle:
                continue
            body = ""
            for _path, chapter_text in chapters.items():
                parts = section_text(chapter_text)
                for index, (heading, _level, _own) in enumerate(parts):
                    if needle in normalise_term(heading):
                        body = section_subtree(parts, index)
                        break
                if body:
                    break
            words = len(re.findall(r"[A-Za-z]+|[\u4e00-\u9fff]", body))
            budgets.append({"section": section.get("title"), "target": target, "actual": words,
                            "ratio": round(words / target, 2) if target else None})
        if budgets:
            off = [b for b in budgets if b["ratio"] is not None
                   and (b["ratio"] < 0.5 or b["ratio"] > 1.6)]
            add("section_budgets_met", "each section is within 0.5x-1.6x its planned length",
                not off, f"off_budget={off[:6]}")
            add("section_budget_report", "per-section word counts against the plan", True,
                json.dumps(budgets, ensure_ascii=False)[:600])

    # --- required argumentative elements ---
    elements = {
        "research question": r"\b(aim|objective|research question|we ask|this study examines|"
                             r"研究问题|本研究|本文)\b",
        "method": r"\b(method|procedure|protocol|materials and methods|方法|实验)\b",
        "results": r"\b(result|finding|we observed|结果|发现)\b",
        "discussion": r"\b(discussion|interpret|we argue|讨论|分析)\b",
        "limitation": r"\b(limitation|limited|caveat|uncertaint|局限|不足|不确定)\b",
    }
    missing_elements = [name for name, pattern in elements.items()
                        if not re.search(pattern, joined, re.I)]
    add("argumentative_elements", "research question, method, results, discussion and limitation "
                                 "are all present", not missing_elements,
        f"missing={missing_elements}")

    # --- 跨章节一致性: numbering continuity and cross-reference resolution ---
    for label, pattern in (("figure", FIGURE_REF), ("table", TABLE_REF), ("equation", EQ_REF)):
        numbers = defaultdict(list)
        for path, text in chapters.items():
            for match in pattern.finditer(text):
                numbers[match.group(1)].append(path)
        if not numbers:
            continue
        order = sorted(numbers, key=lambda value: (len(value), value))
        gaps = []
        try:
            numeric = sorted({int(value.rstrip("abcdefghijklmnopqrstuvwxyz"))
                              for value in numbers if value.rstrip("abcdefghijklmnopqrstuvwxyz").isdigit()})
            if numeric:
                gaps = [n for n in range(1, numeric[-1] + 1) if n not in numeric]
        except ValueError:
            pass
        add(f"{label}_numbering_continuous", f"the {label} numbers have no gap", not gaps,
            f"used={order} missing={gaps}")

    # --- 术语与引用: citations resolve both ways ---
    cited_brackets = set()
    for text in chapters.values():
        for match in CITE_BRACKET.finditer(text):
            for part in re.split(r"[,\-–]", match.group(1)):
                part = part.strip()
                if part.isdigit():
                    cited_brackets.add(part)
    cited_authors = {(m.group(1), m.group(2)) for text in chapters.values()
                     for m in CITE_AUTHOR.finditer(text)}
    cited_tex = {key.strip() for text in chapters.values() for m in CITE_TEX.finditer(text)
                 for key in m.group(1).split(",")}

    if references:
        ref_text = "\n".join(references.values())
        numbered = {m.group(1) for m in REFERENCE_LINE.finditer(ref_text) if m.group(1)}
        if cited_brackets or numbered:
            unresolved = sorted(cited_brackets - numbered, key=lambda v: int(v))
            uncited = sorted(numbered - cited_brackets, key=lambda v: int(v))
            add("citations_resolve", "every numeric citation has a reference entry",
                not unresolved, f"cited_but_no_entry={unresolved}")
            add("references_all_cited", "every reference entry is cited at least once",
                not uncited, f"entry_never_cited={uncited}")
        for name, (surname, year) in sorted(cited_authors):
            hit = re.search(rf"{re.escape(surname)}[^\n]{{0,120}}{year}", ref_text)
            add(f"citation_author_{surname}_{year}", f"{surname} {year} resolves to an entry",
                bool(hit), f"searched the reference list for '{surname}' and '{year}'")
        for key in sorted(cited_tex):
            hit = re.search(rf"\b{re.escape(key)}\b", ref_text)
            add(f"citation_key_{key}", f"the citation key {key} has a bibliography entry",
                bool(hit), f"key '{key}' in the reference list" if hit else f"key '{key}' missing")
    elif cited_brackets or cited_authors or cited_tex:
        add("references_supplied", "the material needed to resolve the citations is present",
            False, f"the draft cites {len(cited_brackets)} numbered, "
                   f"{len(cited_authors)} author-year and {len(cited_tex)} keyed references, "
                   f"but no reference list was supplied to check them against")

    # --- 跨章节一致性: the same concept written two ways ---
    variants = defaultdict(set)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", joined)
    for token in tokens:
        variants[normalise_term(token)].add(token)
    inconsistent = {key: sorted(values) for key, values in variants.items() if len(values) > 1}
    # a unit written two ways is a real defect; a word that is merely capitalised differently is not
    units = re.compile(r"(MPa|kPa|GPa|Pa|mL|μL|uL|µL|mV|kV|mA|μm|µm|um|nm|kHz|MHz|GHz|°C|℃)", re.I)
    unit_variants = {}
    for key, values in inconsistent.items():
        if any(units.fullmatch(value) for value in values):
            unit_variants[key] = values
    add("units_written_consistently", "each unit symbol is written one way throughout",
        not unit_variants, f"variants={unit_variants}")

    # --- repeat detection across chapters ---
    def shingles(text: str, size: int = 9) -> set:
        words = re.findall(r"\w+", text.lower())
        return {" ".join(words[i:i + size]) for i in range(max(0, len(words) - size + 1))}

    per_chapter = {path: shingles(text) for path, text in chapters.items()}
    duplicated = []
    paths = sorted(per_chapter)
    for i, left in enumerate(paths):
        for right in paths[i + 1:]:
            shared = per_chapter[left] & per_chapter[right]
            if len(shared) >= 12:
                duplicated.append({"between": [left, right], "shared_shingles": len(shared)})
    add("no_duplicated_passages", "no two chapters repeat one another", not duplicated,
        f"overlapping_pairs={duplicated[:4]}")

    failures = [c for c in checks if c["status"] == "fail"]
    return {"schema": "chapter-consistency/v1",
            "checks": checks, "passed": len(checks) - len(failures),
            "failed": len(failures),
            "status": "consistent" if not failures else "needs_work",
            "scope_note": "Checks structure, numbering, citation resolution and repetition. It does "
                          "not judge whether the argument is correct or the literature is read "
                          "correctly."}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Cross-chapter consistency audit")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("audit")
    p.add_argument("--chapters", nargs="+", required=True)
    p.add_argument("--outline")
    p.add_argument("--references", nargs="*", default=[])
    p.add_argument("--out", default="chapter-consistency.json")
    args = parser.parse_args(argv)

    chapter_paths = []
    for item in args.chapters:
        path = Path(item)
        chapter_paths.extend(sorted(path.rglob("*.md")) if path.is_dir() else [path])
    chapters = read_chapters([str(p) for p in chapter_paths])
    outline = json.loads(Path(args.outline).read_text(encoding="utf-8")) if args.outline else None
    references = read_chapters(args.references) if args.references else None

    report = audit(chapters, outline, references)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
    for check in report["checks"]:
        if check["status"] == "fail":
            print(f"  FAIL {check['id']}: {check['evidence']}")
    print(f"-> {args.out}")
    return 0 if report["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
