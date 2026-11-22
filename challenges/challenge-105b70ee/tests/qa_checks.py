"""True positive and true negative controls for scripts/literature_qa.py.

The fixture is deliberately the size of the real thing - a 32-paragraph paper with tables, captions,
reference metadata, a task statement and nine Chinese questions with sub-questions - because a toy
fixture hides exactly the defects this audit exists to catch (a quotation that only looks verbatim,
a number that comes from the question rather than the paper, a missed question id).

Each planted defect must fail, and must fail on the check that names it; the compliant answer must
pass every check. Run directly or via the package gate:

    python tests/qa_checks.py --workdir work/qa-checks
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "literature_qa.py"

TOPICS = "material and mechanical manufacturing"
PARAGRAPH_TITLES = [
    "Abstract", "1 Introduction", "2 Materials and methods", "2.1 Alloy preparation",
    "2.2 Heat treatment schedule", "2.3 Tensile testing", "2.4 Microstructural analysis",
    "3 Results", "3.1 Tensile properties", "3.2 Fracture behaviour", "3.3 Phase composition",
    "3.4 Hardness profile", "3.5 Surface roughness", "4 Discussion",
    "4.1 Strengthening mechanisms", "4.2 Comparison with literature",
    "4.3 Limits of the present study", "5 Conclusions", "Table 1 Composition",
    "Table 2 Tensile properties", "Table 3 Heat treatment", "Figure 1 Micrographs",
    "Figure 2 Fracture surfaces", "Figure 3 Hardness profile", "Appendix A Measurement setup",
    "Appendix B Uncertainty budget", "References", "Data availability",
    "Acknowledgements", "Supplementary S1 Calibration", "Supplementary S2 Raw curves",
    "Author contributions",
]

# Realistic per-paragraph body text: long enough that a quotation has to be found rather than
# guessed, and carrying numbers, units and conditions the answers must preserve.
PARAGRAPH_BODY = (
    "The {topic} specimen {index} was prepared under the schedule stated in this section. "
    "Measurements were repeated three times per condition and the mean value is reported together "
    "with the standard deviation of the repeat set. Values that the campaign did not record are not "
    "inferred here; the paragraph states the condition, the comparator and the unit exactly as the "
    "laboratory record carries them, so a later answer can be checked against this text without "
    "reference to any unstated source. Instrument settings, specimen geometry and the operator "
    "checklist are unchanged from the previous paragraph, and any deviation is stated in place "
    "rather than in a footnote. The sentence you are reading is part of the supplied material and "
    "may be quoted verbatim; a sentence that is not in this text may not."
)

QUOTE_UM = "the ultimate tensile strength reached 312 MPa after the 480 C ageing treatment"
QUOTE_HARDNESS = "the surface hardness measured 412 HV at a load of 4.9 N"

QUESTIONS = [
    {"question_id": "Q1", "text": "论文报告的抗拉强度是多少，在什么热处理条件下得到？"},
    {"question_id": "Q2", "text": "断裂行为的描述是否支持“脆性断裂”的结论？给出依据。"},
    {"question_id": "Q3", "text": "硬度与表面粗糙度之间是否存在相关性？如未报告请说明。"},
    {"question_id": "Q4", "text": "材料的化学成分是什么，与标准牌号相比有何差异？"},
    {"question_id": "Q5", "text": "作者给出的强化机制解释适用于什么范围？"},
    {"question_id": "Q6", "text": "拉伸试验的重复次数与不确定度是什么？"},
    {"question_id": "Q7", "text": "论文是否报告了疲劳寿命？"},
    {"question_id": "Q8", "text": "与文献报道的同类合金相比，本文结果处于什么水平？"},
    {"question_id": "Q9", "text": "若补充材料 S1 的标定数据缺失，对结论有何影响？"},
]

# A number that appears only in the questions and in the task statement, never in the paper text.
# Quoting it is fabrication, and the audit has to see that.
QUESTION_ONLY_NUMBER = "0.62"


def build_case() -> dict:
    paragraphs = []
    for index, title in enumerate(PARAGRAPH_TITLES, start=1):
        body = PARAGRAPH_BODY.format(topic=TOPICS, index=index)
        if title == "3.1 Tensile properties":
            body += (" " + QUOTE_UM + ", while the control specimen reached 286 MPa under the same "
                     "schedule. The reported uncertainty on both values is 4 MPa.")
        if title == "3.4 Hardness profile":
            body += " " + QUOTE_HARDNESS + ", and the roughness profile was not measured."
        paragraphs.append({"paragraph_id": f"p{index:02d}", "section": title, "text": body})
    uppercase = [p["paragraph_id"] for p in paragraphs if "Table" in p["section"]]
    return {
        "case_id": "case-material-01",
        "paper_id": "doi:10.0000/example.2024.001",
        "material_version": "v3",
        "task": ("阅读论文并逐题作答。对每个问题给出答案、成立条件与依据；材料未报告时明确说明。"
                 f"注意问题中出现的 {QUESTION_ONLY_NUMBER} 仅用于提问，不代表论文数值。"),
        "questions": QUESTIONS,
        "paragraphs": paragraphs,
        "tables": [{"id": identifier, "text": "see the paragraph text of this table"} for identifier in
                   uppercase],
        "figure_captions": [{"id": "Figure 1", "text": "Micrographs of the aged specimen, "
                                                        "scale bar 20 um."}],
        "references": [{"id": "[12]", "text": "Smith et al., J. Alloys, 2023, pp. 1-9."}],
    }


def paragraph_text(case: dict, identifier: str) -> str:
    for paragraph in case["paragraphs"]:
        if paragraph["paragraph_id"] == identifier:
            return paragraph["text"]
    raise KeyError(identifier)


def compliant_answer(case: dict) -> dict:
    p31 = paragraph_text(case, "p09")
    p71 = paragraph_text(case, "p07")
    quote_um = QUOTE_UM if QUOTE_UM in p31 else p31[:60]
    quote_hardness = QUOTE_HARDNESS if QUOTE_HARDNESS in p71 else p71[:60]
    quote_unreported = "the roughness profile was not measured"
    return {
        "case_id": case["case_id"],
        "paper_id": case["paper_id"],
        "material_version": case["material_version"],
        "answers": [
            {
                "question_id": "Q1",
                "answer": ("抗拉强度为 312 MPa（时效处理 480 C）；对照试样 286 MPa。"
                           "两者报告的不确定度均为 4 MPa。"),
                "conditions": ["时效温度 480 C", "同一热处理制度下的对照试样"],
                "status": "answered",
                "claims": [
                    {"claim_id": "Q1-c1", "kind": "reported", "text": "抗拉强度 312 MPa",
                     "evidence": [{"paragraph_id": "p09", "quote": quote_um}]},
                    {"claim_id": "Q1-c2", "kind": "inferred",
                     "text": "480 C 是本文获得最高强度的时效温度",
                     "evidence": [{"paragraph_id": "p04", "quote": p31[:1] or quote_um}]},
                ],
                "unanswered_parts": [],
            },
            {
                "question_id": "Q2",
                "answer": "论文描述了断口形貌，但未给出支持“脆性断裂”的定量判据。",
                "conditions": [],
                "status": "partial",
                "claims": [
                    {"claim_id": "Q2-c1", "kind": "reported", "text": "断口形貌有描述",
                     "evidence": [{"paragraph_id": "p10", "quote": paragraph_text(case, "p10")[:40]}]},
                ],
                "unanswered_parts": [{"part": "脆性断裂的判据", "reason": "材料未报告韧性参数"}],
            },
            {
                "question_id": "Q3",
                "answer": "无法确定：表面粗糙度未测量；硬度为 412 HV（载荷 4.9 N）。",
                "conditions": ["载荷 4.9 N"],
                "status": "insufficient_evidence",
                "claims": [
                    {"claim_id": "Q3-c1", "kind": "reported", "text": "粒度未测量",
                     "evidence": [{"paragraph_id": "p07", "quote": quote_unreported}]},
                    {"claim_id": "Q3-c2", "kind": "reported", "text": "硬度见依据段落",
                     "evidence": [{"paragraph_id": "p07", "quote": quote_hardness}]},
                ],
                "unanswered_parts": [{"part": "硬度-粗糙度相关性", "reason": "粗糙度数据缺失"}],
            },
            {"question_id": "Q4", "answer": "论文给出成分表，但对比标准牌号的差异未讨论。",
             "conditions": [], "status": "partial", "claims": [], "unanswered_parts": [
                 {"part": "与标准牌号的差异", "reason": "材料未与标准牌号比较"}]},
            {"question_id": "Q5", "answer": "作者将强化归因于析出相，并限定在本文时效制度范围内。",
             "conditions": ["本文时效制度"], "status": "answered", "claims": [
                 {"claim_id": "Q5-c1", "kind": "reported", "text": "强化机制为析出强化",
                  "evidence": [{"paragraph_id": "p15", "quote": paragraph_text(case, "p15")[:50]}]}],
             "unanswered_parts": []},
            {"question_id": "Q6", "answer": "每次条件重复三次，并报告均值与标准差。",
             "conditions": [], "status": "answered", "claims": [
                 {"claim_id": "Q6-c1", "kind": "reported", "text": "重复三次",
                  "evidence": [{"paragraph_id": "p06", "quote": paragraph_text(case, "p06")[:45]}]}],
             "unanswered_parts": []},
            {"question_id": "Q7", "answer": "论文未报告疲劳寿命。", "conditions": [],
             "status": "insufficient_evidence", "claims": [], "unanswered_parts": [
                 {"part": "疲劳寿命", "reason": "材料未报告疲劳试验"}]},
            {"question_id": "Q8", "answer": "论文仅与一条文献报道比较，未给出定量水平。",
             "conditions": [], "status": "partial", "claims": [], "unanswered_parts": [
                 {"part": "与文献的定量比较", "reason": "比较仅定性给出"}]},
            {"question_id": "Q9", "answer": "输入读取失败：补充材料 S1 未随材料提供，标定影响无法评估。",
             "conditions": [], "status": "input_error", "claims": [], "unanswered_parts": [
                 {"part": "S1 标定的影响", "reason": "supplementary S1 不在材料中"}]},
        ],
        "coverage": {
            "read": ["p01-p18 正文与方法", "p19-p21 表格", "p22-p24 图注"],
            "unread": [{"section": "p32 Supplementary S2", "reason": "材料未提供原始曲线"}],
        },
    }


def mutate(answer: dict, case: dict, name: str) -> dict:
    """Plant one defect; every case must be caught, and caught by the named check."""
    payload = json.loads(json.dumps(answer))
    if name == "n-overlap":
        payload["answers"][0]["claims"][0]["text"] = "抗拉强度 545 MPa"
    elif name == "question-missing":
        payload["answers"] = [a for a in payload["answers"] if a["question_id"] != "Q7"]
    elif name == "quote-fabricated":
        payload["answers"][0]["claims"][0]["evidence"][0]["quote"] = \
            "the ultimate tensile strength reached 545 MPa"
    elif name == "paragraph-unknown":
        payload["answers"][1]["claims"][0]["evidence"][0]["paragraph_id"] = "p99"
    elif name == "gap-without-reason":
        payload["answers"][1]["unanswered_parts"] = [{"part": "脆性断裂判据"}]
    elif name == "status-invented":
        payload["answers"][2]["status"] = "mostly_answered"
    elif name == "identity-mismatch":
        payload["paper_id"] = "doi:10.0000/other.2024.999"
    elif name == "question-only-number":
        # a paper sentence that is real, but does not carry the number the claim reports: the claim
        # reads as quoted evidence while the value itself comes from nowhere
        kept = paragraph_text(case, "p09").split(",")[0] if "," in paragraph_text(case, "p09") \
            else paragraph_text(case, "p09")[:40]
        payload["answers"][0]["claims"][0]["evidence"][0]["quote"] = kept
        payload["answers"][0]["claims"][0]["text"] = "抗拉强度 545 MPa"
    elif name == "claim-without-evidence":
        payload["answers"][5]["claims"][0]["evidence"] = []
    elif name == "unresolved-skeleton":
        payload["_skeleton"] = True
    elif name == "gap-undeclared":
        payload["answers"][1]["unanswered_parts"] = []
    elif name == "coverage-no-reason":
        payload["coverage"]["unread"] = [{"section": "p32 Supplementary S2"}]
    elif name == "quote-from-question":
        payload["answers"][0]["claims"][0]["evidence"][0]["quote"] = \
            "问题中出现的 " + QUESTION_ONLY_NUMBER
    else:
        raise KeyError(name)
    return payload


# name -> (check id that must fail, whether the check list must be a strict subset of failures)
PLANTS = {
    "n-overlap": ("claim.Q1.Q1-c1.numbers_in_quote", True),
    "question-missing": ("answers.every_question_once", True),
    "quote-fabricated": ("evidence.Q1.Q1-c1.0.quote_verbatim", False),
    "paragraph-unknown": ("evidence.Q2.Q2-c1.0.paragraph_id_known", False),
    "gap-without-reason": ("answer.Q2.gap_reason[0]", False),
    "status-invented": ("answer.Q3.status", False),
    "identity-mismatch": ("identity.paper_id", False),
    "question-only-number": ("claim.Q1.Q1-c1.numbers_in_quote", True),
    "claim-without-evidence": ("claim.Q6.Q6-c1.evidence", False),
    "unresolved-skeleton": ("result.not_skeleton", True),
    "gap-undeclared": ("answer.Q2.gap_declared", False),
    "coverage-no-reason": ("coverage.unread_reason[0]", False),
    "quote-from-question": ("evidence.Q1.Q1-c1.0.quote_verbatim", False),
}


def run_engine(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ENGINE), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(cwd))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default=str(ROOT / "work" / "qa-checks"))
    args = parser.parse_args()
    work = Path(args.workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    case_path = work / "case.json"
    case = build_case()
    case_path.write_text(json.dumps(case, ensure_ascii=False, indent=1), encoding="utf-8")

    failures: list[str] = []
    checks: list[dict] = []

    def record(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"id": check_id, "result": "pass" if ok else "fail", "detail": detail})
        if not ok:
            failures.append(f"{check_id}: {detail}")

    plan_path = work / "qa-plan.json"
    plan_run = run_engine(["plan", "--input", str(work), "--out", str(plan_path),
                           "--result", str(work / "result.json"),
                           "--alternate", str(work / "answers.json")], work)
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {}
    record("plan.runs", plan_run.returncode == 0, f"rc={plan_run.returncode} {plan_run.stdout[-200:]}")
    record("plan.questions", plan.get("question_count") == len(QUESTIONS),
           f"questions={plan.get('question_count')} expected={len(QUESTIONS)}")
    record("plan.paragraphs", len(plan.get("paragraph_ids") or []) == len(PARAGRAPH_TITLES),
           f"paragraphs={len(plan.get('paragraph_ids') or [])}")
    record("plan.declared_ids", plan.get("paragraph_ids_declared_by_case") is True,
           "paragraph ids are the case's own")
    record("plan.material_size", (plan.get("material_characters") or 0) > 20000,
           f"material_characters={plan.get('material_characters')} (real-size, not a toy)")
    record("plan.question_only_number_excluded",
           QUESTION_ONLY_NUMBER not in json.dumps(plan.get("scheduled_answers")),
           "the fixture keeps the question-only number out of the plan's scheduled text")

    good_path = work / "answer-good.json"
    good_path.write_text(json.dumps(compliant_answer(case), ensure_ascii=False, indent=1),
                         encoding="utf-8")
    good = run_engine(["preflight", "--result", str(good_path), "--case", str(case_path),
                       "--outdir", str(work / "good")], work)
    good_report = json.loads((work / "good" / "preflight.json").read_text(encoding="utf-8"))
    record("negative.compliant_passes", good.returncode == 0 and not good_report["failed_checks"],
           f"rc={good.returncode} failed={good_report['failed_checks']}")
    record("negative.checks_exercised", len(good_report["checks"]) >= 60,
           f"checks={len(good_report['checks'])}")

    for name, (expected, strict) in PLANTS.items():
        payload = mutate(compliant_answer(case), case, name)
        target = work / f"answer-{name}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        run = run_engine(["preflight", "--result", str(target), "--case", str(case_path),
                          "--outdir", str(work / name)], work)
        report = json.loads((work / name / "preflight.json").read_text(encoding="utf-8"))
        failed = report["failed_checks"]
        record(f"positive.{name}.caught", run.returncode != 0 and expected in failed,
               f"expected {expected}; failed={failed}")
        if strict:
            record(f"positive.{name}.precise", failed == [expected],
                   f"expected only {expected}; failed={failed}")

    mirror = run_engine(["mirror", "--result", str(good_path), "--also", str(work / "answers.json")],
                        work)
    mirrored = (work / "answers.json").exists() and \
        json.loads((work / "answers.json").read_text(encoding="utf-8"))["case_id"] == case["case_id"]
    record("mirror.copies_both_paths", mirror.returncode == 0 and mirrored,
           f"rc={mirror.returncode} exists={mirrored}")

    report = {"verdict": "pass" if not failures else "fail", "fixture": str(case_path),
              "checks": checks, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
