"""Provider abstraction + parallel discovery."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from .http import http_get, parse_json


@dataclass
class Provider:
    name: str
    kind: str
    base_url: str
    priority: int = 1
    required: bool = False
    expected_models: list = field(default_factory=list)

    @property
    def models_url(self) -> str:
        return self.base_url.rstrip("/") + "/v1/models"

    @property
    def chat_url(self) -> str:
        return self.base_url.rstrip("/") + "/v1/chat/completions"


@dataclass
class ProviderStatus:
    provider: Provider
    alive: bool
    served_models: list
    latency_ms: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.provider.name,
            "kind": self.provider.kind,
            "base_url": self.provider.base_url,
            "priority": self.provider.priority,
            "required": self.provider.required,
            "expected_models": list(self.provider.expected_models),
            "alive": self.alive,
            "served_models": list(self.served_models),
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


def _probe_one(provider: Provider, timeout: float) -> ProviderStatus:
    code, body, latency = http_get(provider.models_url, timeout=timeout)
    if code == 200:
        data = parse_json(body) or {}
        served = []
        for m in (data.get("data") or []):
            if isinstance(m, dict) and isinstance(m.get("id"), str):
                served.append(m["id"])
        return ProviderStatus(provider=provider, alive=True, served_models=served, latency_ms=latency)
    err = f"HTTP {code}: {body[:120]}" if code != -1 else body[:160]
    return ProviderStatus(
        provider=provider,
        alive=False,
        served_models=[],
        latency_ms=latency,
        error=err,
    )


def discover_providers(providers: list, timeout: float = 3.0) -> list:
    """Probe every provider in parallel. Never raises."""
    if not providers:
        return []
    results: dict = {}
    with ThreadPoolExecutor(max_workers=max(2, len(providers))) as pool:
        futs = {pool.submit(_probe_one, p, timeout): p for p in providers}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                results[p.name] = fut.result()
            except Exception as exc:
                results[p.name] = ProviderStatus(
                    provider=p, alive=False, served_models=[], error=str(exc)
                )
    return [results[p.name] for p in providers]


def pick_actual_provider(statuses: list) -> Optional[ProviderStatus]:
    """Pick alive provider: priority ascending, tie-broken by name alphabetically.

    Tie-breaker locked in DESIGN §9.1 (2026-04-13) so R4 regression is deterministic.
    """
    alive = [s for s in statuses if s.alive]
    if not alive:
        return None
    alive.sort(key=lambda s: (s.provider.priority, s.provider.name))
    return alive[0]
