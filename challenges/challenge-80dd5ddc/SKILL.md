---
name: knowledge-base-question-answering
description: Use when questions must be answered from a research knowledge base with citations that resolve to file, version and position, graded uncertainty, and a clear 'no basis in this library' answer when the material does not support one.
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


# 科研知识库问答 — answer from the library, with citations that resolve

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
- **Every key claim resolves to file, version and position.** A citation that points at a file but not a
  place is incomplete, and one that points at a superseded version is marked as such.
- **Uncertainty is graded and specific.** Insufficient evidence, conflicting evidence, unreadable file
  and restricted access are four different states, and each names what would resolve it.
- **"No basis in this library" is a correct answer.** The rubric scores whether the skill will say it,
  so an unsupported question must not be answered from general knowledge.


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
