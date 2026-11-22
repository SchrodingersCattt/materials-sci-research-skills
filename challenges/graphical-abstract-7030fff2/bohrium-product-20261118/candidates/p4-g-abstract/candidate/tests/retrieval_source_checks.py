"""Prove the source-bound layer of retrieval_audit behaves: planted defects fail, clean input does not.

Three capabilities were added for the source-bound search cases (`ingest`, `references`, `delta`). Each
one is checked twice: against a case that must be rejected, and against a case that must pass. A check
that only runs the good case proves nothing, so both controls are here.

    python tests/retrieval_source_checks.py [--workdir work/retrieval-source]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "retrieval_audit.py"


def run(*argv) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(TOOL), *[str(a) for a in argv]],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="work/retrieval-source")
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    observed: dict = {}

    # ---- 1 ingest: the three shapes a case actually supplies, normalised into one record shape
    crossref = {
        "message": {"items": [
            {"DOI": "10.1000/a1", "title": ["Nickel catalysts for glycerol conversion"],
             "author": [{"given": "A.", "family": "Wei"}, {"given": "B.", "family": "Liu"}],
             "issued": {"date-parts": [[2019, 4]]}, "container-title": ["J. Catal."],
             "type": "journal-article", "language": "en",
             "reference": [{"DOI": "10.1000/a2"}, {"DOI": "10.1000/z9"}]},
            {"DOI": "10.1000/a2", "title": ["Glycerol reforming: a review"],
             "issued": {"date-parts": [[2021]]}, "container-title": ["Chem. Rev."],
             "reference": [{"DOI": "10.1000/a1"}]},
        ]}}
    europepmc = {"resultList": {"result": [
        {"id": "MED-1", "doi": "10.1000/a1", "title": "Nickel catalysts for glycerol conversion",
         "authorString": "Wei A, Liu B", "pubYear": "2019", "journalTitle": "J. Catal."},
        {"id": "MED-2", "title": "A study with no identifier at all", "authorString": "Chen C",
         "pubYear": "2020", "references": ["10.1000/a2"]},
        {"id": "MED-3", "title": "An isolated work that cites nothing and is cited by nothing",
         "authorString": "Zhao D", "pubYear": "2005", "journalTitle": "Old J."},
        {"id": "MED-4", "authorString": "Nobody", "pubYear": "2001", "abstract": "a record with no title"},
    ]}}
    (work / "crossref.json").write_text(json.dumps(crossref), encoding="utf-8")
    (work / "europepmc.json").write_text(json.dumps(europepmc), encoding="utf-8")
    (work / "sources-good.json").write_text(json.dumps({"sources": [
        {"source": "crossref", "path": str(work / "crossref.json")},
        {"source": "europepmc", "path": str(work / "europepmc.json")},
    ]}), encoding="utf-8")
    rc, _ = run("ingest", "--sources", work / "sources-good.json", "--corpus", work / "corpus.csv",
                "--out", work / "ingest.json", "--state", work / "import-state.json")
    ingest = load(work / "ingest.json")
    corpus = work / "corpus.csv"
    observed["ingest"] = {"rc": rc, "status": ingest["status"], "counts": ingest["counts"]}
    header = corpus.read_text(encoding="utf-8").splitlines()[0]
    if rc != 0 or ingest["status"] != "complete":
        failures.append(f"clean source-bound corpus was rejected (rc={rc}, status={ingest['status']})")
    if not all(field in header for field in ("id", "source", "source_locator", "doi", "references")):
        failures.append(f"corpus header is missing canonical fields: {header}")
    if ingest["counts"]["records"] != 4:
        failures.append(f"expected 4 distinct records (one cross-source duplicate merged), got "
                        f"{ingest['counts']['records']}")
    if ingest["counts"]["merged_duplicates"] != 1:
        failures.append("the same DOI arriving from two sources was not merged")
    if not ingest["dropped"]:
        failures.append("a record carrying no title was not dropped and named")
    if not any("title" in row.get("reason", "") for row in ingest["dropped"]):
        failures.append("the dropped record does not say why it was dropped")

    # negative control: a declared source that is not on disk must fail rather than be skipped silently
    (work / "sources-missing.json").write_text(json.dumps({"sources": [
        {"source": "crossref", "path": str(work / "not-here.json")},
    ]}), encoding="utf-8")
    rc_bad, _ = run("ingest", "--sources", work / "sources-missing.json", "--corpus", work / "corpus-bad.csv",
                    "--out", work / "ingest-bad.json")
    bad = load(work / "ingest-bad.json")
    observed["ingest_missing_source"] = {"rc": rc_bad, "status": bad["status"]}
    if rc_bad == 0 or bad["status"] == "complete":
        failures.append("a missing declared source was accepted (false negative)")

    # negative control: an identity carrying two different titles must be reported
    clashes = {"items": [
        {"doi": "10.1000/c1", "title": "First work about membranes", "year": "2018"},
        {"DOI": "10.1000/c1", "title": "A different work sharing the DOI", "issued": {"date-parts": [[2020]]}},
    ]}
    (work / "clash.json").write_text(json.dumps(clashes), encoding="utf-8")
    (work / "sources-clash.json").write_text(json.dumps({"sources": [
        {"source": "publisher", "path": str(work / "clash.json")}]}), encoding="utf-8")
    run("ingest", "--sources", work / "sources-clash.json", "--corpus", work / "corpus-clash.csv",
        "--out", work / "ingest-clash.json")
    clash = load(work / "ingest-clash.json")
    observed["ingest_identity_clash"] = [f["dimension"] for f in clash["findings"]]
    if not any(f["dimension"] == "source_identity" for f in clash["findings"]):
        failures.append("one DOI carrying two different titles was merged silently (false negative)")

    # ---- 2 references: the retained graph, with external targets named rather than invented
    rc, _ = run("references", "--records", corpus, "--out", work / "references.json",
                "--state", work / "import-state.json")
    refs = load(work / "references.json")
    observed["references"] = {"rc": rc, "status": refs["status"], "internal": refs["internal_edges"],
                              "external": refs["external_edges"], "isolated": refs["isolated"]}
    if rc != 0 or refs["status"] != "complete":
        failures.append(f"a retained reference graph was rejected (rc={rc}, status={refs['status']})")
    if refs["internal_edges"] < 2:
        failures.append(f"in-corpus citations were not retained (internal edges={refs['internal_edges']})")
    if refs["external_edges"] < 1:
        failures.append("a citation to a work outside the corpus was not kept as external")
    if not all(edge.get("evidence") for edge in refs["graph"]):
        failures.append("a graph edge carries no locator, so the edge cannot be re-derived")
    if not refs["isolated"]:
        failures.append("a record that neither cites nor is cited was not reported as isolated")

    # negative control: a corpus that states no references must not look like a graph
    work_records = work / "no-refs.csv"
    work_records.write_text(
        "id,source,source_locator,title,authors,year,journal,doi,abstract,type,language,references\n"
        "10.1000/n1,corpus,corpus#/0,One paper,,2020,,10.1000/n1,,,en,[]\n"
        "10.1000/n2,corpus,corpus#/1,Another paper,,2021,,10.1000/n2,,,en,[]\n",
        encoding="utf-8")
    rc_nr, _ = run("references", "--records", work_records, "--out", work / "references-none.json")
    none = load(work / "references-none.json")
    observed["references_none"] = {"rc": rc_nr, "status": none["status"]}
    if rc_nr == 0 or none["status"] == "complete":
        failures.append("a corpus stating no reference lists was accepted as a retained graph (false negative)")

    # ---- 3 delta: resuming an import reports what is new, changed and gone
    before = work / "state-before.csv"
    after = work / "state-after.csv"
    cols = "id,source,source_locator,title,authors,year,journal,doi,abstract,type,language,references\n"
    before.write_text(cols +
                      "10.1000/a1,corpus,c#/0,Nickel catalysts for glycerol conversion,Wei A,2019,J,10.1000/a1,,,en,[]\n"
                      "10.1000/a2,corpus,c#/1,Glycerol reforming: a review,Liu B,2021,C,10.1000/a2,,,en,[]\n",
                      encoding="utf-8")
    after.write_text(cols +
                     "10.1000/a1,corpus,c#/0,Nickel catalysts for glycerol conversion at high loading,Wei A,2019,J,10.1000/a1,,,en,[]\n"
                     "10.1000/a3,corpus,c#/2,A newly imported study,Chen C,2022,N,10.1000/a3,,,en,[]\n",
                     encoding="utf-8")
    rc, _ = run("delta", "--previous", before, "--current", after, "--out", work / "delta.json",
                "--state", work / "import-state.json")
    delta = load(work / "delta.json")
    observed["delta"] = {"rc": rc, "status": delta["status"], "added": delta["added"],
                         "changed": [c["id"] for c in delta["changed"]], "removed": delta["removed"]}
    if rc != 0 or delta["status"] != "complete":
        failures.append(f"a resumable import was rejected (rc={rc}, status={delta['status']})")
    if delta["added"] != ["10.1000/a3"]:
        failures.append(f"the new record was not identified as added: {delta['added']}")
    if [c["id"] for c in delta["changed"]] != ["10.1000/a1"]:
        failures.append(f"a record changed under a stable identity was not reported as changed: {delta['changed']}")
    if delta["removed"] != ["10.1000/a2"]:
        failures.append(f"a record that disappeared was not reported as removed: {delta['removed']}")
    if delta["changed"] and "title" not in delta["changed"][0]["fields"]:
        failures.append("the change record does not name the field that changed")
    if "resumed_from" not in (delta.get("state") or {}):
        failures.append("the import state was not carried forward, so the next run cannot resume")

    # negative control: two different works under one identity must be reported, not averaged
    clash_state = work / "state-clash.csv"
    clash_state.write_text(cols +
                           "10.1000/c1,corpus,c#/0,First work about membranes,X,2018,M,10.1000/c1,,,en,[]\n"
                           "10.1000/c1,corpus,c#/1,A different work sharing the identity,Y,2020,M,10.1000/c1,,,en,[]\n",
                           encoding="utf-8")
    rc_cl, _ = run("delta", "--previous", before, "--current", clash_state, "--out", work / "delta-clash.json")
    clash_delta = load(work / "delta-clash.json")
    observed["delta_identity_clash"] = {"rc": rc_cl, "status": clash_delta["status"]}
    if rc_cl == 0 or clash_delta["status"] == "complete":
        failures.append("an identity collision was resumed instead of reported (false negative)")

    report = {"tool": "retrieval_audit.py", "checks": 17, "observed": observed,
              "verdict": "pass" if not failures else "fail", "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
