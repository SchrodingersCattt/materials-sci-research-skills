"""Prove protocol_audit behaves, on fixtures with planted defects and correct controls.

The governing rule under test is the one the brief states and that is easiest to get wrong: something
the protocol does not state must be reported as **not stated**, never assumed satisfied. So the
fixtures come in pairs — a defective protocol and a correct one — and a check fails if the tool cannot
tell them apart.

    python tests/protocol_audit_checks.py [--workdir work/protocol]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "protocol_audit.py"

DEFECTIVE = {
    "goal": "determine whether catalyst loading changes conversion",
    "variables": [
        {"name": "loading"},                                  # name only: no unit/instrument/range
        {"name": "conversion", "measured_by": "GC", "unit": "%", "instrument": "Agilent 7820A",
         "range": "0-100"},
    ],
    "controls": [{"name": "untreated", "kind": "blank"}],      # no positive control
    "decision_criteria": ["conversion should be better"],      # no numeric bound
    "resources": [
        {"name": "GC-FID"},                                   # no lead time, no tolerance
        {"name": "tube furnace", "tolerance": 1200},          # exceeds the inventory capability
    ],
    "parameters": [
        {"name": "temperature", "value": 250, "unit": "C", "min": 100, "max": 200, "basis": "we usually do this"},
        {"name": "loading", "value": 5, "min": 1, "max": 10},  # no unit, no basis
    ],
    "search_strategy": {"method": "one-factor-at-a-time"},    # no stopping criterion
    "approvals": [],
}

GOOD = {
    "goal": "determine whether catalyst loading changes conversion",
    "variables": [
        {"name": "loading", "measured_by": "gravimetric balance", "unit": "wt%",
         "instrument": "Mettler XS205", "range": "1-10"},
        {"name": "conversion", "measured_by": "GC-FID peak area", "unit": "%",
         "instrument": "Agilent 7820A", "range": "0-100"},
    ],
    "controls": [{"name": "untreated", "kind": "blank"}, {"name": "known-active", "kind": "positive"}],
    "decision_criteria": ["conversion within 5 % of the reference standard"],
    "resources": [{"name": "GC-FID", "lead_time": 0, "tolerance": 100},
                  {"name": "tube furnace", "lead_time": 3, "tolerance": 100}],
    "parameters": [
        {"name": "temperature", "value": 180, "unit": "C", "min": 100, "max": 200,
         "basis": "furnace range [equipment limit]"},
        {"name": "loading", "value": 5, "unit": "wt%", "min": 1, "max": 10,
         "basis": "range reported by [12]"},
    ],
    "search_strategy": {"method": "response surface", "stop_rule": "stop when predicted gain < 2 %"},
    "approvals": ["safety review"],
}

INVENTORY = {"items": {"GC-FID": {"available": True, "max": 100},
                       "tube furnace": {"available": True, "max": 200},
                       "Mettler XS205": {"available": True}}}


def run(*argv) -> tuple[int, dict | None, str]:
    proc = subprocess.run([sys.executable, str(TOOL), *[str(a) for a in argv]],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, None, (proc.stdout or "") + (proc.stderr or "")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="work/protocol")
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    (work / "defective.json").write_text(json.dumps(DEFECTIVE, ensure_ascii=False), encoding="utf-8")
    (work / "good.json").write_text(json.dumps(GOOD, ensure_ascii=False), encoding="utf-8")
    (work / "inventory.json").write_text(json.dumps(INVENTORY, ensure_ascii=False), encoding="utf-8")

    failures: list[str] = []
    observed: dict = {}

    # ---- 1 operationalise: the defective protocol must be flagged, the good one must not
    run("operationalise", "--protocol", work / "defective.json", "--out", work / "opd.json")
    run("operationalise", "--protocol", work / "good.json", "--out", work / "opg.json")
    opd, opg = load(work / "opd.json"), load(work / "opg.json")
    observed["operationalise"] = {"defective_status": opd["status"], "defective_high": opd["high_severity"],
                                  "good_status": opg["status"]}
    if opd["status"] != "needs_work":
        failures.append("a protocol with a name-only variable was judged executable")
    if not any(f["dimension"] == "variable_operationalisation" for f in opd["findings"]):
        failures.append("a variable lacking unit/instrument/range was not reported")
    if not any(f["dimension"] == "control_design" and "positive" in f["evidence"] for f in opd["findings"]):
        failures.append("a protocol with only a blank control was not flagged for a missing positive control")
    if opg["status"] != "executable":
        failures.append(f"a well-formed protocol was judged {opg['status']!r} (false positive)")

    # ---- 2 feasibility: unstated must be `not stated`, and a capability breach must be rejected
    run("feasibility", "--protocol", work / "defective.json", "--inventory", work / "inventory.json",
        "--out", work / "fd.json")
    run("feasibility", "--protocol", work / "good.json", "--inventory", work / "inventory.json",
        "--out", work / "fg.json")
    fd, fg = load(work / "fd.json"), load(work / "fg.json")
    observed["feasibility"] = {"defective": fd["status"], "good": fg["status"],
                               "not_stated": len(fd["not_stated"])}
    if not fd["not_stated"]:
        failures.append("items the protocol never stated were not reported as not_stated")
    if fd["status"] == "VERIFIED_EXECUTABLE":
        failures.append("a protocol declaring a 1200-unit tolerance on a 200-unit instrument passed feasibility")
    if not any(s["state"] == "REJECT_LIMIT_EXCEEDED" or s["state"] == "HOLD_RESOURCE_GAP" for s in fd["items"]):
        failures.append("no capability breach was detected")
    # the good protocol asks for 100 on a 100-capability item: within, so it must pass
    if fg["status"] != "VERIFIED_EXECUTABLE":
        failures.append(f"a feasible protocol was judged {fg['status']!r} (false positive)")

    # ---- 3 feasibility with NO inventory must hold rather than assume
    run("feasibility", "--protocol", work / "good.json", "--out", work / "fn.json")
    fn = load(work / "fn.json")
    # a protocol declaring no external requirements has nothing to assume and must pass
    no_needs = {"variables": GOOD["variables"], "controls": GOOD["controls"]}
    (work / "none.json").write_text(json.dumps(no_needs, ensure_ascii=False), encoding="utf-8")
    run("feasibility", "--protocol", work / "none.json", "--out", work / "fz.json")
    fz = load(work / "fz.json")
    observed["feasibility_no_inventory"] = {"with_needs": fn["status"], "with_needs_allowed": fn["audit_allowed"],
                                            "without_needs": fz["status"]}
    if fn["audit_allowed"]:
        failures.append("with no inventory supplied and requirements declared, feasibility was allowed: absence was treated as satisfaction")
    if fz["status"] != "VERIFIED_EXECUTABLE":
        failures.append("a protocol declaring no external requirements was not allowed (false positive)")

    # ---- 4 parameters: provenance and out-of-range recommendation
    run("parameters", "--protocol", work / "defective.json", "--out", work / "pd.json")
    run("parameters", "--protocol", work / "good.json", "--out", work / "pg.json")
    pd, pg = load(work / "pd.json"), load(work / "pg.json")
    observed["parameters"] = {"defective_high": pd["high_severity"], "good_status": pg["status"]}
    if not any(f["dimension"] == "parameter_provenance" for f in pd["findings"]):
        failures.append("a parameter range with no stated basis was not reported")
    if not any("outside stated range" in f["evidence"] for f in pd["findings"]):
        failures.append("a recommended value outside its own stated range was not caught")
    if not any(f["dimension"] == "search_strategy" and "convergence" in f["evidence"]
               for f in pd["findings"]):
        failures.append("a search strategy with no stopping criterion was not reported")
    if pg["status"] != "complete":
        failures.append(f"a well-formed parameter set was judged {pg['status']!r} (false positive)")

    # ---- 5 compare: missing fields and a gestalt risk must both be flagged
    candidates = {"chosen": "A", "candidates": [
        {"name": "A", "goal_fit": "high", "risk": "some risk", "cost": "100 CNY consumables",
         "feasibility": "high", "evidence": "[1]", "time": "2 days"},
        {"name": "B", "goal_fit": "medium", "risk": {"trigger": "overheat", "consequence": "run lost",
                                                     "mitigation": "interlock"}, "cost": "machine 4 h",
         "feasibility": "medium", "evidence": "[2]", "time": "prep 1 d, queue 2 d"},
    ]}
    (work / "cands.json").write_text(json.dumps(candidates, ensure_ascii=False), encoding="utf-8")
    run("compare", "--candidates", work / "cands.json", "--out", work / "cmp.json")
    cmp_ = load(work / "cmp.json")
    observed["compare"] = {"candidates": cmp_["candidates"], "findings": len(cmp_["findings"])}
    if not any(f["dimension"] == "risk_specificity" for f in cmp_["findings"]):
        failures.append("a gestalt risk with no trigger/consequence/mitigation was not flagged")
    if not any(f["dimension"] == "cost_completeness" for f in cmp_["findings"]):
        failures.append("a consumables-only cost was not flagged as missing machine time and labour")
    if not any(f["dimension"] == "time_completeness" for f in cmp_["findings"]):
        failures.append("an execution-only time estimate was not flagged as missing prep/queue/rework")
    if not any(f["dimension"] == "selection_justification" for f in cmp_["findings"]):
        failures.append("a choice with no rejection reason was not flagged")

    # ---- 6 anomaly: a planted outlier must be found with a stated distance; clean data must not alarm
    rows = [{"group": "run", "value": v} for v in (10.0, 10.2, 9.8, 10.1, 9.9, 10.0, 41.0)]
    clean = [{"group": "run", "value": v} for v in (10.0, 10.2, 9.8, 10.1, 9.9, 10.0, 9.95)]
    for name, data in (("anom.csv", rows), ("clean.csv", clean)):
        with open(work / name, "w", encoding="utf-8", newline="") as handle:
            handle.write("group,value\n")
            for r in data:
                handle.write(f"{r['group']},{r['value']}\n")
    run("anomaly", "--readings", work / "anom.csv", "--id-col", "group", "--value-col", "value",
        "--out", work / "a1.json")
    run("anomaly", "--readings", work / "clean.csv", "--id-col", "group", "--value-col", "value",
        "--out", work / "a2.json")
    a1, a2 = load(work / "a1.json"), load(work / "a2.json")
    observed["anomaly"] = {"planted_found": len(a1["anomalies"]), "clean_flagged": len(a2["anomalies"])}
    if not a1["anomalies"]:
        failures.append("the planted outlier at 41.0 was not detected")
    elif not any(abs(x["value"] - 41.0) < 1e-9 for x in a1["anomalies"]):
        failures.append("an anomaly was reported but not the planted one")
    if a2["anomalies"]:
        failures.append(f"clean data produced {len(a2['anomalies'])} false anomalies")
    if not a1.get("threshold"):
        failures.append("anomaly output carries no stated threshold")

    # ---- 7 cost: missing rates must be admitted, not assumed zero
    plan = {"steps": [{"name": "synthesis", "machine_hours": 4, "labour_hours": 2,
                       "consumable_cost": 150},
                      {"name": "analysis", "machine_hours": 2, "labour_hours": 1}],
            "overhead": {"preparation_factor": 0.1, "rework_factor": 0.05}}
    (work / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    (work / "rates.json").write_text(json.dumps({"machine_hour": 80, "labour_hour": 120,
                                                "currency": "CNY"}), encoding="utf-8")
    run("cost", "--plan", work / "plan.json", "--rates", work / "rates.json", "--out", work / "c1.json")
    run("cost", "--plan", work / "plan.json", "--out", work / "c2.json")
    c1, c2 = load(work / "c1.json"), load(work / "c2.json")
    observed["cost"] = {"with_rates": c1["total"], "without_rates_status": c2["status"],
                        "missing": c2["missing_rates"]}
    if c1["totals"]["machine"] <= 0 or c1["totals"]["labour"] <= 0:
        failures.append("machine time or labour was not costed")
    if not c1["overhead_included"]:
        failures.append("preparation and rework overhead were not included")
    if not c2["missing_rates"]:
        failures.append("with no rates supplied, the cost model did not report missing rates")

    report = {"fixture": str(work), "checks": 7, "failures": failures, "observed": observed,
              "verdict": "pass" if not failures else "fail",
              "note": "Synthetic fixtures only; not organiser cases, not official results."}
    (work / "protocol-audit-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                     encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
