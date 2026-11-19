# Innovation and its boundary — 生物机制图与通路图

Channel: `challenge-83d4f050`.

## New capability

Two things are hard to get from a general agent or a general writing tool in one pass, and
are implemented here as named, testable checks:

1. **Declared-source closure.** Every number and qualifier in the deliverable must belong to
   a source row that was read at a recorded version, and every number found in the text must
   be declared. A general agent produces plausible numbers; it does not produce a closure
   proof, and it cannot tell you which of its numbers are undeclared.
2. **A real container, rebuilt and re-read.** The deliverable is written as genuine OOXML or
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
the fixture, and the negative paths prove the checks can fail.

`scripts/contract_check.py` — subcommands: extract, skeleton, conform, verify
`scripts/make_figure.py` — subcommands: chart, diagram, inspect-png, verify

## Boundary

The skill does not claim to judge scientific validity, statistical significance, causality or
literature entailment, and it does not replace review. Where a required construct cannot be
produced honestly, the run says so and keeps the editable source rather than substituting a
file with the right extension and the wrong content.
