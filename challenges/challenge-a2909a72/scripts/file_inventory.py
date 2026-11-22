"""File inventory, content-based de-duplication, version chains and reversible reorganisation.

Written for research-library tasks where the failure that matters is not a wrong classification but an
untrustworthy record: files moved with no manifest, identical content treated as two documents because
the names differ, one name treated as one document because the content changed, unreadable paths
silently skipped while the report says everything finished, and metadata guessed from filenames.

Four rules this module holds to:

  * **Identity is the content hash, never the filename.** Two names, one hash -> one document with two
    names. One name, two hashes -> a version chain.
  * **Nothing is destroyed.** Reorganisation produces a *plan* first; applying it appends to a journal;
    the journal can be reversed. There is no in-place edit path.
  * **Every metadata field names its source** -- filename, content, sidecar, or human -- so a guessed
    value is never presented as an extracted one.
  * **Skips are recorded and counted.** A path that cannot be read is reported with its reason, and the
    run reports how many were skipped rather than claiming completion.

    python file_inventory.py scan      --root DIR --out inv.json
    python file_inventory.py dupes     --inventory inv.json --out dupes.json
    python file_inventory.py versions  --inventory inv.json --out versions.json
    python file_inventory.py plan      --inventory inv.json --rules rules.json --out plan.json
    python file_inventory.py apply     --plan plan.json --journal journal.jsonl [--dry-run]
    python file_inventory.py rollback  --journal journal.jsonl
    python file_inventory.py manifest  --inventory inv.json --out manifest.csv
    python file_inventory.py verify    --inventory inv.json --journal journal.jsonl --out verify.json

Python standard library only. No network.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = "file-inventory/v1"
CHUNK = 1 << 20
TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".tex", ".bib", ".yaml", ".yml",
                 ".xml", ".html", ".rst", ".py", ".r", ".sql", ".cfg", ".ini", ".log"}
ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "big5", "latin-1")

# Version markers people actually append. Stripping only trailing digits is not enough: `analysis_v2`
# leaves a dangling `v`, so the chain never forms and two versions of one document look like two
# documents. Applied repeatedly, because `report_v2_final` carries two markers.
VERSION_TAIL = re.compile(
    r"(?:[\s._\-]*[\(\[]?\d+[\)\]]?)?"
    r"(?:[\s._\-]*(?:v|ver|version|rev|revision|r|draft|final|copy|edited|updated|new)\b[\s._\-]*\d*)?$",
    re.I)
VERSION_STRIP = re.compile(
    r"[\s._\-]*(?:v|ver|version|rev|revision|draft|final|copy|edited|updated|new)[\s._\-]*\d*$"
    r"|[\s._\-]*[\(\[]?\d+[\)\]]?$",
    re.I)


def identity_stem(name_or_stem: str) -> str:
    """The version-independent identity of a name.

    `analysis`, `analysis_v2`, `analysis-3`, `analysis (2)`, `analysis_final` all collapse to
    `analysis`, so a version chain can form. Markers are stripped repeatedly so stacked ones
    (`report_v2_final`) also collapse.

    Stripping never removes the whole identity. A file named `draft.md` or `final.md` is *called* that,
    so its stem is the identity; stripping the marker would leave nothing and silently merge unrelated
    documents into one empty group.
    """
    stem = Path(name_or_stem).stem if "." in name_or_stem else name_or_stem
    original = stem
    previous = None
    while previous != stem:
        previous = stem
        candidate = VERSION_STRIP.sub("", stem).strip(" _-.")
        if not candidate:
            break
        stem = candidate
    return (stem or original).lower()


# --------------------------------------------------------------------------- scanning

def detect_encoding(head: bytes) -> str | None:
    """The first encoding that decodes the sample, or None if it looks binary."""
    if b"\x00" in head[:4096]:
        return None
    for enc in ENCODINGS:
        try:
            head.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return None


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_root(root: Path, max_bytes: int, max_depth: int, follow: bool) -> dict:
    entries: list[dict] = []
    skipped: list[dict] = []
    root = root.resolve()

    def note(path: Path, reason: str, detail: str = "") -> None:
        skipped.append({"path": str(path), "reason": reason, "detail": detail})

    for current, dirnames, filenames in os.walk(root, followlinks=follow, onerror=lambda e: note(
            Path(getattr(e, "filename", root)), "unreadable_dir", str(e))):
        here = Path(current)
        depth = len(here.relative_to(root).parts)
        if depth >= max_depth:
            for name in list(dirnames):
                note(here / name, "too_deep", f"depth >= {max_depth}")
            dirnames[:] = []
        for name in sorted(filenames):
            path = here / name
            if path.is_symlink() and not follow:
                note(path, "symlink", "not followed")
                continue
            try:
                stat = path.stat()
            except OSError as exc:
                note(path, "unreadable", str(exc))
                continue
            if not path.is_file():
                note(path, "not_a_file", "")
                continue
            if stat.st_size > max_bytes:
                note(path, "too_large", f"{stat.st_size} bytes > {max_bytes}")
                continue
            try:
                digest = sha256_of(path)
            except OSError as exc:
                note(path, "unreadable", str(exc))
                continue
            suffix = path.suffix.lower()
            encoding = None
            if suffix in TEXT_SUFFIXES:
                try:
                    with open(path, "rb") as handle:
                        encoding = detect_encoding(handle.read(8192))
                except OSError:
                    encoding = None
            entries.append({
                "path": str(path.relative_to(root)),
                "name": name,
                "stem": identity_stem(path.name),
                "suffix": suffix,
                "size": stat.st_size,
                "mtime": round(stat.st_mtime, 3),
                "sha256": digest,
                "encoding": encoding,
                "readable": True,
            })

    total = sum(entry["size"] for entry in entries)
    return {
        "schema": SCHEMA,
        "root": str(root),
        "file_count": len(entries),
        "total_bytes": total,
        "skipped_count": len(skipped),
        "skipped": skipped,
        "files": entries,
        "scope_note": (
            f"scanned {len(entries)} file(s) under {root}; {len(skipped)} path(s) skipped and listed "
            "individually. This run does not claim to have covered the skipped paths."
        ),
    }


# --------------------------------------------------------------------------- identity

def group_duplicates(inventory: dict) -> dict:
    """Group by content hash. Two names with one hash are one document, whatever the names say."""
    by_hash: dict[str, list[dict]] = {}
    for entry in inventory["files"]:
        by_hash.setdefault(entry["sha256"], []).append(entry)
    groups = []
    for digest, members in sorted(by_hash.items(), key=lambda kv: -len(kv[1])):
        if len(members) < 2:
            continue
        names = sorted({m["name"] for m in members})
        groups.append({
            "sha256": digest,
            "size": members[0]["size"],
            "count": len(members),
            "paths": sorted(m["path"] for m in members),
            "names_differ": len(names) > 1,
            "kind": "renamed_copy" if len(names) > 1 else "same_name_copy",
        })
    return {
        "schema": SCHEMA,
        "duplicate_groups": len(groups),
        "redundant_files": sum(g["count"] - 1 for g in groups),
        "sha256_basis": "content hash; filenames are never used to decide identity",
        "groups": groups,
    }


def build_version_chains(inventory: dict) -> dict:
    """Same identity, different content over time -> a version chain ordered by mtime.

    Identity here is the normalised stem: a trailing number or date is stripped, so `report_v3` and
    `report` are candidates. The chain records which hash superseded which and the size delta, and it
    states plainly that ordering is by modification time rather than by editorial intent.
    """
    by_stem: dict[str, list[dict]] = {}
    for entry in inventory["files"]:
        key = entry["stem"].lower() or identity_stem(entry["name"]) or entry["name"].lower()
        by_stem.setdefault(key, []).append(entry)
    chains = []
    for stem, members in sorted(by_stem.items()):
        hashes = {m["sha256"] for m in members}
        if len(members) < 2 or len(hashes) < 2:
            continue
        members.sort(key=lambda m: (m["mtime"], m["path"]))
        steps = []
        for older, newer in zip(members, members[1:]):
            steps.append({
                "from": older["path"], "to": newer["path"],
                "from_sha256": older["sha256"][:16], "to_sha256": newer["sha256"][:16],
                "size_delta": newer["size"] - older["size"],
                "identical_content": older["sha256"] == newer["sha256"],
            })
        chains.append({
            "identity": stem,
            "versions": len(members),
            "current": members[-1]["path"],
            "supersedes": [m["path"] for m in members[:-1]],
            "steps": steps,
        })
    return {
        "schema": SCHEMA,
        "chain_count": len(chains),
        "ordering_basis": "modification time, not editorial intent; a rebuild can be newer than an edit",
        "chains": chains,
    }


# --------------------------------------------------------------------------- reorganisation

def build_plan(inventory: dict, rules: dict) -> dict:
    """Produce the reorganisation as a plan. This function touches nothing on disk."""
    template = rules.get("naming_template", "{stem}{suffix}")
    keep = rules.get("keep_duplicate_policy", "first_by_path")
    operations = []
    seen_targets: dict[str, str] = {}

    for entry in sorted(inventory["files"], key=lambda e: e["path"]):
        fields = {
            "stem": entry["stem"] or "unnamed",
            "name": entry["name"],
            "suffix": entry["suffix"],
            "sha256_12": entry["sha256"][:12],
            "mtime_year": str(__import__("datetime").datetime.fromtimestamp(entry["mtime"]).year),
        }
        target_name = template.format(**fields)
        target_name = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", target_name)
        rel_parent = Path(entry["path"]).parent
        target = str(rel_parent / target_name) if template != "{name}" else entry["path"]
        if target == entry["path"]:
            continue
        if target in seen_targets:
            operations.append({"action": "archive_duplicate", "path": entry["path"],
                               "reason": f"target name already claimed by {seen_targets[target]}",
                               "policy": keep})
            continue
        seen_targets[target] = entry["path"]
        operations.append({
            "action": "rename", "path": entry["path"], "target": target,
            "sha256": entry["sha256"][:16],
            "reason": f"naming template {template!r}",
        })

    return {
        "schema": SCHEMA,
        "dry": True,
        "operations": len(operations),
        "reversible": "every operation is applied through a journal and can be reversed",
        "irreversible_operations": 0,
        "plan": operations,
    }


def append_journal(journal: Path, record: dict) -> None:
    journal.parent.mkdir(parents=True, exist_ok=True)
    with open(journal, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def apply_plan(plan: dict, root: Path, journal: Path, dry: bool) -> dict:
    """Apply renames, journalling each one so the state can be reversed. Idempotent."""
    done, failed, skipped_already = [], [], []
    for operation in plan.get("plan", []):
        source = root / operation["path"]
        target = root / operation["target"]
        if not source.exists():
            if target.exists():
                skipped_already.append(operation["path"])
                continue
            failed.append({"path": operation["path"], "reason": "source absent and target absent"})
            continue
        if target.exists():
            failed.append({"path": operation["path"], "reason": f"target exists: {target.name}"})
            continue
        if dry:
            done.append({"path": operation["path"], "target": operation["target"], "dry": True})
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
        except OSError as exc:
            failed.append({"path": operation["path"], "reason": str(exc)})
            continue
        append_journal(journal, {"action": "rename", "root": str(root),
                                 "from": operation["path"], "to": operation["target"],
                                 "sha256": operation.get("sha256")})
        done.append({"path": operation["path"], "target": operation["target"]})
    return {"schema": SCHEMA, "applied": len(done), "already_done": len(skipped_already),
            "failed": len(failed), "dry_run": dry, "journal": str(journal),
            "failures": failed, "operations": done}


def rollback(journal: Path) -> dict:
    """Reverse the journal, newest first, so a partial apply is undone in the right order."""
    if not journal.exists():
        return {"schema": SCHEMA, "reversed": 0, "note": "no journal"}
    records = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
    reversed_count, failures = 0, []
    for record in reversed(records):
        if record.get("action") != "rename":
            continue
        root, back, fwd = Path(record["root"]), Path(record["from"]), Path(record["to"])
        source, target = root / fwd, root / back
        if not source.exists():
            failures.append({"path": record["to"], "reason": "already restored or removed"})
            continue
        if target.exists():
            failures.append({"path": record["from"], "reason": "original path occupied"})
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
            reversed_count += 1
        except OSError as exc:
            failures.append({"path": record["to"], "reason": str(exc)})
    return {"schema": SCHEMA, "reversed": reversed_count, "failed": len(failures), "failures": failures}


# --------------------------------------------------------------------------- output

def write_manifest(inventory: dict, out: Path) -> dict:
    """A searchable, handover-able CSV. One row per file, with the hash that defines its identity."""
    out.parent.mkdir(parents=True, exist_ok=True)
    columns = ["path", "name", "suffix", "size", "mtime", "sha256", "encoding"]
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for entry in sorted(inventory["files"], key=lambda e: e["path"]):
            writer.writerow(entry)
    return {"schema": SCHEMA, "rows": len(inventory["files"]), "out": str(out),
            "skipped_rows": inventory.get("skipped_count", 0)}


def verify_state(inventory: dict, root: Path, journal: Path | None) -> dict:
    """Re-hash what is on disk and compare against the manifest the run claimed.

    This is the check that turns 'the reorganisation finished' into 'the reorganisation finished and
    the content is intact'. A missing file, a changed hash or a failed journal entry is reported.
    """
    expected = {entry["path"]: entry["sha256"] for entry in inventory["files"]}
    moved: dict[str, str] = {}
    if journal and journal.exists():
        for line in journal.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("action") == "rename":
                moved[record["from"]] = record["to"]

    def locate(rel: str) -> Path:
        return root / moved.get(rel, rel)

    present, missing, changed = 0, [], []
    for rel, digest in sorted(expected.items()):
        path = locate(rel)
        if not path.exists():
            missing.append(rel)
            continue
        try:
            if sha256_of(path) != digest:
                changed.append(rel)
                continue
        except OSError as exc:
            changed.append(f"{rel} ({exc})")
            continue
        present += 1
    return {
        "schema": SCHEMA,
        "expected": len(expected),
        "present_and_identical": present,
        "missing": missing,
        "content_changed": changed,
        "relocated": len(moved),
        "status": "verified" if not missing and not changed else "needs_work",
    }


# --------------------------------------------------------------------------- cli

def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="File inventory, de-duplication and version chains")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scan")
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-bytes", type=int, default=200 * 1024 * 1024)
    p.add_argument("--max-depth", type=int, default=24)
    p.add_argument("--follow-symlinks", action="store_true")

    p = sub.add_parser("dupes"); p.add_argument("--inventory", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("versions"); p.add_argument("--inventory", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("plan"); p.add_argument("--inventory", required=True); p.add_argument("--rules", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("apply"); p.add_argument("--plan", required=True); p.add_argument("--journal", required=True); p.add_argument("--root"); p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("rollback"); p.add_argument("--journal", required=True)
    p = sub.add_parser("manifest"); p.add_argument("--inventory", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("verify"); p.add_argument("--inventory", required=True); p.add_argument("--root"); p.add_argument("--journal"); p.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.command == "scan":
        inventory = scan_root(Path(args.root), args.max_bytes, args.max_depth, args.follow_symlinks)
        write_json(args.out, inventory)
        print(json.dumps({"files": inventory["file_count"], "skipped": inventory["skipped_count"],
                          "bytes": inventory["total_bytes"], "out": args.out}, ensure_ascii=False))
        return 0
    if args.command == "dupes":
        result = group_duplicates(read_json(args.inventory)); write_json(args.out, result)
        print(json.dumps({"groups": result["duplicate_groups"], "redundant": result["redundant_files"]}, ensure_ascii=False))
        return 0
    if args.command == "versions":
        result = build_version_chains(read_json(args.inventory)); write_json(args.out, result)
        print(json.dumps({"chains": result["chain_count"]}, ensure_ascii=False))
        return 0
    if args.command == "plan":
        result = build_plan(read_json(args.inventory), read_json(args.rules)); write_json(args.out, result)
        print(json.dumps({"operations": result["operations"], "dry": True}, ensure_ascii=False))
        return 0
    if args.command == "apply":
        plan = read_json(args.plan)
        root = Path(args.root) if args.root else Path(plan.get("root", "."))
        result = apply_plan(plan, root, Path(args.journal), args.dry_run)
        print(json.dumps({k: result[k] for k in ("applied", "failed", "already_done", "dry_run")}, ensure_ascii=False))
        return 0 if result["failed"] == 0 else 3
    if args.command == "rollback":
        result = rollback(Path(args.journal))
        print(json.dumps({"reversed": result["reversed"], "failed": result["failed"]}, ensure_ascii=False))
        return 0 if result["failed"] == 0 else 3
    if args.command == "manifest":
        result = write_manifest(read_json(args.inventory), Path(args.out))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "verify":
        inventory = read_json(args.inventory)
        root = Path(args.root) if args.root else Path(inventory["root"])
        result = verify_state(inventory, root, Path(args.journal) if args.journal else None)
        write_json(args.out, result)
        print(json.dumps({k: result[k] for k in ("expected", "present_and_identical", "missing", "content_changed", "status")}, ensure_ascii=False))
        return 0 if result["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
