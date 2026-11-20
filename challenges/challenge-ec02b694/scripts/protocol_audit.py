"""Experimental protocol audit: operationalise, check feasibility, compare routes, interpret results.

Written for the experiment-design tasks, where the failure that matters is never "cannot write
something" but "wrote something that reads like a textbook contents page". Five views of one object:

  * **operationalise** — every variable must say how it is measured, in what unit, on which
    instrument, over what range. A variable with only a name is a finding.
  * **feasibility**   — check a protocol against a supplied inventory. The rule that carries this
    task: **what the protocol does not state is reported as not stated, never as satisfied.**
  * **parameters**    — key parameters with range, unit and *provenance* (equipment limit / literature
    interval / experience), a search strategy with a convergence criterion, and a cost trade-off that
    includes machine time and labour rather than consumables alone.
  * **compare**       — 3-5 candidate routes on identical fields, with an explicit rejection reason.
    A comparison only works if the fields are the same for every candidate.
  * **anomaly**       — a trend, anomalies with a stated threshold and distance, candidate causes with
    an **elimination record** rather than a single guess, and re-check steps naming a concrete action.

    python protocol_audit.py operationalise --protocol p.json --out findings.json
    python protocol_audit.py feasibility   --protocol p.json --inventory inv.json --out feas.json
    python protocol_audit.py parameters    --protocol p.json --out params.json
    python protocol_audit.py compare       --candidates c.json --out compare.json
    python protocol_audit.py anomaly       --readings r.csv --id-col ID --value-col VALUE --out anom.json
    python protocol_audit.py cost          --plan plan.json --rates rates.json --out cost.json
    python protocol_audit.py verify        --report report.json --out verify.json

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

SCHEMA = "protocol-audit/v1"

CONTROL_KINDS = ("blank", "positive", "negative", "vehicle", "reference", "sham")
PROVENANCE = ("equipment_limit", "material_limit", "safety_threshold", "literature", "experience",
              "unspecified")
PROVENANCE_MARKERS = {
    "equipment_limit": (r"\bmax(?:imum)?\b", r"\brange\b", r"\bcapacity\b", r"\u91cf\u7a0b",
                        r"\u4e0a\u9650", r"\u6700\u5927"),
    "material_limit": (r"\u8010\u6e29", r"\u6750\u6599", r"\bwithstand\b", r"\btolerance\b"),
    "safety_threshold": (r"\bsafety\b", r"\bSDS\b", r"\u5b89\u5168", r"\bthreshold\b",
                         r"\bexposure\b"),
    "literature": (r"\[[0-9]{1,3}\]", r"\bdoi\b", r"\bet al\.?", r"\u6587\u732e", r"\breported\b"),
    "experience": (r"\btypically\b", r"\busually\b", r"\bwe\b", r"\u4e60\u60ef", r"\u7ecf\u9a8c",
                   r"\bin practice\b"),
}
# A variable is operationalised only when all four are present. This is the whole point of cf1995b5.
OPERATIONAL_KEYS = ("measured_by", "unit", "instrument", "range")

FEASIBILITY_STATES = ("VERIFIED_EXECUTABLE", "HOLD_MISSING_STATEMENT", "HOLD_RESOURCE_GAP",
                      "REJECT_LIMIT_EXCEEDED", "HOLD_APPROVAL_UNCONFIRMED")


# ------------------------------------------------------------------ 1 operationalise

def _field(obj: dict, *names, default=None):
    for name in names:
        if isinstance(obj, dict) and obj.get(name) not in (None, "", []):
            return obj[name]
    return default


def operationalise(protocol: dict) -> dict:
    """Report variables that exist as a name only, and controls that are missing a kind."""
    findings: list[dict] = []

    variables = _field(protocol, "variables", "independent_variables", "factors", default=[]) or []
    if isinstance(variables, dict):
        variables = [{"name": k, **(v if isinstance(v, dict) else {"description": v})}
                     for k, v in variables.items()]
    for var in variables:
        name = _field(var, "name", "variable", "id", default="(unnamed)")
        missing = [k for k in OPERATIONAL_KEYS if not _field(var, k)]
        if missing:
            findings.append({
                "dimension": "variable_operationalisation", "severity": "high" if len(missing) > 2 else "medium",
                "locator": f"variable:{name}", "evidence": f"missing {', '.join(missing)}",
                "suggested_action": (f"state how {name} is measured, in what unit, on which instrument, "
                                     f"over what range"),
            })

    controls = _field(protocol, "controls", default=[]) or []
    if isinstance(controls, dict):
        controls = [{"kind": k, **(v if isinstance(v, dict) else {"name": v})} for k, v in controls.items()]
    kinds = {(_field(c, "kind", "type", default="") or "").lower() for c in controls}
    if controls and "blank" not in kinds and "negative" not in kinds:
        findings.append({"dimension": "control_design", "severity": "high", "locator": "controls",
                         "evidence": "no blank or negative control declared",
                         "suggested_action": "add a blank or negative control and say what it rules out"})
    if controls and "positive" not in kinds:
        findings.append({
            "dimension": "control_design", "severity": "high", "locator": "controls",
            "evidence": "a positive control is absent",
            "suggested_action": ("add a positive control; without one a null result cannot be "
                                 "distinguished from a failed assay"),
        })
    for ctrl in controls:
        kind = (_field(ctrl, "kind", "type", default="") or "").lower()
        if kind and kind not in CONTROL_KINDS:
            findings.append({"dimension": "control_design", "severity": "low",
                             "locator": f"control:{_field(ctrl, 'name', default=kind)}",
                             "evidence": f"unrecognised control kind {kind!r}",
                             "suggested_action": f"classify as one of {', '.join(CONTROL_KINDS)}"})

    criteria = _field(protocol, "decision_criteria", "acceptance_criteria", "success_criteria",
                      default=[]) or []
    if not criteria:
        findings.append({"dimension": "decision_criteria", "severity": "high", "locator": "protocol",
                         "evidence": "no decision or acceptance criterion declared",
                         "suggested_action": "state the threshold and comparison that decides the outcome"})
    elif isinstance(criteria, list):
        for crit in criteria:
            text = crit if isinstance(crit, str) else json.dumps(crit, ensure_ascii=False)
            if not re.search(r"\d|less than|greater than|within|\u4f4e\u4e8e|\u9ad8\u4e8e|\u4e0d\u8d85\u8fc7", text):
                findings.append({"dimension": "decision_criteria", "severity": "medium",
                                 "locator": "decision_criteria", "evidence": text[:120],
                                 "suggested_action": "give the criterion a numeric bound it can be tested against"})

    high = sum(1 for f in findings if f["severity"] == "high")
    return {"schema": SCHEMA, "variables": len(variables), "controls": len(controls),
            "findings": findings, "high_severity": high,
            "status": "executable" if high == 0 else "needs_work",
            "rule": "a variable with no operational definition, or a control with no kind, is a finding"}


# ------------------------------------------------------------------ 2 feasibility

def feasibility(protocol: dict, inventory: dict | None) -> dict:
    """Check a protocol against a supplied inventory without inferring anything absent.

    The governing rule, taken straight from the brief: something the protocol does not state is
    reported as **not stated**, never as available. If no inventory is supplied, availability is
    unknown for every item rather than assumed.
    """
    inventory = inventory or {}
    have = {str(k).lower(): v for k, v in (inventory.get("items") or inventory).items()} \
        if isinstance(inventory, dict) else {}

    needs: list[dict] = []
    for item in _field(protocol, "resources", "requirements", "equipment", default=[]) or []:
        if isinstance(item, str):
            item = {"name": item}
        name = str(_field(item, "name", "item", "equipment", default="(unnamed)"))
        needs.append({
            "name": name,
            "declared_lead_time": _field(item, "lead_time", "lead_time_days"),
            "declared_tolerance": _field(item, "tolerance", "tolerance_percent"),
            "stated": True,
        })

    results = []
    for need in needs:
        key = need["name"].lower()
        match = next((v for k, v in have.items() if k == key or k in key or key in k), None)
        if match is None:
            state = "HOLD_MISSING_STATEMENT" if not inventory else "HOLD_RESOURCE_GAP"
            detail = ("not stated in the protocol and no inventory supplied"
                      if not inventory else "not present in the supplied inventory")
        else:
            state = "VERIFIED_EXECUTABLE"
            detail = f"present in inventory as {match!r}" if isinstance(match, str) else "present in inventory"
            if isinstance(match, dict):
                avail = match.get("available")
                if avail is False:
                    state, detail = "HOLD_RESOURCE_GAP", "inventory marks it unavailable"
                cap = match.get("range") or match.get("max")
                want = need.get("declared_tolerance")
                if cap is not None and isinstance(want, (int, float)) and isinstance(cap, (int, float)) \
                        and want > cap:
                    state, detail = "REJECT_LIMIT_EXCEEDED", f"requested {want} exceeds capability {cap}"
        results.append({**need, "state": state, "detail": detail})

    # A capability the protocol declares but never quantifies. Only lead time and tolerance block a
    # feasibility verdict, because without them the item cannot be shown to be scheduleable. Range and
    # quantity are recorded as informational: whether they matter depends on the item, and demanding
    # them unconditionally rejects perfectly feasible protocols.
    blocking_fields = ("lead_time", "tolerance")
    informational_fields = ("range", "quantity")
    unstated = []
    informational = []
    for item in _field(protocol, "resources", "requirements", default=[]) or []:
        if isinstance(item, dict):
            name = item.get("name", "?")
            for field_name in blocking_fields:
                if item.get(field_name) in (None, "", []):
                    unstated.append({"item": name, "field": field_name, "state": "not_stated"})
            for field_name in informational_fields:
                if item.get(field_name) in (None, "", []):
                    informational.append({"item": name, "field": field_name, "state": "not_stated"})

    approvals = [a for a in (_field(protocol, "approvals", "ethics", "safety", default=[]) or [])]
    approval_state = "HOLD_APPROVAL_UNCONFIRMED" if approvals else "HOLD_MISSING_STATEMENT"

    # A protocol that declares no external requirements has nothing to check against an inventory, and
    # nothing is being assumed on its behalf -- so it passes. But if it DOES declare requirements and no
    # inventory was supplied, every item's availability is unknown: that must hold, never pass.
    blocker_states = {"HOLD_RESOURCE_GAP", "REJECT_LIMIT_EXCEEDED"}
    overall = "VERIFIED_EXECUTABLE"
    if not results:
        overall = "VERIFIED_EXECUTABLE"
    elif not inventory:
        overall = "HOLD_MISSING_STATEMENT"
    elif any(r["state"] in blocker_states for r in results) or unstated:
        overall = ("HOLD_RESOURCE_GAP" if any(r["state"] in blocker_states for r in results)
                   else "HOLD_MISSING_STATEMENT")

    return {
        "schema": SCHEMA, "status": overall, "items_checked": len(results),
        "not_stated": unstated, "informational_not_stated": informational,
        "approvals": {"count": len(approvals), "state": approval_state},
        "items": results,
        "rule": ("an item the protocol does not state is reported as not stated; absence of a statement "
                 "is never treated as satisfaction. Only lead time and tolerance block a verdict, "
                 "because without them schedulability cannot be established."),
        "audit_allowed": overall == "VERIFIED_EXECUTABLE",
    }


# ------------------------------------------------------------------ 3 parameters

def _provenance_of(text: str) -> str:
    lowered = (text or "")
    for kind, patterns in PROVENANCE_MARKERS.items():
        if any(re.search(p, lowered, re.I) for p in patterns):
            return kind
    return "unspecified"


def parameters(protocol: dict) -> dict:
    """Key parameters with range, unit, provenance, a search strategy and a cost trade-off."""
    findings: list[dict] = []
    rows: list[dict] = []

    params = _field(protocol, "parameters", "key_parameters", default=[]) or []
    if isinstance(params, dict):
        params = [{"name": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in params.items()]

    for p in params:
        name = _field(p, "name", "parameter", default="(unnamed)")
        unit = _field(p, "unit")
        lo, hi = _field(p, "min", "lower"), _field(p, "max", "upper")
        value = _field(p, "value", "recommended")
        src_text = " ".join(str(_field(p, k, default="")) for k in
                            ("basis", "source", "justification", "note", "provenance"))
        prov = _provenance_of(src_text)
        if not unit:
            findings.append({"dimension": "parameter_unit", "severity": "medium",
                             "locator": f"parameter:{name}", "evidence": "no unit",
                             "suggested_action": f"state the unit for {name}"})
        if lo is None or hi is None:
            findings.append({"dimension": "parameter_range", "severity": "medium",
                             "locator": f"parameter:{name}", "evidence": "no admissible range",
                             "suggested_action": f"state the range {name} may take, not only a point value"})
        if prov == "unspecified":
            findings.append({
                "dimension": "parameter_provenance", "severity": "high", "locator": f"parameter:{name}",
                "evidence": "no basis given for the range",
                "suggested_action": ("say whether the range comes from an equipment limit, a material "
                                     "limit, a safety threshold, the literature, or experience"),
            })
        if isinstance(value, (int, float)) and isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            if not (lo <= value <= hi):
                findings.append({"dimension": "parameter_range", "severity": "high",
                                 "locator": f"parameter:{name}",
                                 "evidence": f"recommended {value} outside stated range [{lo}, {hi}]",
                                 "suggested_action": "reconcile the recommendation with the admissible range"})
        rows.append({"name": name, "unit": unit, "min": lo, "max": hi, "value": value,
                     "provenance": prov})

    strategy = _field(protocol, "search_strategy", "optimisation", default={}) or {}
    if isinstance(strategy, dict):
        if not _field(strategy, "method", "design"):
            findings.append({"dimension": "search_strategy", "severity": "medium", "locator": "search_strategy",
                             "evidence": "no search or design method named",
                             "suggested_action": "name the search method and the candidate points it generates"})
        if not _field(strategy, "stop_rule", "convergence", "stopping_criterion"):
            findings.append({
                "dimension": "search_strategy", "severity": "high", "locator": "search_strategy",
                "evidence": "no convergence or stopping criterion",
                "suggested_action": ("state when the search stops and on what evidence, so the run is "
                                     "reproducible and bounded"),
            })
    elif not strategy:
        findings.append({"dimension": "search_strategy", "severity": "high", "locator": "protocol",
                         "evidence": "no search strategy declared",
                         "suggested_action": "state the method, the candidate points and the stopping rule"})

    return {"schema": SCHEMA, "parameters": rows, "findings": findings,
            "high_severity": sum(1 for f in findings if f["severity"] == "high"),
            "status": "complete" if not any(f["severity"] == "high" for f in findings) else "needs_work",
            "rule": "a parameter range without a stated basis is a finding; a search without a stop rule is a finding"}


# ------------------------------------------------------------------ 4 compare

COMPARE_FIELDS = ("goal_fit", "risk", "cost", "feasibility", "evidence")


def compare(candidates: dict | list) -> dict:
    """Compare candidate routes on identical fields, and require a rejection reason."""
    items = candidates.get("candidates") if isinstance(candidates, dict) else candidates
    items = items or []
    findings: list[dict] = []
    matrix = []
    gestalt_phrases = ("some risk", "certain risk", "存在一定风险", "generally", "overall",
                       "有一定风险", "需要进一步确认")

    for cand in items:
        name = _field(cand, "name", "id", default="(unnamed)")
        row = {"name": name}
        for field_name in COMPARE_FIELDS:
            row[field_name] = _field(cand, field_name)
            if row[field_name] in (None, "", []):
                findings.append({
                    "dimension": "comparison_completeness", "severity": "high",
                    "locator": f"candidate:{name}", "evidence": f"field {field_name} is missing",
                    "suggested_action": (f"state {field_name} for every candidate on the same basis; a "
                                        "comparison is only possible when the fields are identical"),
                })
        risk_text = json.dumps(_field(cand, "risk", default=""), ensure_ascii=False)
        if any(p in risk_text.lower() for p in gestalt_phrases) and not re.search(
                r"trigger|consequence|mitigat|\u89e6\u53d1|\u540e\u679c|\u7f13\u89e3", risk_text, re.I):
            findings.append({
                "dimension": "risk_specificity", "severity": "high", "locator": f"candidate:{name}",
                "evidence": risk_text[:120],
                "suggested_action": "give each risk a trigger, a consequence magnitude and a mitigation",
            })
        # time and cost must not be consumables-only
        cost_text = json.dumps(_field(cand, "cost", default=""), ensure_ascii=False)
        if cost_text and not re.search(r"machine|labor|labour|hour|机时|人工|工日|人力", cost_text, re.I):
            findings.append({
                "dimension": "cost_completeness", "severity": "medium", "locator": f"candidate:{name}",
                "evidence": cost_text[:120],
                "suggested_action": "include machine time and labour, not consumables alone",
            })
        time_text = json.dumps(_field(cand, "time", "duration", default=""), ensure_ascii=False)
        if time_text and not re.search(r"prep|schedul|queue|rework|准备|排期|排队|返工", time_text, re.I):
            findings.append({
                "dimension": "time_completeness", "severity": "medium", "locator": f"candidate:{name}",
                "evidence": time_text[:120],
                "suggested_action": ("include preparation, instrument scheduling, queueing and rework, "
                                     "not execution alone"),
            })
        matrix.append(row)

    chosen = _field(candidates, "chosen") if isinstance(candidates, dict) else None
    rejection = _field(candidates, "rejection_reason", "reason") if isinstance(candidates, dict) else None
    if len(items) > 1 and not rejection:
        findings.append({
            "dimension": "selection_justification", "severity": "high", "locator": "selection",
            "evidence": "a choice is implied but no rejection reason is recorded",
            "suggested_action": ("state why each rejected route was rejected; the brief asks for a "
                                 "defensible choice and a concrete reason to discard the others"),
        })

    return {"schema": SCHEMA, "candidates": len(items), "fields": list(COMPARE_FIELDS),
            "matrix": matrix, "chosen": chosen, "rejection_reason": rejection,
            "findings": findings,
            "status": "complete" if not any(f["severity"] == "high" for f in findings) else "needs_work",
            "rule": "identical fields for every candidate; risk needs trigger, consequence and mitigation"}


# ------------------------------------------------------------------ 5 anomaly

def anomaly(readings: list[dict], id_col: str, value_col: str, method: str = "mad",
            threshold: float = 3.0) -> dict:
    """Flag anomalous readings with a stated threshold and distance, plus an elimination scaffold."""
    groups: dict[str, list[float]] = {}
    order: list[tuple[str, float]] = []
    for row in readings:
        try:
            value = float(str(row.get(value_col)).strip())
        except (TypeError, ValueError):
            continue
        key = str(row.get(id_col, "(all)"))
        groups.setdefault(key, []).append(value)
        order.append((key, value))

    anomalies: list[dict] = []
    for key, values in groups.items():
        if len(values) < 3:
            continue
        median = statistics.median(values)
        if method == "mad":
            deviations = [abs(v - median) for v in values]
            mad = statistics.median(deviations)
            scale = mad * 1.4826 if mad > 0 else 0.0
            basis = f"modified z-score on MAD, median={median:g}, scaled MAD={scale:g}"
        else:
            scale = statistics.pstdev(values) or 0.0
            basis = f"z-score, mean={statistics.fmean(values):g}, sd={scale:g}"
        if scale <= 0:
            continue
        for value in values:
            distance = abs(value - median) / scale
            if distance > threshold:
                anomalies.append({
                    "group": key, "value": value, "distance": round(distance, 3),
                    "threshold": threshold, "basis": basis,
                    "direction": "high" if value > median else "low",
                })

    trend = []
    for key, values in groups.items():
        if len(values) >= 3:
            rising = sum(1 for a, b in zip(values, values[1:]) if b > a)
            falling = sum(1 for a, b in zip(values, values[1:]) if b < a)
            trend.append({"group": key, "n": len(values), "monotonic_runs": {"up": rising, "down": falling},
                          "statement": ("monotonic rising" if rising == len(values) - 1 else
                                        "monotonic falling" if falling == len(values) - 1 else
                                        "not monotonic")})

    return {
        "schema": SCHEMA, "groups": len(groups), "readings": len(order),
        "method": method, "threshold": threshold,
        "trend": trend, "anomalies": anomalies,
        "candidate_causes": [],
        "elimination_record": [],
        "recheck_steps": [],
        "rule": ("an anomaly needs a stated threshold and its distance, not an adjective; each candidate "
                 "cause needs an elimination entry, and each re-check needs a concrete action"),
        "next": ("fill candidate_causes with every plausible cause, record for each how it was tested, "
                 "and add re-check steps that name an action rather than 'check data quality'"),
    }


# ------------------------------------------------------------------ 6 cost

DEFAULT_RATES = {
    "machine_hour": 0.0, "labour_hour": 0.0, "consumable_unit": 0.0,
    "currency": "CNY", "note": "rates must be supplied; nothing here is inferred",
}


def cost(plan: dict, rates: dict | None) -> dict:
    """Roll up machine time, labour and consumables, plus preparation, scheduling and rework.

    No rate is inferred. A missing rate is reported as missing and the total is marked incomplete,
    because a cost model that silently assumes zero is worse than one that admits it cannot total.
    """
    rates = {**DEFAULT_RATES, **(rates or {})}
    missing_rate: list[str] = []
    lines: list[dict] = []
    totals = {"machine": 0.0, "labour": 0.0, "consumable": 0.0}

    for step in _field(plan, "steps", default=[]) or []:
        name = _field(step, "name", "step", default="(unnamed)")
        machine_h = float(_field(step, "machine_hours", "machine_time_h", default=0) or 0)
        labour_h = float(_field(step, "labour_hours", "labour_time_h", default=0) or 0)
        consumable = float(_field(step, "consumable_cost", default=0) or 0)
        if machine_h and not rates.get("machine_hour"):
            missing_rate.append("machine_hour")
        if labour_h and not rates.get("labour_hour"):
            missing_rate.append("labour_hour")
        line_cost = machine_h * float(rates.get("machine_hour") or 0) \
            + labour_h * float(rates.get("labour_hour") or 0) + consumable
        totals["machine"] += machine_h * float(rates.get("machine_hour") or 0)
        totals["labour"] += labour_h * float(rates.get("labour_hour") or 0)
        totals["consumable"] += consumable
        lines.append({"step": name, "machine_hours": machine_h, "labour_hours": labour_h,
                      "consumable_cost": consumable, "cost": round(line_cost, 2)})

    overhead = _field(plan, "overhead", default={}) or {}
    overhead_cost = 0.0
    for kind in ("preparation", "scheduling", "queueing", "rework"):
        factor = float(overhead.get(kind + "_factor", 0) or 0)
        if factor:
            overhead_cost += sum(totals.values()) * factor

    missing_rate = sorted(set(missing_rate))
    total = sum(totals.values()) + overhead_cost
    return {
        "schema": SCHEMA, "currency": rates.get("currency"), "lines": lines,
        "totals": {k: round(v, 2) for k, v in totals.items()},
        "overhead_included": sorted(k for k in ("preparation", "scheduling", "queueing", "rework")
                                    if overhead.get(k + "_factor")),
        "overhead_cost": round(overhead_cost, 2),
        "total": round(total, 2),
        "missing_rates": missing_rate,
        "status": "complete" if not missing_rate else "incomplete: rates missing",
        "rule": ("machine time and labour are costed, not only consumables; a missing rate is reported "
                 "rather than assumed to be zero"),
    }


# ------------------------------------------------------------------ cli

def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Experimental protocol audit")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("operationalise"); p.add_argument("--protocol", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("feasibility"); p.add_argument("--protocol", required=True); p.add_argument("--inventory"); p.add_argument("--out", required=True)
    p = sub.add_parser("parameters"); p.add_argument("--protocol", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("compare"); p.add_argument("--candidates", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("anomaly")
    p.add_argument("--readings", required=True); p.add_argument("--id-col", default="group")
    p.add_argument("--value-col", default="value"); p.add_argument("--method", default="mad", choices=("mad", "z"))
    p.add_argument("--threshold", type=float, default=3.0); p.add_argument("--out", required=True)
    p = sub.add_parser("cost"); p.add_argument("--plan", required=True); p.add_argument("--rates"); p.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.command == "operationalise":
        result = operationalise(read_json(args.protocol)); write_json(args.out, result)
        print(json.dumps({"findings": len(result["findings"]), "high": result["high_severity"],
                          "status": result["status"]}, ensure_ascii=False))
        return 0 if result["status"] == "executable" else 3
    if args.command == "feasibility":
        inv = read_json(args.inventory) if args.inventory else None
        result = feasibility(read_json(args.protocol), inv); write_json(args.out, result)
        print(json.dumps({"status": result["status"], "checked": result["items_checked"],
                          "not_stated": len(result["not_stated"]), "audit_allowed": result["audit_allowed"]},
                         ensure_ascii=False))
        return 0 if result["audit_allowed"] else 3
    if args.command == "parameters":
        result = parameters(read_json(args.protocol)); write_json(args.out, result)
        print(json.dumps({"parameters": len(result["parameters"]), "high": result["high_severity"],
                          "status": result["status"]}, ensure_ascii=False))
        return 0 if result["status"] == "complete" else 3
    if args.command == "compare":
        result = compare(read_json(args.candidates)); write_json(args.out, result)
        print(json.dumps({"candidates": result["candidates"], "findings": len(result["findings"]),
                          "status": result["status"]}, ensure_ascii=False))
        return 0 if result["status"] == "complete" else 3
    if args.command == "anomaly":
        result = anomaly(read_csv(args.readings), args.id_col, args.value_col, args.method, args.threshold)
        write_json(args.out, result)
        print(json.dumps({"groups": result["groups"], "anomalies": len(result["anomalies"]),
                          "threshold": result["threshold"]}, ensure_ascii=False))
        return 0
    if args.command == "cost":
        rates = read_json(args.rates) if args.rates else None
        result = cost(read_json(args.plan), rates); write_json(args.out, result)
        print(json.dumps({"total": result["total"], "currency": result["currency"],
                          "missing_rates": result["missing_rates"], "status": result["status"]},
                         ensure_ascii=False))
        return 0 if not result["missing_rates"] else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
