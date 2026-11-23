# Provenance

## Origin

Built in the session that produced this directory (2026-11-16, Asia/Shanghai) for the period-4
图表解析 (scientific figure and table reading) challenge. The `v2` suffix marks the second revision: the
first version read a value off a plotted point without calibrating the axes, so it could report a
plausible number that the figure did not support. This revision derives the pixel-to-value mapping from
declared axis calibration points and states a reading interval rather than a single value.

## Dependencies

| Component | Use | Required |
|---|---|---|
| Python standard library | the entire runtime (`figure_tool.py`, `gain_check.py`) | yes |
| Pillow (optional) | decoding the supplied figure raster for pixel inspection | auto-detected; the report says whether it was used |
| An OCR tool (optional) | reading text when a figure carries no extractable text layer | never assumed; a missing tool is reported as a limitation |
| No network, no third-party requirement | the runtime contract forbids both | — |

## What the scripts are

| Script | Provenance | Role |
|---|---|---|
| `scripts/figure_tool.py` | written for this challenge | Reads supplied figures and tables from the real files. `source()` confines every path to the input root and refuses absolute or escaping paths, so a label cannot stand in for a file. `rgb_image` decodes the raster, `inspect` reports what is actually there, `calibration_check` validates the declared axis calibration before anything is measured, `reading_interval` converts a pixel position into a value **with its uncertainty** rather than a point estimate, `digitize` reads a plotted series, and `tables` reads the supplied tables. `merge_partial` carries earlier partial results forward, and every input and output is recorded with its SHA-256 |
| `scripts/gain_check.py` | shared across the period-4 packages | Measures a written answer against the supplied material on coverage and grounding, with a `--baseline` mode for skill-versus-baseline comparison |
| `tests/test_calibration.py` | written for this challenge | Self-test covering the calibration and reading-interval path, including an over-precise answer that must be rejected |
| `tests/gain_checks.py`, `tests/gain_cases/` | shared fixtures | Gain self-test including negative controls (fabricated answer, off-topic answer, hedge-stripped answer) that must score worse than the grounded one |

## Verified evidence

- `tests/test_calibration.py` and `tests/gain_checks.py` both pass on the synthetic fixtures in this
  directory. The gain self-test includes its negative controls, so a passing result means the comparison
  can actually discriminate, not merely that it ran.
- Calibration is checked before measurement: a declared axis that does not reproduce its own calibration
  points fails the run rather than yielding numbers.
- Every path read or written is recorded with its SHA-256, so a reviewer can confirm the recorded source
  is the source that was read.
- The `examples/` directory holds synthetic inputs and the transcript under "Minimal call example" in
  `SKILL.md` is the real captured output of running those inputs through the tools.

## Boundaries

- A digitized value is only as good as its calibration. Where the figure does not declare enough axis
  information to calibrate, the tool says so and reports an interval or refuses, rather than inventing a
  scale.
- Pixel reading is a measurement, not ground truth: sub-pixel detail, compression artifacts and
  anti-aliasing bound the precision, which is why a reading interval is reported instead of a point
  estimate.
- OCR output is treated as text to be verified against the figure, not as an authoritative value.
- Nothing here is an official score, and `GAIN-EVIDENCE.md` reports fixture measurements, not case results.
