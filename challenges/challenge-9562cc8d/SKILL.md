---
name: publication-quality-data-visualisation
description: |-
  Use when research data must become a publication-quality figure: chart type matched to the data, encoding declared in a manifest, axes and annotation checked, error bars defined, and an export that survives print.
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

1. **Produce the deliverable now** — the cleaned table, the statistics, the figure, the report — even
   if some checks are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: profile, repair what the profile names, rerun, update `result.json`.


## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference, including the data
  dictionary and `environment/resources.yaml`. Read the actual files; a column name is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only, plus the declared toolchain (`scientific-python`, `SQLite`). No network.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# 科研数据可视化 — from raw table to a figure that survives review

VISUAL_ENGINE
PROFILE_ENGINE

## What this must get right

- **The data dictionary is read before any processing.** Column semantics, units and constraints drive
  the decisions; a generic script that ignores them is the failure this track names first.
- **Missing, zero and not-applicable are three different states.** Conflating them changes every
  downstream statistic.
- **Every transformation is recorded** with the value before and after, and the input file is never
  modified.
- **The report's numbers come from the same computation as the results.** A quality report that
  disagrees with the table it describes is worse than none.
- **Assumptions behind a test are stated and checked** — sample size, normality, variance, group count —
  and an effect size plus interval accompanies every p-value. `p = 0.04` is not "proves effective".
- **Untreated problems are named.** A missing value that was left, an outlier that was kept, a query
  that failed — each is reported rather than dropped from the narrative.
- **The chart type is matched to the data's structure.** An unordered category comparison is not a pie
  chart, and a time series is not a set of side-by-side bars.
- **Axes are honest.** No truncated baseline without saying so, a log axis declared as logarithmic.
- **Error bars say what they are** — standard deviation, standard error or confidence interval — and the
  sample size behind them is available.
- **Colour survives greyscale and colour-vision deficiency**, and categories that cannot be
  distinguished are not forced into one panel.
- **The export is usable**: resolution at target size, fonts embedded, non-ASCII text rendering, and
  dimensions matching the target column width.


## What it must refuse

- **Refuse to fill a missing value without a stated rule**, and never with a column mean unless the rule
  says so and the reason is given.
- **Refuse to treat a not-detected as a zero.** "未检测" and "检测为 0" are different facts.
- **Refuse to delete an outlier silently.** Keep it, flag it with the rule, and say what was done.
- **Refuse to report a p-value as a conclusion.** Effect size, interval and assumptions come with it.
- **Refuse to claim full coverage** when a column could not be parsed, a table failed, or rows were
  dropped.
- **Refuse to invent a value the data does not contain**, and never overwrite the supplied input.
- **Refuse to report "QA passed" until visual inspection at target size has happened.** Automated
  checks are necessary and not sufficient.


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
locators, the run status and the uncertainty. A number is reported with its unit, its condition and the
rule that produced it. A value that is missing is reported as missing, a value that is zero as zero,
and a value that was not applicable as not applicable — the three are never conflated. Where a step
could not be completed, the output names the step rather than reporting a partial pass as complete.
