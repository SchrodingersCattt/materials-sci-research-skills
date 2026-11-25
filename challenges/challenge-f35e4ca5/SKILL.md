---
name: weekly-skill
description: Inspect supplied scientific figure pixels and all source tables; produce calibrated, evidence-linked results with uncertainty.
---

# Scientific figure and table reading

Read `/input/case.json`, `/input/task.md` and the actual files. This task requires the one provided original image **and every provided original table**. Inspect the image itself, not just its caption or filename; preserve source-specific panel labels, legend, axis type, ticks, units, pixel locations, error bars and the relevant figure legend. Other figures without supplied pixels are a missing-data note, not hidden work to invent. Do not turn OCR guesses into exact values, invent statistics or claim a visual check you did not perform.

1. Initialize `/app/output/result.json` early with `python3 /skills/weekly-skill/scripts/figure_tool.py init --input /input --out /app/output`. Preserve every original output-contract field and original case ID.
2. Inventory inputs and identify the actual figure and all tables. Run `python3 /skills/weekly-skill/scripts/figure_tool.py inspect --input /input --out /app/output --image materials/actual-figure.png`, replacing the example path with the actual one. The helper records image dimensions/hash and, when available, runs Tesseract OCR with pixel bounding boxes. OCR is uncertain: inspect actual pixels or a viewer and cross-check labels against the caption and tables. It is not an automatic scientific interpretation.
3. Run `python3 /skills/weekly-skill/scripts/figure_tool.py tables --input /input --out /app/output` to preserve all CSV/TSV rows and file hashes. Also read every provided table in other formats with available tools; keep table/sheet, row, column, caption and units. Do not mistake a missing value for zero, or match a figure panel to an unrelated table.
4. If a plotted point can be calibrated from real axes, create a case-specific config with the actual image, axis pixel/value pairs, scale (`linear` or positive `log`), units, exact evidence for each axis, and point pixel coordinates. Invented syntax example: `{"image":"figure.png","axes":{"x":{"pixel0":10,"value0":0,"pixel1":110,"value1":10,"scale":"linear","unit":"s","evidence":"x-axis ticks"},"y":{"pixel0":100,"value0":0,"pixel1":0,"value1":1,"scale":"linear","unit":"a.u.","evidence":"y-axis ticks"}},"points":[{"label":"A","role":"data","x":60,"y":50},{"label":"legend swatch","role":"reference","x":120,"y":20}]}`. This is an interface example, not an official case. Each inspected pixel needs `role: data` for a real plotted point/whisker or `role: reference` for a legend, axis or other non-data pixel; reference pixels retain RGB but are never converted to scientific x/y values. Run `python3 /skills/weekly-skill/scripts/figure_tool.py digitize --input /input --out /app/output --config /app/work/digitize.json`. It retains RGB at each selected pixel, calibrated x/y and one-pixel sensitivity for data points in JSON and CSV. For a categorical axis any index is only a position locator, not a measured numeric quantity. Inspect the actual plotted pixels, colors, legend, error bars and calibration; do not claim manual coordinates were automatically detected. Unsupported axes, ambiguous curves or unreported units must remain uncertain.
5. Answer every case question with a structured figure/table record, linked caption/source rows, pixel or panel locators, numerical precision, direct observations versus inference and unassessable items. Keep output paths and a truthful change record in `/app/output/result.json`, preserving all original output-contract fields. Do not claim an official score or that a statistical test exists unless the source reports it.

Requires Python 3 and ImageMagick for pixel reading, Tesseract for optional OCR, and format-specific tools for non-CSV/TSV tables. Calibration and figure interpretation require agent inspection; the helper does not detect plot types, determine statistical significance or validate scientific meaning.

## Improved calibration and uncertainty
This version prefers installed Pillow for image decoding, falling back to ImageMagick. No installation or network is necessary if either is present; report a concrete missing-decoder error otherwise.
For each numeric axis use at least two observed ticks. Where a third tick is readable, add check_ticks: [{"pixel":60,"value":5}] and tick_tolerance_px:2. The helper rejects a declared scale that disagrees with those ticks. No third tick means no independent scale validation; the report says so. Do not use a numeric calibration for categorical labels, broken axes or a different subplot/right-hand axis.
A data point may include pixel_radius (default 1), chosen from line thickness, overlap and reading uncertainty. Outputs now include asymmetric reading intervals for log axes and the maximum checked-tick pixel residual. These are digitization sensitivity bounds, NOT statistical confidence intervals or SD/SEM, and do not exhaust systematic calibration/OCR error. Central points outside the calibration span are rejected, rather than silently extrapolated.
Keep raw table values separate from digitized estimates. Preserve all original tables, including their footnotes, units and missing cells. A table can provide exact reported values only when its sample, condition and series demonstrably match the figure. Do not require a pixel-estimated number to occur in a text quotation. Record source image hash, panel, pixel coordinates, calibration, series identity and estimate status instead.
For dual axes make separate configs per series/axis. Do not assume error-bar semantics from shape. Separate visually observed trend, source-reported statistic and interpretation.
Within the case budget prioritize the supplied image AND all original tables over unnecessary replotting or ancillary figures. Save results early and retain original output_contract nesting/types. The init command is only a partial scaffold; it does not guarantee schema conformance.
Run python tests/test_calibration.py. Synthetic tests are not formal case results or evidence of a score gain.

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

## Minimal call example (synthetic - interface only, not an answer)

Row 4 of the organizer's delivery table asks for at least one set of inputs, the invocation, and a
sample output marked as an example. Everything below is **synthetic**: the case id is
`SYNTHETIC-EXAMPLE-0001`, the material invents two rows and deliberately leaves one value
absent, and the transcript under it is the **real captured output** of running these commands in this
package. It demonstrates the interface; it is not an answer to any case, and it is not a score.

### The inputs (`examples/`)

| File | What it is |
|---|---|
| `examples/case.json` | a synthetic input you can point the tool at |
| `examples/task.md` | a synthetic input you can point the tool at |
| `examples/material/synthetic-material.md` | a synthetic input you can point the tool at |


### The invocation

```bash
python "$SKILL_DIR/scripts/figure_tool.py" --help
python "$SKILL_DIR/scripts/gain_check.py" --help
```

### Sample output (real transcript from these commands)

Paths in the transcript are written `<WORKDIR>` because they differ on every machine; everything else
is exactly what the commands printed.

| Command | Exit | Output |
|---|---|---|
| `figure_tool.py --help` | 0 | `{"interface": "usage: figure_tool.py [-h] --input INPUT [--out OUT] [--image IMAGE]\n                      [--config CONFIG]\n                      {init,inspect,tables,digitize}\n\npositional argument<WORKDIR>"}` |
| `gain_check.py --help` | 0 | `{"interface": "usage: gain_check.py [-h] --source SOURCE --answer ANSWER\n                     [--baseline BASELINE] --out OUT\n\noption<WORKDIR>"}` |

This package is a single tool rather than a staged runner, so its interface is the tool's own command line. `--help` for each script is captured below, and `examples/` holds synthetic inputs to point them at.
`extract` reports how many contract keys, files and columns it found; `skeleton` lists the keys the
result must carry, including `case_id`; `plan` writes the checklist and names what to do next. On a real
case the same commands run against `/input/case.json` and `/input/task.md` unchanged - only the paths
differ, which is exactly why the example is included: it proves the interface works end to end.

The synthetic material's absent catalyst loading exists so the example shows the honest path: the
deliverable must say "not reported", and the audit fails the run if a number appears that the material
never stated.
## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 2 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 2 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `test_calibration.py`. |
| Worked fixtures (`examples/`) | `README.md`, `case.json`, `material`, `task.md` - realistic shapes you can run end to end before touching real material. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `GAIN-EVIDENCE.md`, `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and the
suites named above are the regression tests to run after any edit. `CHANGELOG.md` records what changed
and why. A package that fails its own checks is not a package to submit - the composing repository's
`verify_package.py` is the pre-submission gate.
## What this saves, measured

The rubric asks whether loading this package measurably reduces manual work, under the same input and
the same permissions. These are the numbers, and every one is reproducible by running the package -
they are counted from the shipped source, not asserted.

| What the package does automatically | Count |
|---|---|
| declared artifacts inspected per run | 6 |
| of which are content checks, not just file presence | 6 |
| distinct machine-readable reports emitted | 0 |
| conditions the package refuses to pass silently | 0 |
| self-test suites shipped | 2 |
| self-test assertions | 10 |
| adversarial negative controls in the test suite | 1 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 6 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 0 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 0 machine-readable report(s): structured JSON |
| Regression safety | none | 10 assertions in the shipped self-tests, including 1 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `calibration_check`, `claimed_numbers`, `compare`, `inspect`, `measure`, `norm_number`.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
