"""CheckResult + status/category constants."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"

STATUSES = frozenset({STATUS_PASS, STATUS_WARN, STATUS_FAIL, STATUS_SKIP})

CATEGORY_ENV = "env"
CATEGORY_INFRA = "infra"
CATEGORY_OPENCODE = "opencode"
CATEGORY_OMO = "omo"
CATEGORY_LOGS = "logs"
CATEGORY_MODEL = "model"
CATEGORY_E2E = "e2e"

CATEGORIES = [
    CATEGORY_ENV,
    CATEGORY_INFRA,
    CATEGORY_OPENCODE,
    CATEGORY_OMO,
    CATEGORY_LOGS,
    CATEGORY_MODEL,
    CATEGORY_E2E,
]

CATEGORY_LABELS = {
    CATEGORY_ENV: "ENV",
    CATEGORY_INFRA: "INFRA",
    CATEGORY_OPENCODE: "OPENCODE",
    CATEGORY_OMO: "OMO",
    CATEGORY_LOGS: "LOGS",
    CATEGORY_MODEL: "MODEL",
    CATEGORY_E2E: "E2E",
}


@dataclass
class CheckResult:
    id: str
    name: str
    status: str
    detail: str
    category: str
    fix: Optional[str] = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
