"""Synthetic reading fixture: a case with paragraphs, a field request and a question list.

Also writes a compliant answer and a defective answer so the self-test can prove the checker catches
guessed values, missing evidence, off-vocabulary statuses and quotations that are not in the source.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CASE = {
    "case_id": "SYN-READ-1",
    "task_instruction": "Synthetic interface fixture; not a formal case.",
    "paragraphs": [
        {"paragraph_id": "p1", "text": "The synthetic specimen A reached 31.2 MPa with a standard "
                                      "deviation of 1.4 MPa across six specimens."},
        {"paragraph_id": "p2", "text": "Specimen B reached 24.0 MPa with a standard deviation of "
                                      "1.1 MPa. Temperature was held at 25 C."},
        {"paragraph_id": "p3", "text": "The fixture reports no significance test and no "
                                      "long-term stability data."},
    ],
    "target_fields": [
        {"field_id": "strength_A", "description": "strength of specimen A", "unit": "MPa"},
        {"field_id": "strength_B", "description": "strength of specimen B", "unit": "MPa"},
        {"field_id": "temperature", "description": "test temperature", "unit": "C"},
        {"field_id": "p_value", "description": "reported significance"},
        {"field_id": "stability", "description": "long-term stability result"},
    ],
    "questions": [
        {"question_id": "q1", "text": "Which specimen was stronger, and by how much?"},
        {"question_id": "q2", "text": "Was a significance test reported?"},
    ],
    "required_fields": ["case_id", "status", "result", "claims", "uncertainties"],
}

GOOD_ANSWER = {
    "case_id": "SYN-READ-1",
    "status": "answered",
    "result": {"strength_A": "31.2 MPa", "strength_B": "24.0 MPa", "temperature": "25 C"},
    "fields": [
        {"field_id": "strength_A", "status": "reported", "value": "31.2", "unit": "MPa",
         "paragraph_id": "p1", "quote": "The synthetic specimen A reached 31.2 MPa"},
        {"field_id": "strength_B", "status": "reported", "value": "24.0", "unit": "MPa",
         "paragraph_id": "p2", "quote": "Specimen B reached 24.0 MPa"},
        {"field_id": "temperature", "status": "reported", "value": "25", "unit": "C",
         "paragraph_id": "p2", "quote": "Temperature was held at 25 C."},
        {"field_id": "p_value", "status": "not_reported", "value": None,
         "paragraph_id": "p3", "quote": "The fixture reports no significance test",
         "note": "the material states that no test is reported"},
        {"field_id": "stability", "status": "not_reported", "value": None,
         "paragraph_id": "p3", "quote": "no long-term stability data"},
    ],
    "questions": [
        {"question_id": "q1", "status": "answered",
         "answer": "Specimen A was stronger, by 7.2 MPa in the fixture.",
         "conditions": ["single synthetic batch", "six specimens per group"],
         "claims": [{"claim_id": "c1", "text": "Specimen A reached 31.2 MPa", "kind": "reported",
                     "evidence": [{"paragraph_id": "p1",
                                   "quote": "The synthetic specimen A reached 31.2 MPa"}]}],
         "unanswered_parts": []},
        {"question_id": "q2", "status": "answered",
         "answer": "No significance test is reported in the fixture.", "conditions": [],
         "claims": [{"claim_id": "c2", "text": "no significance test is reported",
                     "kind": "reported",
                     "evidence": [{"paragraph_id": "p3",
                                   "quote": "The fixture reports no significance test"}]}],
         "unanswered_parts": []},
    ],
    "claims": [{"claim_id": "c1", "kind": "reported", "text": "Specimen A reached 31.2 MPa",
                "evidence": [{"paragraph_id": "p1",
                              "quote": "The synthetic specimen A reached 31.2 MPa"}]}],
    "uncertainties": ["no significance test is reported", "no long-term stability data"],
}

BAD_ANSWER = {
    "case_id": "SYN-READ-1",
    "status": "answered",
    "result": {"strength_A": "31.2 MPa"},
    "fields": [
        {"field_id": "strength_A", "status": "reported", "value": "31.2", "unit": "MPa",
         "quote": "The synthetic specimen A reached 31.2 MPa"},
        {"field_id": "temperature", "status": "reported", "value": "25", "unit": "C",
         "paragraph_id": "p2", "quote": "the temperature was held at twenty-five degrees"},
        {"field_id": "p_value", "status": "not_reported", "value": "0.03"},
        {"field_id": "stability", "status": "guessed", "value": "stable"},
    ],
    "questions": [
        {"question_id": "q1", "status": "answered", "answer": "A was stronger.",
         "claims": [{"claim_id": "c9", "text": "A was stronger", "kind": "reported",
                     "evidence": []}]},
    ],
    "claims": [],
    "uncertainties": [],
    "note": "deliberately defective: strength_B is missing entirely, stability uses an "
            "off-vocabulary status, p_value carries a value while 'not_reported', temperature's "
            "quote is not verbatim and omits the digits of its value, strength_A has no locator, "
            "and q1 has no evidence for its reported claim",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "case.json").write_text(json.dumps(CASE, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "answer-good.json").write_text(json.dumps(GOOD_ANSWER, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    (out / "answer-bad.json").write_text(json.dumps(BAD_ANSWER, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    print(f"synthetic reading fixture written to {out}")
    print("Fixture only: no formal case, no official answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
