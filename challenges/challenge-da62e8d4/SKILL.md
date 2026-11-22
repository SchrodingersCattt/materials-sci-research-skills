---
name: weekly-skill
description: Run the supplied numerical reproduction methods and report source-bound parameters, actual outputs, tolerances and limitations.
---

# Evidence-bound numerical reproduction

This version addresses the supplied parameter/code/metric verification case. Read `/input/case.json`, `/input/task.md`, every actual supplied method, data, reference, tolerance and source statement. The organizer's synthetic run is not author code, a physical experiment or a complete original-paper reproduction. Do not invent missing originals, datasets, baselines, environments or results.

1. Initialize early: `python3 /skills/weekly-skill/scripts/repro_tool.py init --input /input --out /app/output`. Preserve every original output-contract field and case identifier.
2. Inventory and hash the real files. Locate the actual two candidate methods, inputs, parameters, references, source metadata and *predeclared* tolerances. Compare paper, organizer and code settings; state conflicts and missing original repositories/data. Inspect the scripts and determine their real argument and input requirements. Record which parameters were explicitly supplied and which are assumptions. Do not change a tolerance after seeing the output.
3. Write a runtime plan `/app/work/repro-plan.json` such as the invented interface example `{"runs":[{"id":"method-a","script":"materials/method.py","cwd":"materials","args":["--seed","7"],"timeout_seconds":120}]}`. The script path is relative to `/input`, cwd and data paths refer to the work copy, and args are passed as separate strings, never shell text. Include both supplied methods and the case-specified settings. Example is invented, not an official answer.
4. Run `python3 /skills/weekly-skill/scripts/repro_tool.py run --input /input --work /app/work --out /app/output --plan /app/work/repro-plan.json`. It copies actual input to a fresh work directory, executes case-supplied Python scripts, and records exact command, exit, elapsed time, Python/platform versions, script hash, raw stdout/stderr and timeouts. Inspect all actual outputs and generated data under `/app/work/case-copies/run-N`. A successful exit is not numerical agreement. If dependencies, code, data or execution are missing, keep a partial result and record the exact failure; never fabricate a run.
5. Use the input's metric definitions and predeclared tolerance to compare actual results against reference values. Optional `compare` command consumes a JSON array with `metric`, numeric `reference`, `observed`, `absolute_tolerance`, and exact `reference_source`, `observed_source`, `tolerance_source` strings; it writes numeric deltas and within-tolerance flags. A fabricated tolerance or reference is forbidden. Preserve original raw logs and evidence in the result. Explain numerical differences with evidence and separate verified causes from possibilities.
6. Finalize `/app/output/result.json` with all original required fields, source locations and hashes, observed method results, commands/logs, environment, parameter choices, comparison, missing originals, clear uncertainty, change record and honest status. Copy any relevant generated artifacts under `/app/output`. Use the input case ID. Do not claim an official score or independent validation.

Requires Python 3 standard library and whatever dependencies the supplied methods themselves require. No external packages are installed by this helper; it does not prove that a script implements the paper's method, that output-derived metrics are semantically comparable, or that exact source quotes entail the conclusions.


## v2 controlled execution
Each method and repeat uses its own fresh input copy. Never reuse another method's mutated inputs as a fair comparison. Entire plan paths/arguments/timeouts are validated before executing any method. Existing execution records or logs are refused rather than overwritten; use fresh directories for a new run. Records are checkpointed after each completed method so a later failure does not erase earlier evidence. File isolation is NOT a security sandbox: inspect supplied code before execution and respect the platform's execution permissions. Raw stdout/stderr are capped at 1 MB per stream, with original byte counts and truncation flags. Timed-out descendants and unrestricted network/file access require an actual sandbox when untrusted code is involved.

<!-- gain-evidence:begin -->
## Evidence you can reproduce (do this before you finish)

The comparison this channel scores under 使用增益 and 创新增益 is measurable, so measure it
instead of describing it. After the deliverable exists:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

It reports `coverage` (how many of your claims the supplied material supports) and
`grounding` (how many of your numbers trace back to it), and with `--baseline` a
skill-versus-baseline delta on the same material. Exit 2 means the inputs were not
comparable - fix the inputs, do not read it as a pass. Put the resulting `gain.json` in the
output directory: it is runtime evidence the reviewer can re-run, which prose cannot replace.
<!-- gain-evidence:end -->

## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 2 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 2 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `test_v2.py`. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `GAIN-EVIDENCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and the
suites named above are the regression tests to run after any edit. `CHANGELOG.md` records what changed
and why. A package that fails its own checks is not a package to submit - the composing repository's
`verify_package.py` is the pre-submission gate.
