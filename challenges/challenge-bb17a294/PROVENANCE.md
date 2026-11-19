# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for
写作12｜学术翻译与双语写作, from the shared dependency-free runtime that replaces the earlier
`doc-forge`-dependent primary path. The number audit and the OOXML writers are
standard-library only; a renderer is optional and reported honestly when absent.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`zipfile`, `csv`, `decimal`, `hashlib`, `json`, `re`, `subprocess`, `shutil`) | the entire runtime |
| the OOXML wordprocessingML / presentationML part layout | written and re-read directly |
| LibreOffice + Poppler (optional) | PDF/PNG preview and font report only |

The ledger-and-hash method follows the approach of the MIT-licensed
[doc-forge](https://github.com/SchrodingersCattt/doc-forge) project (commit
`1fa02b08aea33debb3cc9fb1b5af138dd7e9b006`): a small auditable ledger instead of a silent
conversion. No doc-forge source is vendored, imported or required.

## Verified evidence

- Self-test on the shared synthetic fixture: positive path passes, negative paths are rejected (recorded in the session report).

All fixture content is invented for interface testing. No formal case, hidden material or
official score was used to build or validate this skill.

## Boundaries

- The audit is a source-boundary and prose-agreement instrument, not a scientific verdict.
- The writers cover text, tables and lists; unsupported constructs are reported, not dropped.
- Resource budget observed: within the 50-file / 500 KB-per-file / 2 MB-total skill limits.
