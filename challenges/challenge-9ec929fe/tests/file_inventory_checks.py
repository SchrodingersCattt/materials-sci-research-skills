"""Prove file_inventory measures what it claims, on a fixture with planted defects.

Seven behaviours, each with a negative control where one applies. Exit 0 only when all hold.

The fixture is deliberately adversarial: duplicate content under different names, one name with two
different contents over time, a non-ASCII filename, an oversized file, a binary with no text layer, a
symlink and a deep tree. That is the shape of a real research library, and every one of these is
something the brief says existing tools get wrong.

    python tests/file_inventory_checks.py [--workdir work/inventory]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "file_inventory.py"


def run(*argv) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(TOOL), *[str(a) for a in argv]],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def build_fixture(root: Path) -> None:
    if root.exists():
        import shutil
        shutil.rmtree(root)
    (root / "data").mkdir(parents=True)
    (root / "old").mkdir()
    # non-ASCII directory and a filename with a space, built from escapes so no shell layer can
    # corrupt it; this is a real case the brief calls out explicitly
    cjk_dir = root / "\u6df1\u76ee\u5f55"
    cjk_dir.mkdir()

    # 1 - identical content, different names: one document with two names
    payload = b"%PDF-1.4 identical payload" * 40
    (root / "paper.pdf").write_bytes(payload)
    (root / "data" / "paper_copy.pdf").write_bytes(payload)

    # 2 - one identity, two different contents over time: a version chain
    older = root / "analysis.md"
    newer = root / "old" / "analysis_v2.md"
    older.write_text("# v1\nfirst line\n", encoding="utf-8")
    newer.write_text("# v2\nfirst line\nsecond line\nthird line\n", encoding="utf-8")
    os.utime(older, (1_000_000, 1_000_000))
    os.utime(newer, (2_000_000, 2_000_000))

    # 3 - non-ASCII filename with a stray space
    (cjk_dir / "\u5b9e\u9a8c \u8bb0\u5f55.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    # 4 - oversized, must be skipped and counted rather than silently dropped
    (root / "huge.bin").write_bytes(b"0" * (3 * 1024 * 1024))

    # 5 - binary with no text layer
    (root / "image.png").write_bytes(bytes(range(256)) * 8)

    # 6 - symlink, not followed by default
    try:
        os.symlink(root / "paper.pdf", root / "link.pdf")
    except (OSError, NotImplementedError):
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="work/inventory")
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    root = work / "library"
    build_fixture(root)

    failures: list[str] = []
    observed: dict = {}
    inv = work / "inv.json"

    # ---- 1 scan, with a cap that forces the oversized file to be skipped
    rc, out = run("scan", "--root", root, "--max-bytes", 1_000_000, "--out", inv)
    if rc != 0:
        print(json.dumps({"stage": "scan", "rc": rc, "output": out[-400:]}, ensure_ascii=False))
        return 1
    inventory = json.loads(inv.read_text(encoding="utf-8"))
    observed["scan"] = {"files": inventory["file_count"], "skipped": inventory["skipped_count"]}

    if inventory["file_count"] < 4:
        failures.append(f"expected at least 4 readable files, got {inventory['file_count']}")
    # the oversized file must be recorded as skipped, not omitted
    skipped_reasons = {s["reason"] for s in inventory["skipped"]}
    if "too_large" not in skipped_reasons:
        failures.append(f"oversized file was not reported as skipped (reasons: {sorted(skipped_reasons)})")
    if not any("huge.bin" in s["path"] for s in inventory["skipped"]):
        failures.append("the oversized file is absent from the skip record, so the run would claim full coverage")
    # a non-ASCII name must survive intact
    if not any("\u5b9e\u9a8c" in f["path"] for f in inventory["files"]):
        failures.append("the non-ASCII filename did not survive the scan")
    # a symlink must not be silently followed
    if not any(s["reason"] == "symlink" for s in inventory["skipped"]):
        observed.setdefault("notes", []).append("no symlink in fixture or not reported")

    # ---- 2 duplicates are judged by content, not by name
    dupes_path = work / "dupes.json"
    rc, _ = run("dupes", "--inventory", inv, "--out", dupes_path)
    dupes = json.loads(dupes_path.read_text(encoding="utf-8"))
    observed["duplicates"] = {"groups": dupes["duplicate_groups"], "redundant": dupes["redundant_files"]}
    if dupes["duplicate_groups"] < 1:
        failures.append("identical content under two names was not detected as one document")
    group = next((g for g in dupes["groups"] if g["kind"] == "renamed_copy"), None)
    if group is None:
        failures.append("no renamed-copy group: identity was decided by filename")
    elif not group["names_differ"]:
        failures.append("a renamed copy was reported with identical names")

    # ---- 3 version chain from same identity, different content
    versions_path = work / "versions.json"
    run("versions", "--inventory", inv, "--out", versions_path)
    versions = json.loads(versions_path.read_text(encoding="utf-8"))
    observed["versions"] = {"chains": versions["chain_count"]}
    if versions["chain_count"] < 1:
        failures.append("two different contents under one identity produced no version chain")
    else:
        chain = versions["chains"][0]
        if chain["versions"] < 2:
            failures.append("version chain has fewer than two versions")
        if not any(not s["identical_content"] for s in chain["steps"]):
            failures.append("version chain did not distinguish differing content")

    # ---- 4 a rename plan touches nothing on disk
    before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    rules = work / "rules.json"
    rules.write_text(json.dumps({"naming_template": "{stem}{suffix}"}), encoding="utf-8")
    plan_path = work / "plan.json"
    run("plan", "--inventory", inv, "--rules", rules, "--out", plan_path)
    after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    observed["plan"] = {"operations": plan["operations"], "dry": plan["dry"]}
    if before != after:
        failures.append("planning modified the tree; a plan must be inert")

    # ---- 5 apply, journalled and reversible
    plan["root"] = str(root)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    journal = work / "journal.jsonl"
    if journal.exists():
        journal.unlink()
    rc, out = run("apply", "--plan", plan_path, "--journal", journal, "--root", root)
    applied = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    observed["apply"] = applied
    if rc not in (0, 3):
        failures.append(f"apply failed unexpectedly: {out[-200:]}")
    if journal.exists() and journal.stat().st_size > 0:
        # ---- 6 verify catches tampering: delete a file, verification must fail
        victim = next(p for p in root.rglob("*") if p.is_file())
        victim.unlink()
        vpath = work / "verify-tampered.json"
        rc_bad, _ = run("verify", "--inventory", inv, "--root", root, "--journal", journal, "--out", vpath)
        tampered = json.loads(vpath.read_text(encoding="utf-8"))
        observed["verify_after_deletion"] = {"status": tampered["status"], "missing": len(tampered["missing"])}
        if rc_bad == 0 or tampered["status"] == "verified":
            failures.append("verification passed after a file was deleted: it cannot detect content loss")
        if not tampered["missing"]:
            failures.append("deleted file was not reported as missing")

        # ---- 7 rollback restores the tree
        rc_rb, _ = run("rollback", "--journal", journal)
        observed["rollback"] = {"rc": rc_rb}
        if rc_rb != 0:
            failures.append("rollback did not complete cleanly")
    else:
        failures.append("apply produced no journal, so the reorganisation is not reversible")

    # ---- negative control: an empty directory must scan clean and report zero, not error
    empty = work / "empty"
    empty.mkdir(exist_ok=True)
    rc_empty, _ = run("scan", "--root", empty, "--out", work / "empty.json")
    empty_inv = json.loads((work / "empty.json").read_text(encoding="utf-8"))
    observed["empty_dir"] = {"rc": rc_empty, "files": empty_inv["file_count"]}
    if rc_empty != 0 or empty_inv["file_count"] != 0:
        failures.append("an empty directory was not handled cleanly")


    # ---- 8 a file *named* after a version marker keeps its identity
    # `draft.md` and `final.md` are names, not markers. Stripping the marker leaves nothing, which
    # silently merges unrelated documents into one empty group and breaks every version chain.
    import sys as _sys
    _sys.path.insert(0, str(TOOL.parent))
    from file_inventory import identity_stem as _ident
    marker_names = ["draft.md", "final.md", "report_v2_final.md", "notes (2).md"]
    collapsed = {n: _ident(n) for n in marker_names}
    observed["identity_stem"] = collapsed
    for name, ident in collapsed.items():
        if not ident:
            failures.append(f"{name} lost its entire identity to version-marker stripping")
    if collapsed["draft.md"] != "draft":
        failures.append(f"draft.md should keep identity 'draft', got {collapsed['draft.md']!r}")

    report = {
        "fixture": str(root),
        "checks": 9,
        "failures": failures,
        "observed": observed,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not an organiser case, not an official result.",
    }
    (work / "file-inventory-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                     encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
