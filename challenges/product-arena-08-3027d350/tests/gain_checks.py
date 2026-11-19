"""Prove the gain check measures what it claims, on a fixture with planted defects.

    python tests/gain_checks.py [--workdir work/gain]

Exit 0 only when every behaviour holds. Standard library only, deterministic, no network.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "scripts" / "gain_check.py"
CASES = HERE / "gain_cases"
MATERIAL = CASES / "material"


def run(answer: Path, out: Path, baseline: Path | None = None) -> tuple[int, dict]:
    argv = [sys.executable, str(TOOL), "--source", str(MATERIAL), "--answer", str(answer),
            "--out", str(out)]
    if baseline is not None:
        argv += ["--baseline", str(baseline)]
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    payload = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    return proc.returncode, payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="work/gain")
    args = ap.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    observed: dict = {}

    rc, grounded = run(CASES / "answer-grounded.json", work / "grounded.json")
    skill = grounded.get("skill", {})
    observed["grounded"] = {k: skill.get(k) for k in
                            ("coverage", "grounding", "claims_measured", "verdict")}
    if rc != 0:
        failures.append(f"the grounded answer was refused or errored (rc={rc})")
    if skill.get("grounding") != 1.0:
        failures.append(f"a fully traceable answer scored grounding={skill.get('grounding')}")
    if skill.get("verdict") != "grounded":
        failures.append(f"a grounded answer was judged {skill.get('verdict')!r}")
    if skill.get("numbers_untraceable"):
        failures.append(f"traceable numbers were reported as untraceable: {skill['numbers_untraceable']}")

    rc, fabricated = run(CASES / "answer-fabricated.json", work / "fabricated.json")
    fab = fabricated.get("skill", {})
    observed["fabricated"] = {"grounding": fab.get("grounding"),
                              "untraceable": fab.get("numbers_untraceable"),
                              "verdict": fab.get("verdict")}
    if "91.4" not in (fab.get("numbers_untraceable") or []):
        failures.append("a fabricated number (91.4) was not flagged as untraceable")

    rc, hedge = run(CASES / "answer-hedge-stripped.json", work / "hedge.json")
    hg = hedge.get("skill", {})
    observed["hedge_stripped"] = {"coverage": hg.get("coverage"), "verdict": hg.get("verdict"),
                                  "numbers_claimed": hg.get("numbers_claimed")}
    if not hg.get("numbers_claimed"):
        failures.append("the weaker answer's numbers were not counted, so it was never measured")
    # The weaker answer is fully traceable, so the scorer must not pretend it is defective; it only
    # has to rank below the grounded answer, which carries the same facts plus the source's uncertainty.
    if hg.get("grounding") != 1.0:
        failures.append("a traceable but thinner answer was wrongly reported as ungrounded")

    rc, offtopic = run(CASES / "answer-off-topic.json", work / "offtopic.json")
    ot = offtopic.get("skill", {})
    observed["off_topic"] = {"coverage": ot.get("coverage"),
                             "untraceable": ot.get("numbers_untraceable")}
    if ot.get("coverage", 1.0) > 0.34:
        failures.append("an answer about unrelated material was credited with coverage")

    rc, compared = run(CASES / "answer-grounded.json", work / "compare.json",
                       baseline=CASES / "answer-hedge-stripped.json")
    cmp_ = compared.get("comparison", {})
    observed["comparison"] = {"verdict": cmp_.get("verdict"), "delta": cmp_.get("delta")}
    if cmp_.get("verdict") != "skill_stronger":
        failures.append(f"the grounded answer did not beat the weaker one: {cmp_.get('verdict')!r}")

    empty = work / "empty.md"
    empty.write_text("\n", encoding="utf-8")
    rc, refused = run(empty, work / "empty.json")
    observed["empty_answer"] = {"rc": rc, "refused": refused.get("refused")}
    if rc != 2:
        failures.append(f"an empty answer should be refused with exit 2, got rc={rc}")

    report = {
        "fixture": str(CASES),
        "checks": 7,
        "failures": failures,
        "observed": observed,
        "verdict": "pass" if not failures else "fail",
        "note": "Synthetic fixture only; not an organizer case, not an official result.",
    }
    (work / "gain-checks-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
