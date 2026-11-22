---
name: evidence-bound-apparatus-and-route
version: 1.0.0
description: Make or edit an editable experimental-apparatus or technical-route diagram from explicit source-grounded components, connections and sequence.
---

> Path note: the evaluator installs this skill at `/skills/weekly-skill`; every `scripts/...` path below is
> relative to the directory of this `SKILL.md`. If the install path differs in a given run,
> resolve the scripts against that directory instead of the literal path.
# Evidence-bound apparatus and route diagrams

Read actual `/input/case.json`, task.md, the `apparatus_and_technical_route` workorder, original output_contract, all supplied primary sources, original diagram/source files and the stated scientific/format constraints. Complete the requested actual illustration or source-preserving edit; do not provide only design advice. Preserve case_id and original result schema; output real editable source, actual requested SVG/PDF/PNG, source-to-element mapping, limitations and `/app/output/result.json`. Do not invent a component, pipe, arrow direction, experiment, condition, material, citation, figure, source locator or successful render. An unknown connection remains visibly unresolved or omitted with an explicit explanation.

1. Inventory the supplied apparatus elements, steps, material/data/control flows, conditions, components, labels and source locators. Distinguish equipment from process steps and physical flow from data or control flow. Trace each arrow from its actual source port/process to its actual destination; preserve order, branches, feedback and uncertainty as stated. Do not infer physical piping merely from conceptual association. When the workorder is an edit, inspect and preserve the supplied actual editable original, IDs, labels and unaffected structure.
2. Create a concise evidence/element/relationship matrix from actual documents; record exact original IDs, locators, source excerpts and any unanswered contradictions. Plan the diagram layout for the actual audience and requirements. Use distinct, explicitly explained visual encodings for physical material flow, data, sequence and control when the case contains them; don't assign invented physical semantics to a line style.
3. For the narrow case of an explicit, simple orthogonal box-and-arrow route, `/skills/weekly-skill/scripts/route_svg.py` can generate an editable-text SVG and a provenance report from an independently authored normalized plan. It requires source/locator on every node and edge, explicit nodes, routed source→target boundary points, no overlapping nodes, bounded geometry and supported flow types. It cannot infer scientific correctness, verify that source locators support claims, render realistic apparatus, route arbitrary curved tubing, handle all fonts or certify readability. Use another genuinely available tool or explicitly report partial when the real case requires unsupported geometry; never present a generic box diagram as a faithful apparatus drawing.
4. For a supplied simple SVG requiring only a whole simple `<text>` replacement or explicit fill-color edit, `/skills/weekly-skill/scripts/edit_svg.py` can apply a hash-pinned, workorder-attributed edit to a new SVG and check unchanged parsed structure. It does not handle arbitrary tspan/group/edge transformations or prove visual/scientific fidelity; preserve the original and use a real editor for unsupported edits. Always verify requested technical semantics yourself.
5. Produce the actual editable SVG and requested PDF/PNG using a real available renderer; inspect every real rendered panel for clipping, text/glyph substitution, overlap, line and arrow direction, port connections, legend consistency and hierarchy. Reopen editable source and compare each node/edge with the actual source/workorder; record what was actually checked. If a renderer, font, evidence or input is missing, retain the honest useful partial graphic, list precise gaps and never claim an export or complete scientific review that didn't occur. Do not install dependencies during official evaluation.

Bundled examples/tests are synthetic interface demonstrations, not organizer cases, experimental facts, formal model scores or evidence of benchmark gains. Machine-checked geometry and source-locator presence do not establish correct science.

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
| 5 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 1 self-test suites (`tests/`) | Run `python tests/run_checks.py` (or the suite named for the engine) to reproduce every claim made in this package. |
| Worked fixtures (`examples/`) | `README.md`, `create_svg_synthetic.py`, `synthetic-plan.json`, `synthetic-source.txt` - realistic shapes you can run end to end before touching real material. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `GAIN-EVIDENCE.md`, `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and
`tests/run_checks.py` is the regression suite to run after any edit. `CHANGELOG.md` records what
changed and why. A package that fails its own checks is not a package to submit — see
`verify_package.py` in the composing repository for the pre-submission gate.
