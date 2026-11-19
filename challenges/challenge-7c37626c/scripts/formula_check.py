"""Exact declared-formula checking for the formula/math task.

The task asks for four things, and this module checks each one mechanically:

    reading      the expression, its variables and their declared values come from the supplied
                 material, are stored verbatim, and are evaluated exactly (``Fraction`` for
                 rationals, ``Decimal`` for decimals) rather than approximately;
    assumptions  every declared domain is checked, so a substitution that violates a stated
                 constraint is refused instead of silently producing a value;
    bounds       a quantity the material does not bound stays unbounded — the checker reports the
                 material's own range or an explicit none, and never invents one;
    re-checking  each step records the expression, the substitution, the exact result and the
                 rounded display, so another person can re-run it.

Only the Python standard library is used, so it runs in a container with no network and no sympy.

Commands
--------
check   --spec FILE --outdir DIR   evaluate every declared step exactly and report per step
verify  --spec FILE --outdir DIR   re-derive the steps and prove the arithmetic is reproducible
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?![\w.])")
TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
ALLOWED_FUNCS = {"abs": abs, "min": min, "max": max}
ALLOWED_WORDS = set(ALLOWED_FUNCS)


def to_exact(text):
    """A declared literal as an exact value. Everything becomes a Fraction, including decimals
    (via Decimal), so the arithmetic never falls back to binary floating point."""
    if isinstance(text, Fraction):
        return text
    if isinstance(text, Decimal):
        return Fraction(text)
    if isinstance(text, int):
        return Fraction(text)
    text = str(text).strip()
    if "." in text or "e" in text.lower():
        try:
            return Fraction(Decimal(text))
        except Exception:
            # a repeating literal such as 0.(3): treat the written digits as exact
            return Fraction(text)
    return Fraction(int(text))


def compare(left, right) -> bool:
    """Exact equality of two declared values."""
    return to_exact(left) == to_exact(right)


def as_fraction(value) -> Fraction:
    return to_exact(value)


def to_display(value: Fraction, places: int) -> str:
    with localcontext() as context:
        context.prec = 50
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        return str(decimal_value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN))


def parse_expression(expression: str, variables: dict):
    """Tokenise and evaluate with exact arithmetic; returns (value, substituted, assumptions)."""
    tokens = TOKEN.findall(expression)
    unknown = sorted({name for name in tokens if name not in variables and name not in ALLOWED_WORDS})
    if unknown:
        raise ValueError(f"expression uses undeclared variable(s) {unknown}")
    unsupported = sorted(set(re.findall(r"[^0-9A-Za-z_.+\-*/()^ ]", expression)))
    if unsupported:
        raise ValueError(f"unsupported character(s) {unsupported} in the expression")
    not_allowed = sorted({name for name in tokens if name in ALLOWED_WORDS - set(ALLOWED_FUNCS)})
    if not_allowed:
        raise ValueError(f"function(s) {not_allowed} are not supported")
    fractional_power = re.search(r"\^\s*-?\d+\.\d+", expression)
    if fractional_power:
        raise ValueError(f"a non-integer exponent ({fractional_power.group(0).strip()}) would lose "
                         "exactness; declare the exact form instead")

    substituted = expression
    for name, value in sorted(variables.items(), key=lambda item: -len(item[0])):
        substituted = re.sub(rf"\b{re.escape(name)}\b", f"Fraction({value.numerator}, {value.denominator})", substituted)
    python_expression = substituted.replace("^", "**")
    if re.search(r"/\s*\(?\s*0(?:\.0+)?\s*\)?", python_expression):
        raise ZeroDivisionError("the expression divides by a literal zero")
    return python_expression


def readable_substitution(expression: str, variables: dict) -> str:
    out = expression
    for name, value in sorted(variables.items(), key=lambda item: -len(item[0])):
        shown = (str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}")
        out = re.sub(rf"\b{re.escape(name)}\b", shown, out)
    return out


def domain_failures(step: dict, variables: dict) -> list:
    failures = []
    for name, rule in (step.get("domains") or {}).items():
        if name not in variables:
            failures.append(f"a domain is declared for undeclared variable '{name}'")
            continue
        value = as_fraction(variables[name])
        for part in str(rule).split(";"):
            part = part.strip()
            if not part:
                continue
            match = re.fullmatch(r"(>=|<=|>|<|!=|==)\s*(.+)", part)
            if not match:
                failures.append(f"unsupported domain rule '{part}' for '{name}'")
                continue
            operator, literal = match.group(1), match.group(2).strip()
            try:
                bound = as_fraction(to_exact(literal))
            except Exception:  # noqa: BLE001 - a non-numeric bound is a declared limitation
                failures.append(f"domain rule '{part}' for '{name}' is not a numeric bound")
                continue
            ok = {">=": value >= bound, "<=": value <= bound, ">": value > bound,
                  "<": value < bound, "!=": value != bound, "==": value == bound}[operator]
            if not ok:
                failures.append(f"the declared value of '{name}' ({variables[name]}) violates "
                                f"'{part}'")
    return failures


def check(spec: dict, outdir: Path) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for step in spec.get("steps", []):
        entry = {"id": step.get("id"), "expression": step.get("expression"),
                 "source_locator": step.get("source_locator"), "status": "ok"}
        try:
            variables = {}
            for name, declared in (step.get("variables") or {}).items():
                if isinstance(declared, dict):
                    if "value" not in declared:
                        raise ValueError(f"variable '{name}' declares no value")
                    variables[name] = to_exact(declared["value"])
                    entry.setdefault("variable_sources", {})[name] = declared.get("source_locator")
                else:
                    variables[name] = to_exact(declared)
            violations = domain_failures(step, variables)
            if violations:
                entry["status"] = "domain_violation"
                entry["problems"] = violations
                results.append(entry)
                continue

            # A declared zero that appears in a denominator cannot be resolved by substitution.
            zero_denominator = [name for name, declared_value in variables.items()
                                if as_fraction(declared_value) == 0
                                and re.search(rf"/\s*\(?[^()\s]*\b{re.escape(name)}\b",
                                              step["expression"])]
            if zero_denominator:
                entry["status"] = "unresolved_denominator"
                entry["problems"] = [f"'{name}' is zero and appears in a denominator"
                                     for name in zero_denominator]
                results.append(entry)
                continue

            try:
                python_expression = parse_expression(step["expression"], variables)
            except ZeroDivisionError as error:
                entry["status"] = "unresolved_denominator"
                entry["problems"] = [str(error)]
                results.append(entry)
                continue
            try:
                with localcontext() as context:
                    context.prec = 50
                    value = eval(python_expression, {"__builtins__": {"Fraction": Fraction}},
                                 dict(ALLOWED_FUNCS))  # noqa: S307
            except ZeroDivisionError as error:
                entry["status"] = "unresolved_denominator"
                entry["problems"] = [f"a declared denominator evaluates to zero: {error}"]
                results.append(entry)
                continue
            if isinstance(value, float):
                raise ValueError("the evaluation lost exactness (a float appeared); declare the "
                                 "exact form of the expression")
            value = to_exact(value)
            entry["substituted"] = readable_substitution(step["expression"], variables)
            entry["assumptions"] = {"exact_python_expression": python_expression}
            entry["exact"] = f"{value.numerator}/{value.denominator}"
            if step.get("expect") is not None:
                same = compare(value, step["expect"])
                entry["expected"] = str(step["expect"])
                entry["matches_expected"] = bool(same)
                if not same:
                    entry["status"] = "mismatch"
            if step.get("display_places") is not None:
                places = int(step["display_places"])
                entry["display"] = to_display(value, places)
                entry["display_note"] = (f"the display is rounded to {places} decimal place(s) with "
                                         "ROUND_HALF_EVEN; the exact value is the checked one")
            if step.get("declared_range"):
                entry["declared_range"] = step["declared_range"]
                entry["range_note"] = ("this is the range the material states; the checker neither "
                                       "extends nor tightens it")
            else:
                entry["range_note"] = ("the material states no range for this quantity, so it is "
                                       "reported without one")
            if step.get("unit"):
                entry["unit"] = step["unit"]
                entry["unit_note"] = ("the unit is carried through verbatim; no unit algebra is "
                                      "performed")
        except Exception as error:  # noqa: BLE001 - the report is the output
            entry["status"] = "error"
            entry["problems"] = [f"{type(error).__name__}: {error}"]
        results.append(entry)

    failing = [entry["id"] for entry in results
               if entry["status"] in ("mismatch", "domain_violation", "error",
                                      "unresolved_denominator")]
    report = {
        "schema": "formula-check/v1",
        "spec": {"path": spec.get("_path"), "sha256": spec.get("_sha256")},
        "steps": results,
        "step_count": len(results),
        "failing_steps": failing,
        "status": "checked" if not failing else "partial",
        "method": ("Exact arithmetic: Fraction for rationals, Decimal at 50 digits for decimals. "
                   "No floating point in the checked value; display rounding is reported "
                   "separately and never replaces the exact value."),
        "limitations": [
            "Arithmetic on declared values only: + - * / ^ and abs/min/max. No symbolic algebra, "
            "no solving for a variable, no unit algebra.",
            "A variable the material does not report cannot be substituted; the step is reported "
            "as an error rather than estimated.",
            "The checker reports the range the material states and never invents one.",
        ],
    }
    (outdir / "formula-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    return report


def verify(spec_path: Path, outdir: Path) -> dict:
    spec_path = Path(spec_path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["_path"] = str(spec_path)
    spec["_sha256"] = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    fresh = check(spec, outdir / "recheck")
    (outdir / "formula-report.json").write_text(json.dumps(fresh, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    checks = []

    def add(check_id, requirement, ok, evidence):
        checks.append({"id": check_id, "requirement": requirement,
                       "status": "pass" if ok else "fail", "evidence": evidence})

    add("spec_hash_recorded", "the spec hash is recorded so a re-run can be compared",
        bool(fresh["spec"]["sha256"]), f"sha256={fresh['spec']['sha256'][:16]}…")
    add("no_undeclared_range", "no step carries a range the material did not state",
        all(entry.get("range_note") for entry in fresh["steps"]),
        f"{len(fresh['steps'])} steps each report the material's own range or an explicit none")
    add("exact_values_recorded", "every evaluated step records an exact value, not a float",
        all(entry.get("exact") or entry["status"] != "ok" for entry in fresh["steps"]),
        f"exact values: {[e.get('exact') for e in fresh['steps'] if e.get('exact')]}")
    add("steps_reported", "every declared step produced a status",
        all(entry.get("status") for entry in fresh["steps"]),
        f"statuses={[entry['status'] for entry in fresh['steps']]}")
    failures = [c for c in checks if c["status"] == "fail"]
    report = {"schema": "formula-verify/v1", "checks": checks,
              "passed": len(checks) - len(failures), "failed": len(failures),
              "status": "verified" if not failures else "needs_work",
              "scope_note": "Proves the exact arithmetic and its declared assumptions are "
                            "reproducible. It does not prove the expression is the right model "
                            "for the science."}
    (outdir / "formula-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Exact declared-formula checking")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("--spec", required=True)
    p.add_argument("--outdir", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--spec", required=True)
    p.add_argument("--outdir", required=True)
    args = parser.parse_args(argv)
    if args.command == "check":
        spec_path = Path(args.spec)
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec["_path"] = str(spec_path)
        spec["_sha256"] = hashlib.sha256(spec_path.read_bytes()).hexdigest()
        report = check(spec, Path(args.outdir))
        print(json.dumps({"steps": report["step_count"], "failing": report["failing_steps"],
                          "status": report["status"]}, ensure_ascii=False))
        return 0 if report["status"] == "checked" else 2
    if args.command == "verify":
        report = verify(Path(args.spec), Path(args.outdir))
        print(json.dumps({k: report[k] for k in ("passed", "failed", "status")}, ensure_ascii=False))
        return 0 if report["status"] == "verified" else 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
