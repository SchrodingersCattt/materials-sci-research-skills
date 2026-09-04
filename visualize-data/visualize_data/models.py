"""Shared result and exit-code models for visualize-data."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any


class ExitCode(IntEnum):
    PASS = 0
    QA_FAILED = 1
    INPUT_ERROR = 2
    INTERNAL_ERROR = 3


@dataclass(frozen=True)
class Finding:
    rule: str
    level: str
    message: str
    panel: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    check: str
    findings: list[Finding] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return not any(item.level == "error" for item in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "passed": self.passed,
            "duration_seconds": self.duration_seconds,
            "metrics": self.metrics,
            "findings": [item.to_dict() for item in self.findings],
        }
