---
name: literature-screening-and-ranking
description: |-
  Use when candidate records must be screened and ranked: a stated relevance basis per record, ranking on declared fields, and uncertain cases kept uncertain rather than forced.
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

1. **Produce the deliverable now** — the screening record, the included set, the evidence table — even
   if some fields are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: reconcile the counts, repair what the reconciliation names, rerun, update.


## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference, including the corpus
  and `environment/resources.yaml`. Read the actual files; a title is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only. **No network** — every source is supplied in the case.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# screen and rank candidates by relevance with stated grounds

## Engine

`scripts/retrieval_audit.py` — the retrieval record, made mechanical.

```bash
python "$SKILL_DIR/scripts/retrieval_audit.py" query     --question work/q.txt \
    --strategy work/strategy.json --out work/query.json
python "$SKILL_DIR/scripts/retrieval_audit.py" screen    --records work/corpus.csv \
    --criteria work/criteria.json --out work/screening.json
python "$SKILL_DIR/scripts/retrieval_audit.py" reconcile --screening work/screening.json --out work/counts.json
python "$SKILL_DIR/scripts/retrieval_audit.py" coverage  --records work/corpus.csv --query work/query.json \
    --out work/coverage.json
python "$SKILL_DIR/scripts/retrieval_audit.py" appraise  --records work/included.csv --scale work/scale.json \
    --out work/appraisal.json
python "$SKILL_DIR/scripts/retrieval_audit.py" synonyms  --terms work/terms.json --out work/synonyms.json
python "$SKILL_DIR/scripts/retrieval_audit.py" verify    --screening work/screening.json --out work/verify.json
```

- **`query`** turns a question into blocks that each state their **intent** and their field, plus explicit
  language and date limits. A block with no stated intent is a finding, because it cannot be reviewed or
  deliberately removed later.
- **`screen`** applies criteria and keeps a per-record reason. A criterion that **cannot be adjudicated**
  — "relevant", "interesting", "重要" with no bound — is a high-severity finding, because two reviewers
  would split on the same record.
- **`reconcile`** checks the stage counts against the **declared** record count, so a record lost between
  retrieval and screening is reported rather than absorbed.
- **`coverage`** states the **bound**: what the corpus and the declared limits could not include, and
  therefore what the conclusion does not extend to.
- **`appraise`** grades a study dimension by dimension against stated markers and carries the grade into
  a **weight**, so a low-quality study does not count equally with a strong one. With no scale supplied
  it refuses rather than inventing one.
- **`synonyms`** builds cross-language sets and records every translation that was applied, so a match
  from a mapping is distinguishable from a match in the text.
- **`verify`** proves the included set is recomputable from the record alone — the test the briefs state.

`scripts/file_inventory.py` supplies corpus discovery: hashing, content-based de-duplication and version
chains, so a duplicate copy is not counted as independent evidence.


## What this must get right

- **Every decision names the criterion that produced it.** An inclusion or exclusion with no reason is
  the failure this track names first.
- **Criteria are adjudicable.** A property plus a bound, not an adjective. "Sample size at least 10",
  not "relevant".
- **The counts reconcile across stages**, and a record lost between them is reported rather than
  absorbed into the total.
- **The conclusion is bounded.** What the corpus and the limits could not include is stated, so a
  finding is not extended past its evidence.
- **A duplicate is not independent evidence.** Content-hash identity decides this, not the filename.
- **Cross-language matches are recorded as translations**, so a reviewer can see the match came from a
  mapping.
- **Uncertain records are kept as uncertain.** A record that only partly satisfies the criteria is
  reported as uncertain, not forced into include or exclude.


## What it must refuse

- **Refuse to invent a source, a citation, a year or a DOI.** A field the corpus does not supply is
  `not reported`.
- **Refuse to assert novelty or absence from a partial corpus.** "No work has done X" is unprovable from
  the material supplied and must not be claimed.
- **Refuse to relax a criterion to reach a result.** If a filter cannot be satisfied, say so.
- **Refuse to present an included set with no screening record**, and never silently drop a record.
- **Refuse to appraise without a stated scale.** Grades with no scale cannot be interpreted.
- **Refuse to treat a preprint and its published version as interchangeable** without saying so.


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

Each case returns a structured result holding the input identifier, the main result, the evidence
locators, the run status and the uncertainty. Every retrieval finding names the source it came from and
the position within it. A record that was excluded names the criterion and the reason. A statement the
corpus does not support is reported as unsupported rather than softened, and the run states which part
of the corpus it did not cover.
