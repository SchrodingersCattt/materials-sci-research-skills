from __future__ import annotations

import json
import shutil
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


def copy_fixture(tmp_path: Path) -> tuple[dict, Path]:
    document = json.loads(VALID.read_text(encoding="utf-8"))
    shutil.copytree(VALID.parent / "_evidence", tmp_path / "_evidence")
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return document, path


def test_frozen_fixture_passes_schema_and_freeze_gate() -> None:
    result = run_validator(VALID, 0)
    assert "PASS" in result.stdout


def test_draft_template_is_undecided_and_validates_without_answers() -> None:
    result = run_validator(ROOT / "templates" / "BENCHMARK_SPEC.yaml", 0)
    assert "PASS" in result.stdout
    assert "model: undecided" in (ROOT / "templates" / "BENCHMARK_SPEC.yaml").read_text(encoding="utf-8")


def test_frozen_spec_rejects_unresolved_questions(tmp_path: Path) -> None:
    document, path = copy_fixture(tmp_path)
    document["unresolved"] = [{"path": "evaluation.metrics[0]", "question": "Which unit?", "state": "pending"}]
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_validator(path, 1)
    assert "unresolved" in result.stdout


def test_frozen_spec_requires_substantive_review_and_verified_evidence(tmp_path: Path) -> None:
    document, path = copy_fixture(tmp_path)
    document["reviews"] = []
    document["freeze_evidence"]["example_check"]["artifact_sha256"] = "0" * 64
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_validator(path, 1)
    assert "accepted substantive review" in result.stdout
    assert "digest does not match" in result.stdout


def test_fabricated_pass_fields_do_not_bypass_artifact_checks(tmp_path: Path) -> None:
    document, path = copy_fixture(tmp_path)
    document["validation"]["schema"]["input_sha256"] = "0" * 64
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_validator(path, 1)
    assert "not bound to this specification" in result.stdout


def test_missing_jsonschema_fails_closed() -> None:
    result = subprocess.run([sys.executable, "-S", str(VALIDATOR), str(VALID)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1
    assert "jsonschema is required" in result.stdout


def test_required_bundle_and_protocol_are_present() -> None:
    for relative in (
        "SKILL.md", "requirements.txt", "templates/BENCHMARK_SPEC.md", "templates/BENCHMARK_SPEC.yaml",
        "templates/DECISIONS.md", "THREAT_MODEL.md", "EXAMPLES.md", "schemas/benchmark-spec.schema.json",
        "references/scientific-validity.md", "references/benchmark-design.md",
        "references/metric-and-ranking-design.md", "references/threat-model.md",
        "tests/interaction_evals.json",
    ):
        assert (ROOT / relative).exists(), relative
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "does not generate tasks" in text
    assert "one unresolved" in text
    assert "ordinary scientific" in text


def test_interaction_evals_cover_activation_and_recovery() -> None:
    cases = json.loads((ROOT / "tests" / "interaction_evals.json").read_text(encoding="utf-8"))
    assert sum(case.get("activate") is True for case in cases) >= 3
    assert sum(case.get("activate") is False for case in cases) >= 3
    recovery = {case["id"]: case.get("expected", []) for case in cases if "expected" in case}
    assert {"recovery-unsure", "recovery-conflict", "recovery-pause", "recovery-no-oracle"} <= recovery.keys()
    assert all(recovery[key] for key in recovery)
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    examples = (ROOT / "EXAMPLES.md").read_text(encoding="utf-8")
    for marker in ("unsure", "superseding", "disputed", "blocked", "pause", "conflict"):
        assert marker in skill.lower() or marker in examples.lower(), marker
