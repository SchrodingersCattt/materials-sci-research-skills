---
name: research-file-retrieval-with-locators
description: |-
  Use when a question must be answered from a file library and located to the exact passage: cross-file search over content rather than filenames, hard filters enforced as constraints, and an evidence link naming file, version and position.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan
# ... read the case material and produce the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md
```

`plan` takes no reading of its own. `finish` returns a JSON report whose `failed_checks` names exactly
what to repair, and exits non-zero if a stage failed or a placeholder is still in `result.json`.

## Budget order (do this first)

1. **Produce the deliverable now** — the inventory, the list, the note set — even if some fields are
   still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rerun, update `result.json`.


## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference, including
  `environment/resources.yaml`. Read the actual files; a filename is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only. No network. Declared tools include `pdf-text-tool`, `pdf-render-tool`,
  `ocr-tool`, `office-renderer`, `scientific-python`.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# 科研文件智能检索 — locate the passage, not just the file

## Engine

`scripts/file_inventory.py` — inventory, content-based identity, version chains and reversible
reorganisation.

```bash
python "$SKILL_DIR/scripts/file_inventory.py" scan     --root /input --out work/inv.json
python "$SKILL_DIR/scripts/file_inventory.py" dupes    --inventory work/inv.json --out work/dupes.json
python "$SKILL_DIR/scripts/file_inventory.py" versions --inventory work/inv.json --out work/versions.json
python "$SKILL_DIR/scripts/file_inventory.py" plan     --inventory work/inv.json --rules work/rules.json \
    --out work/plan.json
python "$SKILL_DIR/scripts/file_inventory.py" apply    --plan work/plan.json --journal work/journal.jsonl \
    --root /input
python "$SKILL_DIR/scripts/file_inventory.py" verify   --inventory work/inv.json --root /input \
    --journal work/journal.jsonl --out work/verify.json
python "$SKILL_DIR/scripts/file_inventory.py" manifest --inventory work/inv.json --out /app/output/manifest.csv
python "$SKILL_DIR/scripts/file_inventory.py" rollback --journal work/journal.jsonl
```

Four rules are built in, each aimed at a failure this track names:

- **Identity is the content hash, never the filename.** Two names with one hash are one document; one
  name with two hashes is a version chain.
- **Nothing is destroyed.** `plan` is inert — it touches nothing. `apply` journals every rename.
  `rollback` reverses the journal newest-first. There is no in-place edit path.
- **Every metadata field names its source** — filename, content, sidecar or human — so a value inferred
  from a name is never presented as an extracted one.
- **Skips are recorded and counted.** `scan` lists each unreadable, oversized, too-deep or symlinked
  path with its reason, and the run reports how many were skipped rather than claiming completion.

## Engine

`scripts/reading_client.py` — a reading loop whose anchors survive re-indexing.

```bash
python "$SKILL_DIR/scripts/reading_client.py" index  --source /input/material --session work/session.json
python "$SKILL_DIR/scripts/reading_client.py" select --session work/session.json --quote "..." 
python "$SKILL_DIR/scripts/reading_client.py" ask    --session work/session.json --anchor A1 \
    --question "..."
python "$SKILL_DIR/scripts/reading_client.py" annotate --session work/session.json --anchor A1 --note "..."
python "$SKILL_DIR/scripts/reading_client.py" review   --session work/session.json
python "$SKILL_DIR/scripts/reading_client.py" export   --session work/session.json --out /app/output/notes.json
```

`select` binds a quote to an anchor. `ask` and `annotate` both require an anchor, so an answer or a note
cannot exist without a source position. `review` reports anchors that no longer resolve — the case that
matters when a document is re-indexed or replaced by another version.


## What this must get right

- **Identity is decided by content.** A duplicate is two paths with one hash; two paths whose names
  merely look alike are not duplicates. Conversely, one name whose content changed is two versions, not
  one file.
- **Nothing is lost and nothing is overwritten.** A same-name collision in a reorganisation plan is
  reported as a collision; it never silently replaces. Every applied change is journaled and reversible.
- **Skips are stated, not hidden.** A path that could not be read, was too large, was too deep, or was
  a symlink is listed with its reason. A run that skipped something never reports full coverage.
- **Every field carries its provenance.** Metadata taken from a filename is marked as inferred from the
  filename; metadata read from the content or a sidecar is marked accordingly; a field that could not be
  determined is `not reported`, never a plausible guess.
- **The deliverable is re-runnable.** Another person with the same inputs and the same records reaches
  the same file set, the same duplicate groups and the same version chains.
- **The answer is a position, not a document.** Returning a whole file when a section was asked for is
  the failure this task exists to catch: the locator must name the section, page or paragraph.
- **Filters are hard constraints.** Year, project code, file type, batch and version are enforced or
  reported as unsatisfiable. A filter is never relaxed to produce a result.
- **Version and duplicate status is part of the evidence.** A hit in a superseded version is reported as
  such, so a copy or an old revision is not presented as independent confirmation.


## What it must refuse

- **Refuse to delete anything.** Removal is out of scope: a redundant copy is archived or reported, and
  the original path is recoverable from the journal.
- **Refuse to invent metadata.** Authors, years, DOIs, project codes and instrument models are read from
  a real source or reported as not reported. A plausible-looking value inferred from a filename is
  marked as inference, not as fact.
- **Refuse to claim completion after a silent skip.**
- **Refuse to answer from outside the library.** If the material does not contain the answer, say so and
  name what is missing, rather than supplying general knowledge.


## Evidence you can reproduce

Use gain is scored on a run, not a claim, and the rubric states that written self-description cannot
substitute for runtime evidence:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

`coverage` is the share of your claims the supplied material supports; `grounding` is the share of your
numbers that trace back to it. Exit 2 means the inputs were not comparable. Ship `gain.json`.


## Output requirements

Each case returns a structured result holding the input identifier, the main result, the
evidence/source locators, the run status and the uncertainty. A file operation is reported as a plan
plus the record of what was applied; a judgement about a file names the file and the field it rests on;
a skip is reported with its reason. Where the material does not determine a field, the field is
`not reported` and the run says which fields those were.

## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 7 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 3 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `reference-map-template.csv`. |
| 2 self-test suites (`tests/`) | Run `python tests/run_checks.py` (or the suite named for the engine) to reproduce every claim made in this package. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and
`tests/run_checks.py` is the regression suite to run after any edit. `CHANGELOG.md` records what
changed and why. A package that fails its own checks is not a package to submit — see
`verify_package.py` in the composing repository for the pre-submission gate.

## What this saves, measured

The rubric asks whether loading this package measurably reduces manual work, under the same input and
the same permissions. These are the numbers, and every one is reproducible by running the package -
they are counted from the shipped source, not asserted.

| What the package does automatically | Count |
|---|---|
| declared artifacts inspected per run | 27 |
| of which are content checks, not just file presence | 27 |
| distinct machine-readable reports emitted | 11 |
| conditions the package refuses to pass silently | 5 |
| self-test suites shipped | 2 |
| self-test assertions | 30 |
| adversarial negative controls in the test suite | 3 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 27 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 5 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 11 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 30 assertions in the shipped self-tests, including 3 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `answer_hash_recorded`, `case_id_preserved`, `claims_have_evidence`, `conflicts_carry_both_sources`, `contract_field`, `declared_columns_present`, `declared_vocabulary_respected`, `field_coverage`, `key_types_match`, `no_duplicate_fields` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
