"""AGENTIS_READY 5-axis verdict."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .result import STATUS_FAIL, STATUS_PASS, STATUS_WARN


REQUIRED_IDS = ("A1", "B3", "B5", "C2", "F2")


@dataclass
class Verdict:
    ready: bool
    reasons: list
    warnings: list

    def to_dict(self) -> dict:
        return asdict(self)


def _by_id(results: list) -> dict:
    return {r.id: r for r in results}


def judge(results: list) -> Verdict:
    by_id = _by_id(results)
    reasons: list = []
    warnings: list = []

    for rid in REQUIRED_IDS:
        r = by_id.get(rid)
        if r is None:
            reasons.append(f"{rid} missing")
            continue
        if r.status == STATUS_FAIL:
            reasons.append(f"{rid} FAIL: {r.detail}")

    for r in results:
        if r.id in REQUIRED_IDS:
            continue
        if r.status in (STATUS_FAIL, STATUS_WARN):
            warnings.append(f"{r.status} {r.id} {r.name}: {r.detail}")

    return Verdict(ready=len(reasons) == 0, reasons=reasons, warnings=warnings)
