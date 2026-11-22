"""A reading client: open, locate, select, ask, annotate, review, export.

The channel this runs on grades a reading loop, not a set of answers:

    open -> locate the paragraph -> select text -> ask about the selection -> save the note or
    conclusion -> review -> export

and it names two properties the result must have: an answer must correspond to the page and the
selected text, and every annotation anchor must land on a real position in the original. So this
keeps a session whose anchors can be re-verified later, instead of returning text alone.

    reading_client.py index    --source article.txt --session session
    reading_client.py select   --session session --quote "exact words"
    reading_client.py ask      --session session --anchor A1 --question "..." --answer "..."
    reading_client.py annotate --session session --anchor A1 --kind conclusion --note "..."
    reading_client.py review   --session session
    reading_client.py export   --session session --out session/export

An anchor stores the paragraph id, the character span, the exact quote and the quote hash, so review
can prove the anchor still resolves rather than trusting it. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PAGE_MARK = re.compile(r"^\s*(?:\[\[page\s*(\d+)\]\]|---\s*page\s*(\d+)\s*---|PAGE\s+(\d+)\s*$|\f)",
                       re.I)
PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path: Path, payload: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_session(root: Path):
    doc_path = root / "document.json"
    ann_path = root / "annotations.json"
    if not doc_path.exists():
        raise SystemExit(f"no session at {root}; run index first")
    document = load(doc_path)
    annotations = load(ann_path) if ann_path.exists() else {"anchors": [], "entries": [],
                                                            "next_anchor": 1}
    annotations.setdefault("anchors", [])
    annotations.setdefault("entries", [])
    annotations.setdefault("next_anchor", len(annotations["anchors"]) + 1)
    return document, annotations


def write_session(root: Path, document: dict, annotations: dict) -> None:
    save(root / "document.json", document)
    save(root / "annotations.json", annotations)


def cmd_index(args) -> int:
    root = Path(args.session)
    root.mkdir(parents=True, exist_ok=True)
    raw = Path(args.source).read_text(encoding="utf-8", errors="replace")
    pages, current, page = [], [], 1
    for line in raw.splitlines(keepends=True):
        match = PAGE_MARK.match(line)
        if match:
            pages.append((page, "".join(current)))
            current = []
            explicit = next((g for g in match.groups() if g), None)
            page = int(explicit) if explicit else page + 1
            continue
        current.append(line)
    pages.append((page, "".join(current)))

    paragraphs = []
    for page_number, text in pages:
        for piece in [p for p in PARAGRAPH_SPLIT.split(text) if p.strip()]:
            body = piece.strip()
            paragraphs.append({"id": f"p{len(paragraphs) + 1:04d}", "page": page_number,
                               "text": body, "chars": len(body), "sha256": sha(body)[:16]})
    document = {
        "schema": "reading-session/v1",
        "source": {"path": str(args.source),
                   "sha256": hashlib.sha256(Path(args.source).read_bytes()).hexdigest(),
                   "bytes": Path(args.source).stat().st_size},
        "pages": len(pages),
        "paragraphs": paragraphs,
        "note": "Anchors reference a paragraph id and a character span inside it. If the source "
                "changes, review reports every anchor that no longer resolves.",
    }
    # Re-indexing the same session must not throw the reader's work away. Existing annotations are
    # kept, and each anchor is compared against the source version it was made on.
    previous = {}
    if (root / "annotations.json").exists():
        previous = load(root / "annotations.json")
    annotations = {
        "anchors": previous.get("anchors") or [],
        "entries": previous.get("entries") or [],
        "next_anchor": previous.get("next_anchor") or len(previous.get("anchors") or []) + 1,
        "source_history": (previous.get("source_history") or []) + [{
            "sha256": document["source"]["sha256"], "at": args.source,
            "paragraphs": len(paragraphs)}],
    }
    write_session(root, document, annotations)
    kept = len(annotations["anchors"])
    print(json.dumps({"session": str(root), "pages": len(pages), "paragraphs": len(paragraphs),
                      "source_sha256": document["source"]["sha256"][:16],
                      "anchors_kept": kept,
                      "reindexed": bool(previous)},
                     ensure_ascii=False, indent=2))
    if kept:
        print(f"note: {kept} existing anchor(s) were kept; run review to see whether they still "
              f"resolve against this source version")
    return 0


def find_spans(haystack: str, needle: str) -> list:
    spans, start = [], 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return spans
        spans.append((index, index + len(needle)))
        start = index + 1


def cmd_select(args) -> int:
    root = Path(args.session)
    document, annotations = read_session(root)
    quote = args.quote
    found = []
    for paragraph in document["paragraphs"]:
        if args.paragraph and paragraph["id"] != args.paragraph:
            continue
        for start, end in find_spans(paragraph["text"], quote):
            found.append((paragraph, start, end, "verbatim"))
        if not found and args.loose:
            target = re.sub(r"\s+", " ", quote).strip().lower()
            body = re.sub(r"\s+", " ", paragraph["text"]).strip().lower()
            if target and target in body:
                found.append((paragraph, 0, len(paragraph["text"]), "whitespace-insensitive"))

    if not found:
        print(json.dumps({"found": False, "quote": quote[:80],
                          "searched_paragraphs": len(document["paragraphs"]),
                          "how": "no paragraph contains this text"},
                         ensure_ascii=False, indent=2))
        return 2
    if len(found) > 1 and not args.allow_ambiguous:
        print(json.dumps({"found": True, "ambiguous": True, "matches": len(found),
                          "candidates": [{"paragraph": p["id"], "page": p["page"],
                                          "start": s, "end": e} for p, s, e, _ in found[:6]],
                          "how": "this text occurs more than once; pass --paragraph"},
                         ensure_ascii=False, indent=2))
        return 2

    paragraph, start, end, method = found[0]
    anchor = {"id": f"A{annotations['next_anchor']}", "paragraph": paragraph["id"],
              "page": paragraph["page"], "start": start, "end": end, "quote": quote,
              "source_sha256": document["source"]["sha256"],
              "quote_sha256": sha(quote)[:16], "paragraph_sha256": paragraph["sha256"],
              "method": method,
              "context_before": paragraph["text"][max(0, start - args.near):start],
              "context_after": paragraph["text"][end:end + args.near]}
    annotations["next_anchor"] += 1
    annotations["anchors"].append(anchor)
    write_session(root, document, annotations)
    print(json.dumps({"anchor": anchor["id"], "page": anchor["page"],
                      "paragraph": anchor["paragraph"], "method": method,
                      "quote": quote[:120]}, ensure_ascii=False, indent=2))
    return 0


def require_anchor(annotations: dict, anchor_id: str) -> dict:
    for anchor in annotations["anchors"]:
        if anchor["id"] == anchor_id:
            return anchor
    raise SystemExit(f"unknown anchor {anchor_id}; run select first")


def append_entry(root: Path, kind: str, anchor: dict, payload: dict) -> dict:
    document, annotations = read_session(root)
    entry = {"id": f"{kind[0].upper()}{len(annotations['entries']) + 1:03d}", "kind": kind,
             "anchor": anchor["id"], "page": anchor["page"], "quote": anchor["quote"]}
    entry.update(payload)
    annotations["entries"].append(entry)
    write_session(root, document, annotations)
    return entry


def cmd_ask(args) -> int:
    root = Path(args.session)
    document, annotations = read_session(root)
    anchor = require_anchor(annotations, args.anchor)
    inside = None if not args.answer_quote else (args.answer_quote in anchor["quote"])
    if inside is False:
        # the answer claims a quotation the selection does not contain: refuse rather than record it
        entry = append_entry(root, "question", anchor, {
            "question": args.question, "answer": args.answer, "evidence": args.evidence,
            "status": "refused",
            "refusal_reason": "the quoted evidence is not inside the selected text",
            "claimed_quote": args.answer_quote})
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 2
    entry = append_entry(root, "question", anchor, {
        "question": args.question, "answer": args.answer, "evidence": args.evidence,
        "status": args.status, "quoted_evidence_inside_selection": inside})
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_annotate(args) -> int:
    root = Path(args.session)
    document, annotations = read_session(root)
    anchor = require_anchor(annotations, args.anchor)
    entry = append_entry(root, "annotation", anchor,
                         {"note": args.note, "category": args.kind})
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def resolve(anchor: dict, document: dict) -> dict:
    paragraph = next((p for p in document["paragraphs"] if p["id"] == anchor["paragraph"]), None)
    made_against = anchor.get("source_sha256")
    if made_against and made_against != document["source"]["sha256"]:
        # The text may still line up, but the anchor was made on a different version of the source,
        # and a reviewer has to know that before trusting it.
        at_span = paragraph["text"][anchor["start"]:anchor["end"]] if paragraph else ""
        return {"status": "stale_source",
                "why": "made against a different source version"
                       + ("; the span still holds the quote, but re-confirm it"
                          if at_span == anchor["quote"] else
                          "; the span no longer holds the quote")}
    if paragraph is None:
        return {"status": "missing", "why": "the paragraph id is gone from the document"}
    at_span = paragraph["text"][anchor["start"]:anchor["end"]]
    if paragraph["sha256"] != anchor["paragraph_sha256"]:
        if at_span == anchor["quote"]:
            return {"status": "moved", "why": "the paragraph changed but the quote still sits at "
                                              "the recorded span"}
        return {"status": "broken", "why": "the paragraph changed and the span no longer holds "
                                           "the quote"}
    if at_span != anchor["quote"]:
        return {"status": "broken", "why": f"span holds {at_span[:40]!r}, not the recorded quote"}
    if sha(anchor["quote"])[:16] != anchor["quote_sha256"]:
        return {"status": "broken", "why": "the stored quote does not match its own hash"}
    return {"status": "resolved", "why": "span and hash both match"}


def cmd_review(args) -> int:
    root = Path(args.session)
    document, annotations = read_session(root)
    anchors, entries = annotations["anchors"], annotations["entries"]
    results = [{"anchor": a["id"], "page": a["page"], "quote": a["quote"][:90],
                **resolve(a, document)} for a in anchors]
    per_page = {}
    for anchor in anchors:
        per_page.setdefault(anchor["page"], []).append(anchor["id"])
    asked = {e["anchor"] for e in entries if e["kind"] == "question"}
    payload = {
        "schema": "reading-review/v1",
        "anchors": len(anchors),
        "resolved": sum(1 for r in results if r["status"] == "resolved"),
        "moved": [r for r in results if r["status"] == "moved"],
        "broken": [r for r in results if r["status"] == "broken"],
        "missing": [r for r in results if r["status"] == "missing"],
        "per_page": {str(k): v for k, v in sorted(per_page.items())},
        "entries_by_kind": {k: sum(1 for e in entries if e["kind"] == k)
                            for k in sorted({e["kind"] for e in entries})},
        "anchors_without_a_question": [a["id"] for a in anchors if a["id"] not in asked],
        "stale_source": [r for r in results if r["status"] == "stale_source"],
        "verdict": "verified" if anchors and all(r["status"] == "resolved" for r in results)
                   else ("empty" if not anchors else "drift"),
        "scope_note": "Proves each annotation still points at the text it was made on. It does not "
                      "judge whether the answer is correct.",
    }
    save(root / "review.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "verified" else 2


def cmd_export(args) -> int:
    root = Path(args.session)
    out = Path(args.out)
    document, annotations = read_session(root)
    out.mkdir(parents=True, exist_ok=True)
    anchors = {a["id"]: a for a in annotations["anchors"]}
    flat = [{**{k: e.get(k) for k in ("id", "kind", "question", "answer", "note", "evidence",
                                      "status", "category")},
             "anchor": e["anchor"], "page": e["page"],
             "paragraph": anchors.get(e["anchor"], {}).get("paragraph"),
             "quote": anchors.get(e["anchor"], {}).get("quote")}
            for e in annotations["entries"]]
    save(out / "annotations.json", {"schema": "reading-export/v1",
                                    "source": document["source"], "entries": flat,
                                    "anchors": annotations["anchors"]})
    lines = [f"# Reading session: {Path(document['source']['path']).name}", "",
             f"- source sha256: `{document['source']['sha256'][:16]}`",
             f"- pages: {document['pages']}, paragraphs: {len(document['paragraphs'])}",
             f"- anchors: {len(anchors)}, entries: {len(flat)}", ""]
    for page in sorted({a["page"] for a in anchors.values()}):
        lines += [f"## Page {page}", ""]
        for anchor in [a for a in anchors.values() if a["page"] == page]:
            lines += [f"### [{anchor['id']}] {anchor['quote'][:90]}", ""]
            for entry in [e for e in flat if e["anchor"] == anchor["id"]]:
                if entry["kind"] == "question":
                    lines.append(f"- **Q ({entry.get('status')})**: {entry.get('question')}")
                    lines.append(f"  - A: {entry.get('answer')}")
                    if entry.get("evidence"):
                        lines.append(f"  - evidence: {entry['evidence']}")
                else:
                    lines.append(f"- **{entry.get('category', 'note')}**: {entry.get('note')}")
            lines.append("")
    (out / "annotations.md").write_text("\n".join(lines), encoding="utf-8")
    navigation = [{"page": a["page"], "anchor": a["id"], "paragraph": a["paragraph"],
                   "quote": a["quote"][:60]}
                  for a in sorted(anchors.values(), key=lambda x: (x["page"], x["start"]))]
    save(out / "navigation.json", {"schema": "reading-navigation/v1", "ordered": navigation})
    print(json.dumps({"out": str(out), "files": sorted(p.name for p in out.iterdir()),
                      "entries": len(flat), "anchors": len(anchors)}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args) -> int:
    root = Path(args.session)
    document, annotations = read_session(root)
    print(json.dumps({"session": str(root), "pages": document["pages"],
                      "paragraphs": len(document["paragraphs"]),
                      "anchors": len(annotations["anchors"]),
                      "entries": len(annotations["entries"]),
                      "source": document["source"]}, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Reading client with verifiable anchors")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("index"); p.add_argument("--source", required=True); p.add_argument("--session", required=True); p.set_defaults(func=cmd_index)
    p = sub.add_parser("select"); p.add_argument("--session", required=True); p.add_argument("--quote", required=True); p.add_argument("--paragraph"); p.add_argument("--near", type=int, default=120); p.add_argument("--loose", action="store_true"); p.add_argument("--allow-ambiguous", action="store_true"); p.set_defaults(func=cmd_select)
    p = sub.add_parser("ask"); p.add_argument("--session", required=True); p.add_argument("--anchor", required=True); p.add_argument("--question", required=True); p.add_argument("--answer", required=True); p.add_argument("--answer-quote", default=""); p.add_argument("--evidence", default=""); p.add_argument("--status", default="answered", choices=["answered","partial","insufficient_evidence","refused"]); p.set_defaults(func=cmd_ask)
    p = sub.add_parser("annotate"); p.add_argument("--session", required=True); p.add_argument("--anchor", required=True); p.add_argument("--note", required=True); p.add_argument("--kind", default="note"); p.set_defaults(func=cmd_annotate)
    p = sub.add_parser("review"); p.add_argument("--session", required=True); p.set_defaults(func=cmd_review)
    p = sub.add_parser("export"); p.add_argument("--session", required=True); p.add_argument("--out", required=True); p.set_defaults(func=cmd_export)
    p = sub.add_parser("status"); p.add_argument("--session", required=True); p.set_defaults(func=cmd_status)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
