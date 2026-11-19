# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for
论文转学术 PPT, from the shared dependency-free template-aware deck editor (filling and cloning inside a supplied PPTX). It replaces an earlier candidate whose
primary path required a pinned `doc-forge` installation and an Office suite inside the evaluation
container; this version is standard-library only.

## Dependencies

| Component | Use |
|---|---|
| Python standard library | the entire runtime |
| LibreOffice + Poppler (optional) | PDF/PNG preview and rendered-text check |
| Pillow (optional, figure tasks) | nicer PNG text when installed; the build report says which path ran |

## Verified evidence

- The shared runtime passes its own self-test on the synthetic fixture, including its negative
  paths; see the runtime candidate's `tests/run_checks.py` output recorded in this session's report.
- The artifact this skill produces is verified by the runtime's `verify`/`check` command, which
  re-reads the produced file rather than trusting the writer.

## Boundaries

- The artifact is drawn or filled exactly as declared; unsupported elements are omitted and named.
- Layout warnings (overflow, overlap, clipping) are estimates backed by a rendered or decoded
  check; they are not typographic proof.
- Not an official score and not a substitute for scientific review.
