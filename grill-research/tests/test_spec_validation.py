from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "fixtures" / "valid_benchmark_spec.json"
VALIDATOR = ROOT / "scripts" / "validate_spec.py"


def run_validator(path: Path, expected: int) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def test_frozen_fixture_passes_schema_and_freeze_gate() -> None:
    result = run_validator(VALID, 0)
    assert "PASS" in result.stdout


def test_frozen_spec_rejects_unresolved_questions(tmp_path: Path) -> None:
    document = json.loads(VALID.read_text(encoding="utf-8"))
    document["unresolved"] = [{"path": "evaluation.metrics[0]", "question": "Which unit?", "state": "pending"}]
    path = tmp_path / "unresolved.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_validator(path, 1)
    assert "unresolved" in result.stdout


def test_frozen_spec_requires_substantive_review_and_evidence(tmp_path: Path) -> None:
    document = json.loads(VALID.read_text(encoding="utf-8"))
    document["reviews"] = []
    document["freeze_evidence"]["example_check"] = ""
    path = tmp_path / "unreviewed.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_validator(path, 1)
    assert "accepted substantive review" in result.stdout
    assert "freeze evidence" in result.stdout


def test_required_bundle_and_protocol_are_present() -> None:
    for relative in (
        "SKILL.md", "BENCHMARK_SPEC.md", "BENCHMARK_SPEC.yaml", "DECISIONS.md",
        "THREAT_MODEL.md", "EXAMPLES.md", "schemas/benchmark-spec.schema.json",
        "references/scientific-validity.md", "references/benchmark-design.md",
        "references/metric-and-ranking-design.md", "references/threat-model.md",
    ):
        assert (ROOT / relative).exists(), relative
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "does not generate tasks" in text
    assert "one unresolved" in text
