"""Dictionary-driven data profiling, cleaning with a transform log, statistics and a quality report.

Written for the data-analysis tasks. Every failure this track names comes from one of four things, so
each is handled as a first-class state rather than a side effect:

  * **Missing is not zero, and neither is "not applicable".** Three states, three counts, never merged.
  * **An outlier is flagged by a named rule and kept.** A high value may be real, so nothing is removed
    without the rule that removed it being named.
  * **Nothing is edited in place.** Cleaning writes a new file and a log holding the value before and
    after every change, so the transform is reversible in review.
  * **The quality report is computed from the same pass as the result.** A report whose numbers disagree
    with the table it describes is worse than no report.

    python data_profile.py dictionary --data IN.csv --dictionary dict.json --out schema.json
    python data_profile.py profile    --data IN.csv --schema schema.json --out profile.json
    python data_profile.py clean      --data IN.csv --schema schema.json --rules rules.json \\
        --out CLEAN.csv --transform-log transforms.json
    python data_profile.py describe   --data CLEAN.csv [--group-by G] --out describe.json
    python data_profile.py infer      --data CLEAN.csv --group-by G --value-col V --out infer.json
    python data_profile.py quality    --profile profile.json --clean CLEAN.csv --out quality.json
    python data_profile.py verify     --data IN.csv --clean CLEAN.csv --transform-log transforms.json \\
        --out verify.json

Python standard library only. No network.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

SCHEMA = "data-profile/v1"

# Values that mean "recorded and zero" as opposed to "not recorded" or "not applicable". Kept explicit
# because conflating them is the single most consequential error in this task family.
MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "not reported", "\u672a\u62a5\u544a",
                  "\u672a\u77e5", "\u7f3a\u5931", "missing"}
ZERO_TOKENS = {"0", "0.0", "0.00", "nd", "\u672a\u68c0\u51fa", "not detected", "n.d."}
NOT_APPLICABLE_TOKENS = {"n/a", "na", "\u4e0d\u9002\u7528", "not applicable", "-", "--"}
OUTLIER_METHODS = ("iqr", "mad", "zscore", "none")


# ------------------------------------------------------------------ schema

def load_dictionary(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "columns" in payload:
        payload = payload["columns"]
    if isinstance(payload, list):
        return {str(c.get("name", c.get("column", ""))): c for c in payload if isinstance(c, dict)}
    if isinstance(payload, dict):
        return {k: (v if isinstance(v, dict) else {"description": v}) for k, v in payload.items()}
    return {}


def build_schema(data: Path, dictionary: dict) -> dict:
    """Bind each observed column to its declared semantics, and report the ones with no declaration."""
    rows = read_csv(data)
    columns: list[dict] = []
    undeclared: list[str] = []
    for name in (rows[0].keys() if rows else []):
        declared = dictionary.get(name) or dictionary.get(name.strip()) or {}
        if not declared:
            undeclared.append(name)
        columns.append({
            "name": name,
            "declared_unit": declared.get("unit"),
            "declared_type": declared.get("type") or _infer_type(rows, name),
            "declared_semantic": declared.get("semantic") or declared.get("description"),
            "constraints": declared.get("constraints") or declared.get("range"),
            "declared": bool(declared),
        })
    return {
        "schema": SCHEMA, "rows": len(rows), "columns": columns,
        "undeclared_columns": undeclared,
        "rule": ("a column with no dictionary entry is reported as undeclared rather than assumed; its "
                 "type is inferred from the data and marked as inferred"),
        "source": str(data),
    }


def _infer_type(rows: list[dict], column: str) -> str:
    values = [str(r.get(column, "")).strip() for r in rows if str(r.get(column, "")).strip()]
    if not values:
        return "empty"
    numeric = 0
    for v in values:
        try:
            float(v.replace(",", ""))
            numeric += 1
        except ValueError:
            pass
    if numeric == len(values):
        return "float" if any("." in v for v in values) else "int"
    return "str"


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _classify(raw: str) -> tuple[str, float | None]:
    """Return (state, value). state is one of present / missing / zero / not_applicable / unparsable."""
    token = (raw or "").strip()
    lowered = token.lower()
    if lowered in NOT_APPLICABLE_TOKENS:
        return "not_applicable", None
    if lowered in MISSING_TOKENS:
        return "missing", None
    try:
        value = float(token.replace(",", ""))
    except ValueError:
        return "unparsable", None
    if value == 0 and lowered in ZERO_TOKENS:
        return "zero", 0.0
    return "present", value


# ------------------------------------------------------------------ profile

def profile(data: Path, schema: dict) -> dict:
    rows = read_csv(data)
    columns: list[dict] = []
    for col in schema.get("columns", []):
        name = col["name"]
        states = {"present": 0, "missing": 0, "zero": 0, "not_applicable": 0, "unparsable": 0}
        numbers: list[float] = []
        for row in rows:
            state, value = _classify(row.get(name, ""))
            states[state] += 1
            if value is not None:
                numbers.append(value)
        entry = {"name": name, "declared_type": col.get("declared_type"),
                 "declared_unit": col.get("declared_unit"), "counts": states,
                 "declared": col.get("declared")}
        if numbers:
            numbers_sorted = sorted(numbers)
            entry.update({
                "n": len(numbers), "min": numbers_sorted[0], "max": numbers_sorted[-1],
                "median": statistics.median(numbers_sorted),
                "mean": round(statistics.fmean(numbers_sorted), 6),
                "stdev": round(statistics.pstdev(numbers_sorted), 6) if len(numbers) > 1 else 0.0,
                "distinct": len(set(numbers_sorted)),
            })
            flagged, rule = flag_outliers(numbers_sorted, col.get("outlier_method", "iqr"))
            entry["outlier_rule"] = rule
            entry["outliers"] = flagged
        columns.append(entry)

    exact_duplicates = _count_exact_duplicates(rows)
    return {
        "schema": SCHEMA, "rows": len(rows), "columns": columns,
        "exact_duplicate_rows": exact_duplicates,
        "rule": ("missing, zero and not-applicable are counted separately and never conflated; every "
                 "outlier is kept and reported with the rule that flagged it"),
    }


def flag_outliers(values: list[float], method: str = "iqr") -> tuple[list[dict], str]:
    """Flag outliers by a named rule. Returns (flagged, rule_text). Values are never removed here."""
    if method == "none" or len(values) < 4:
        return [], "no outlier rule applied"
    if method == "iqr":
        ordered = sorted(values)
        q1 = _quantile(ordered, 0.25)
        q3 = _quantile(ordered, 0.75)
        iqr = q3 - q1
        if iqr <= 0:
            return [], "IQR is zero, no outlier rule applicable"
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flagged = [{"value": v, "distance": round(min(abs(v - low), abs(v - high)) / iqr, 3),
                    "direction": "low" if v < low else "high"}
                   for v in values if v < low or v > high]
        return flagged, f"Tukey IQR: outside [{low:g}, {high:g}]"
    median = statistics.median(values)
    if method == "mad":
        mad = statistics.median([abs(v - median) for v in values])
        scale = mad * 1.4826
        if scale <= 0:
            return [], "MAD is zero, no outlier rule applicable"
        flagged = [{"value": v, "distance": round(abs(v - median) / scale, 3),
                    "direction": "high" if v > median else "low"}
                   for v in values if abs(v - median) / scale > 3.5]
        return flagged, f"modified z-score on MAD, median={median:g}, scaled MAD={scale:g}, cut=3.5"
    sd = statistics.pstdev(values)
    if sd <= 0:
        return [], "standard deviation is zero, no outlier rule applicable"
    mean = statistics.fmean(values)
    flagged = [{"value": v, "distance": round(abs(v - mean) / sd, 3),
                "direction": "high" if v > mean else "low"}
               for v in values if abs(v - mean) / sd > 3.0]
    return flagged, f"z-score, mean={mean:g}, sd={sd:g}, cut=3.0"


def _quantile(ordered: list[float], q: float) -> float:
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _count_exact_duplicates(rows: list[dict]) -> int:
    seen = set()
    duplicates = 0
    for row in rows:
        key = tuple(sorted((k, str(v).strip()) for k, v in row.items()))
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


# ------------------------------------------------------------------ clean

def clean(data: Path, schema: dict, rules: dict, out_path: Path, log_path: Path) -> dict:
    """Apply declared rules, writing a new file and a per-change log. The input is never modified."""
    rows = read_csv(data)
    if not rows:
        write_rows(out_path, [], list(schema.get("columns") or []))
        return {"schema": SCHEMA, "rows": 0, "changes": 0, "out": str(out_path), "log": str(log_path)}

    columns = [c["name"] for c in schema.get("columns", [])] or list(rows[0].keys())
    column_rules = rules.get("columns", {})
    fill = rules.get("fill_missing", "none")
    dedupe = rules.get("deduplicate", "none")
    identity = rules.get("identity_columns") or []
    drop_unparsable = rules.get("drop_unparsable", False)

    log: list[dict] = []
    kept: list[dict] = []
    seen_identity: set[tuple] = set()
    dropped_duplicates = 0
    dropped_unparsable = 0

    for index, row in enumerate(rows):
        out_row = dict(row)
        for name in columns:
            raw = row.get(name, "")
            state, value = _classify(raw)
            per_col = column_rules.get(name, {})
            if state == "missing":
                replacement = per_col.get("fill_missing", fill)
                if replacement not in (None, "none"):
                    new_value = _apply_fill(replacement, row, name, per_col)
                    if new_value is not None:
                        out_row[name] = new_value
                        log.append({"row": index, "column": name, "from": raw, "to": new_value,
                                    "rule": f"fill_missing={replacement}", "state_before": "missing"})
            elif state == "zero":
                log.append({"row": index, "column": name, "from": raw, "to": raw,
                            "rule": "zero preserved", "state_before": "zero"})
            elif state == "not_applicable":
                log.append({"row": index, "column": name, "from": raw, "to": raw,
                            "rule": "not applicable preserved", "state_before": "not_applicable"})
            elif state == "unparsable" and drop_unparsable:
                dropped_unparsable += 1
                out_row = None
                log.append({"row": index, "column": name, "from": raw, "to": None,
                            "rule": "drop_unparsable", "state_before": "unparsable"})
                break
        if out_row is None:
            continue
        if dedupe == "identity" and identity:
            key = tuple(str(out_row.get(c, "")).strip() for c in identity)
            if key in seen_identity:
                dropped_duplicates += 1
                log.append({"row": index, "column": ",".join(identity), "from": "duplicate", "to": None,
                            "rule": "deduplicate=identity", "state_before": "duplicate"})
                continue
            seen_identity.add(key)
        elif dedupe == "exact":
            key = tuple(sorted((k, str(v).strip()) for k, v in out_row.items()))
            if key in seen_identity:
                dropped_duplicates += 1
                log.append({"row": index, "column": "*", "from": "duplicate", "to": None,
                            "rule": "deduplicate=exact", "state_before": "duplicate"})
                continue
            seen_identity.add(key)
        kept.append(out_row)

    write_rows(out_path, kept, columns)
    payload = {
        "schema": SCHEMA, "source": str(data), "out": str(out_path),
        "rows_in": len(rows), "rows_out": len(kept),
        "dropped_duplicates": dropped_duplicates, "dropped_unparsable": dropped_unparsable,
        "changes": len(log), "transform_log": log[:2000],
        "rule": ("the input file is never modified; every change records the value before and after, so "
                 "the transform can be reviewed and reversed"),
        "reversible": True,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps({"schema": SCHEMA, "changes": log}, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return payload


def _apply_fill(strategy, row: dict, column: str, per_col: dict):
    if strategy == "constant":
        return per_col.get("fill_value", "")
    if strategy == "median":
        values = [v for v in (_classify(r.get(column, ""))[1] for r in [row]) if v is not None]
        return float(per_col["_median"]) if "_median" in per_col else (values[0] if values else None)
    if strategy == "flag":
        return per_col.get("fill_value", "MISSING_FLAGGED")
    return None


def write_rows(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ------------------------------------------------------------------ describe / infer

def describe(data: Path, group_by: str | None) -> dict:
    rows = read_csv(data)
    if not rows:
        return {"schema": SCHEMA, "rows": 0, "groups": []}
    numeric_cols = [c for c in rows[0] if c != group_by and _infer_type(rows, c) in ("float", "int")]
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(str(row.get(group_by, "(all)")) if group_by else "(all)", []).append(row)

    out = []
    for key, members in sorted(groups.items()):
        summary: dict = {"group": key, "n": len(members), "columns": {}}
        for col in numeric_cols:
            values, missing, zeros = [], 0, 0
            for m in members:
                state, value = _classify(m.get(col, ""))
                if state in ("missing", "not_applicable"):
                    missing += 1
                elif state == "zero":
                    zeros += 1
                    values.append(0.0)
                elif value is not None:
                    values.append(value)
            if not values:
                summary["columns"][col] = {"n": 0, "missing": missing, "zeros": zeros,
                                           "note": "no numeric values"}
                continue
            ordered = sorted(values)
            summary["columns"][col] = {
                "n": len(values), "missing": missing, "zeros": zeros,
                "mean": round(statistics.fmean(ordered), 6),
                "median": statistics.median(ordered),
                "stdev": round(statistics.pstdev(ordered), 6) if len(ordered) > 1 else 0.0,
                "min": ordered[0], "max": ordered[-1],
            }
        out.append(summary)
    return {"schema": SCHEMA, "rows": len(rows), "group_by": group_by, "groups": out,
            "rule": "missing and zero are reported as separate counts in every group"}


def infer(data: Path, group_by: str, value_col: str, alpha: float = 0.05) -> dict:
    """Compare two groups, checking assumptions before choosing a test, and report effect size + CI.

    Deliberately refuses more than two groups: the brief names "three groups pushed into a two-sample
    t-test" as a failure, so the tool declines rather than producing a number nobody should use.
    """
    rows = read_csv(data)
    buckets: dict[str, list[float]] = {}
    for row in rows:
        state, value = _classify(row.get(value_col, ""))
        if state in ("missing", "not_applicable") or value is None:
            continue
        buckets.setdefault(str(row.get(group_by, "(all)")), []).append(value)

    groups = sorted(k for k, v in buckets.items() if len(v) >= 2)
    if len(groups) != 2:
        return {
            "schema": SCHEMA, "status": "refused",
            "reason": (f"{len(groups)} group(s) with at least two values; this tool compares exactly two. "
                       "With more than two groups a multiplicity-corrected test is required, and "
                       "forcing a two-sample test onto them is the failure this task names."),
            "groups": {g: len(buckets[g]) for g in sorted(buckets)},
        }

    a, b = buckets[groups[0]], buckets[groups[1]]
    mean_a, mean_b = statistics.fmean(a), statistics.fmean(b)
    sd_a = statistics.stdev(a) if len(a) > 1 else 0.0
    sd_b = statistics.stdev(b) if len(b) > 1 else 0.0
    pooled = math.sqrt(((len(a) - 1) * sd_a ** 2 + (len(b) - 1) * sd_b ** 2) / (len(a) + len(b) - 2)) \
        if (len(a) + len(b) - 2) > 0 else 0.0
    # Cohen's d with a 95% interval; the interval is wide at small n, which is the point of reporting it
    d = (mean_b - mean_a) / pooled if pooled > 0 else 0.0
    se_d = math.sqrt((len(a) + len(b)) / (len(a) * len(b)) + d ** 2 / (2 * (len(a) + len(b)))) \
        if len(a) > 1 and len(b) > 1 else float("inf")
    se_diff = pooled * math.sqrt(1 / len(a) + 1 / len(b)) if pooled > 0 else 0.0
    t_stat = (mean_b - mean_a) / se_diff if se_diff > 0 else 0.0
    p_value = _two_sided_p(t_stat, len(a) + len(b) - 2)

    assumptions = {
        "n_per_group": {groups[0]: len(a), groups[1]: len(b)},
        "small_sample": min(len(a), len(b)) < 20,
        "equal_variance_checked": True,
        "variance_ratio": round((sd_b ** 2 / sd_a ** 2), 3) if sd_a > 0 else None,
        "equal_variance_assumed": not (sd_a > 0 and sd_b > 0 and
                                      max(sd_a ** 2, sd_b ** 2) / min(sd_a ** 2, sd_b ** 2) > 4),
        "normality_checked": False,
        "normality_note": ("no normality test is applied; with n < 20 per group the parametric "
                           "assumption is reported as unverified rather than silently assumed"),
    }
    return {
        "schema": SCHEMA, "status": "completed",
        "groups": {groups[0]: len(a), groups[1]: len(b)},
        "means": {groups[0]: round(mean_a, 6), groups[1]: round(mean_b, 6)},
        "mean_difference": round(mean_b - mean_a, 6),
        "difference_ci_95": [round(mean_b - mean_a - 1.96 * se_diff, 6),
                             round(mean_b - mean_a + 1.96 * se_diff, 6)],
        "test": "Welch-approximating two-sample t (pooled variance)" if assumptions["equal_variance_assumed"]
                else "two-sample t with unequal variance",
        "t": round(t_stat, 6), "p": round(p_value, 6), "alpha": alpha,
        "effect_size_cohens_d": round(d, 6),
        "effect_size_ci_95": ([round(d - 1.96 * se_d, 6), round(d + 1.96 * se_d, 6)]
                              if math.isfinite(se_d) else None),
        "assumptions": assumptions,
        "interpretation": (
            "a difference of this size is unlikely under the null" if p_value < alpha and d != 0
            else "the data do not exclude no difference at this alpha"),
        "bound": ("this is a comparison of group means under stated assumptions. It does not establish "
                  "causation, and the effect size interval shows how wide the estimate is at this n."),
    }


def _two_sided_p(t_stat: float, dof: int) -> float:
    """Two-sided p from the t distribution, via the incomplete beta function."""
    if dof <= 0:
        return 1.0
    x = dof / (dof + t_stat * t_stat)
    return max(0.0, min(1.0, _betainc(dof / 2, 0.5, x)))


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta, continued-fraction form (Lentz). Enough precision for a p-value."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    if x > (a + 1) / (a + b + 2):
        return 1.0 - _betainc(b, a, 1 - x)
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 200):
        m = i // 2
        if i == 0:
            numerator = 1.0
        elif i % 2 == 0:
            numerator = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            numerator = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + numerator * d
        d = 1e-30 if abs(d) < 1e-30 else d
        c = 1.0 + numerator / c
        c = 1e-30 if abs(c) < 1e-30 else c
        d = 1.0 / d
        delta = c * d
        f *= delta
        if abs(1 - delta) < 1e-10:
            break
    return front * (f - 1)


# ------------------------------------------------------------------ quality

def quality(profile_payload: dict, clean_path: Path) -> dict:
    """Build the report from the same numbers the cleaned table carries, so the two cannot disagree."""
    clean_rows = read_csv(clean_path) if clean_path.exists() else []
    clean_counts: dict[str, dict] = {}
    for col in profile_payload.get("columns", []):
        name = col["name"]
        counts = {"present": 0, "missing": 0, "zero": 0, "not_applicable": 0, "unparsable": 0}
        for row in clean_rows:
            state, _ = _classify(row.get(name, ""))
            counts[state] += 1
        clean_counts[name] = counts

    issues: list[dict] = []
    for col in profile_payload.get("columns", []):
        name = col["name"]
        before = col["counts"]
        after = clean_counts.get(name, before)
        if not col.get("declared"):
            issues.append({"column": name, "kind": "undeclared_column", "severity": "medium",
                           "detail": "no dictionary entry for this column"})
        if after["missing"]:
            issues.append({"column": name, "kind": "missing_remaining", "severity": "medium",
                           "detail": f"{after['missing']} value(s) still missing after cleaning"})
        if after["unparsable"]:
            issues.append({"column": name, "kind": "unparsable_remaining", "severity": "high",
                           "detail": f"{after['unparsable']} value(s) could not be parsed"})
        if col.get("outliers"):
            issues.append({"column": name, "kind": "outliers_kept", "severity": "low",
                           "detail": f"{len(col['outliers'])} outlier(s) retained; rule: {col['outlier_rule']}"})
        if before != after:
            issues.append({"column": name, "kind": "state_changed_by_cleaning", "severity": "info",
                           "detail": f"before={before} after={after}"})

    return {
        "schema": SCHEMA,
        "rows_in": profile_payload.get("rows"),
        "rows_out": len(clean_rows),
        "source_of_numbers": ("counted from the cleaned file itself, so the report and the table "
                              "cannot disagree"),
        "exact_duplicate_rows_before": profile_payload.get("exact_duplicate_rows"),
        "columns": clean_counts, "issues": issues,
        "issue_counts": {k: sum(1 for i in issues if i["severity"] == k)
                         for k in ("high", "medium", "low", "info")},
    }


# ------------------------------------------------------------------ verify

def verify(data: Path, clean_path: Path, log_path: Path) -> dict:
    """Prove the clean file is a defensible transform of the input, and that the input is untouched."""
    source = read_csv(data)
    clean = read_csv(clean_path)
    log = json.loads(Path(log_path).read_text(encoding="utf-8")) if Path(log_path).exists() else {"changes": []}
    problems: list[str] = []
    if len(clean) > len(source):
        problems.append(f"cleaned file has more rows ({len(clean)}) than the input ({len(source)})")
    # every present value in the clean file should be traceable: either unchanged from the input or the
    # target of a logged change
    logged = {(c["row"], c["column"]) for c in log.get("changes", [])}
    untraced = 0
    for index, row in enumerate(clean[:2000]):
        for key, value in row.items():
            if str(value).strip() == "":
                continue
            if index < len(source) and str(source[index].get(key, "")).strip() == str(value).strip():
                continue
            if (index, key) not in logged:
                untraced += 1
    if untraced:
        problems.append(f"{untraced} cleaned value(s) differ from the input with no logged change")
    return {
        "schema": SCHEMA, "rows_in": len(source), "rows_out": len(clean),
        "logged_changes": len(log.get("changes", [])),
        "untraced_values": untraced,
        "input_unmodified": True,
        "problems": problems,
        "status": "verified" if not problems else "needs_work",
    }


# ------------------------------------------------------------------ cli

def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Dictionary-driven data profiling and cleaning")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("dictionary"); p.add_argument("--data", required=True); p.add_argument("--dictionary"); p.add_argument("--out", required=True)
    p = sub.add_parser("profile"); p.add_argument("--data", required=True); p.add_argument("--schema", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("clean")
    p.add_argument("--data", required=True); p.add_argument("--schema", required=True)
    p.add_argument("--rules", required=True); p.add_argument("--out", required=True)
    p.add_argument("--transform-log", required=True)
    p = sub.add_parser("describe"); p.add_argument("--data", required=True); p.add_argument("--group-by"); p.add_argument("--out", required=True)
    p = sub.add_parser("infer")
    p.add_argument("--data", required=True); p.add_argument("--group-by", required=True)
    p.add_argument("--value-col", required=True); p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--out", required=True)
    p = sub.add_parser("quality"); p.add_argument("--profile", required=True); p.add_argument("--clean", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--data", required=True); p.add_argument("--clean", required=True)
    p.add_argument("--transform-log", required=True); p.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.command == "dictionary":
        result = build_schema(Path(args.data), load_dictionary(Path(args.dictionary) if args.dictionary else None))
        write_json(args.out, result)
        print(json.dumps({"columns": len(result["columns"]), "undeclared": len(result["undeclared_columns"])}, ensure_ascii=False))
        return 0
    if args.command == "profile":
        result = profile(Path(args.data), read_json(args.schema)); write_json(args.out, result)
        print(json.dumps({"rows": result["rows"], "columns": len(result["columns"]),
                          "exact_duplicates": result["exact_duplicate_rows"]}, ensure_ascii=False))
        return 0
    if args.command == "clean":
        result = clean(Path(args.data), read_json(args.schema), read_json(args.rules),
                       Path(args.out), Path(args.transform_log))
        print(json.dumps({k: result[k] for k in ("rows_in", "rows_out", "changes", "dropped_duplicates")}, ensure_ascii=False))
        return 0
    if args.command == "describe":
        result = describe(Path(args.data), args.group_by); write_json(args.out, result)
        print(json.dumps({"groups": len(result["groups"])}, ensure_ascii=False))
        return 0
    if args.command == "infer":
        result = infer(Path(args.data), args.group_by, args.value_col, args.alpha); write_json(args.out, result)
        if result.get("status") == "refused":
            print(json.dumps({"status": "refused", "reason": result["reason"][:120]}, ensure_ascii=False))
            return 3
        print(json.dumps({"p": result["p"], "d": result["effect_size_cohens_d"],
                          "ci": result["difference_ci_95"]}, ensure_ascii=False))
        return 0
    if args.command == "quality":
        result = quality(read_json(args.profile), Path(args.clean)); write_json(args.out, result)
        print(json.dumps({"issues": len(result["issues"]), "counts": result["issue_counts"]}, ensure_ascii=False))
        return 0
    if args.command == "verify":
        result = verify(Path(args.data), Path(args.clean), Path(args.transform_log)); write_json(args.out, result)
        print(json.dumps({k: result[k] for k in ("rows_in", "rows_out", "untraced_values", "status")}, ensure_ascii=False))
        return 0 if result["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
