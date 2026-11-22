# Innovation and its boundary — 学术格式与模板适配

Channel: `challenge-96263d10`.

## New capability

Three things are hard to get from a general agent or a general writing tool in one pass, and
are implemented here as named, testable checks:

1. **A linked caption/cross-reference apparatus.** The organizer's own list of capabilities a base
   agent does not have names 图表题注与交叉引用联动更新. This skill reads the caption labels a
   document declares, the position each one holds in the sequence of its family, and every in-text
   reference to a figure, table or equation; it then updates a caption number **and** the references
   that point at it in one pass, or refuses with a reason when the document does not determine the
   answer (two captions would collide, a reference points at a caption that never existed, a label
   carries a tab so the digit span cannot be addressed). It reports unchanged layout conventions it
   cannot judge - a figure caption above its figure, a table caption below its table - as
   observations for the template to settle, not as defects.
2. **Declared-source closure.** Every number and qualifier in the deliverable must belong to
   a source row that was read at a recorded version, and every number found in the text must
   be declared. A general agent produces plausible numbers; it does not produce a closure
   proof, and it cannot tell you which of its numbers are undeclared.
3. **A real container, rebuilt and re-read.** The deliverable is written as genuine OOXML or
   as vector/bitmap output with a hash manifest, then re-opened and checked against the
   source text, so "the file exists" and "the file contains the verified text" are two
   different, separately reported facts.

## Method change versus the alternatives

| Alternative | What it does | Where it stops | What this skill adds |
|---|---|---|---|
| Base agent alone | drafts fluent text from the material | no closure of numbers to sources,
no artifact verification, no failure taxonomy | an audit pass with named checks and a
repair loop keyed to check ids |
| General writing tools | template and style assistance | not source-bound, no evidence map,
no reject-list | the same text with a source locator per claim and an explicit reject-list |
| Manual workflow | correct but slow | every number rechecked by eye | the same checks
executed by a script that returns the failing check id |

## Evidence

The evidence is the check list itself, not a narrative: it ships in the runtime, it runs on
the fixture, and the negative paths prove the checks can fail. For the apparatus audit the
controls are a defective and a clean copy of the same realistic-size manuscript, so the
positive control shows which defects are caught (`caption_number_out_of_sequence`,
`cross_reference_dangling`, `reference_entry_duplicated`,
`reference_numbering_not_monotonic`) and the negative control shows the audit does not
false-alarm on correct input.

`scripts/adapt_template.py` — subcommands: inspect, specify, apply, verify, linkage, preview
`scripts/contract_check.py` — subcommands: extract, skeleton, conform, verify
`tests/linkage_checks.py` — the true-positive/true-negative control for the apparatus audit

## Boundary

The skill does not claim to judge scientific validity, statistical significance, causality or
literature entailment, and it does not replace review. It also does not decide which layout
convention a template wants: when a caption sits on the other side of its object than the default
assumes, that is reported as an observation. Where a required construct cannot be produced
honestly, the run says so and keeps the editable source rather than substituting a file with the
right extension and the wrong content.
