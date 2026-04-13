"""v2/v3 config loader + migration + JSONC parser (ported from v2.31)."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .provider import Provider


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p)))


def read_jsonc(path: Path) -> Optional[dict]:
    """JSONC parser (strings-aware). Ported from v2.31.

    Handles BOM, line comments, block comments, trailing commas.
    """
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return None
    cleaned_lines: list = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        in_string = False
        escape = False
        out_chars: list = []
        i = 0
        while i < len(line):
            ch = line[i]
            if escape:
                out_chars.append(ch)
                escape = False
                i += 1
                continue
            if ch == "\\" and in_string:
                out_chars.append(ch)
                escape = True
                i += 1
                continue
            if ch == '"':
                in_string = not in_string
                out_chars.append(ch)
                i += 1
                continue
            if not in_string and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break
            out_chars.append(ch)
            i += 1
        cleaned_lines.append("".join(out_chars))
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


@dataclass
class E2EConfig:
    enabled: bool = True
    agents: list = field(default_factory=lambda: ["sisyphus"])
    prompt: str = "ping"
    timeout_sec: int = 60


@dataclass
class Config:
    schema_version: int
    providers: list
    opencode_config_dir: Path
    expected_plugin: str
    environment_hint: str
    e2e: E2EConfig
    source_path: Optional[Path] = None
    migrated_from_v2: bool = False


def migrate_v2_to_v3(v2: dict) -> dict:
    """v2 flat dict → v3 dict. No disk writes."""
    vllm_url = v2.get("vllm_url", "http://127.0.0.1:8000")
    vllm_model = v2.get("vllm_model", "")
    return {
        "schema_version": 3,
        "providers": [
            {
                "name": "vllm",
                "kind": "openai_compatible",
                "base_url": vllm_url,
                "priority": 1,
                "required": False,
                "expected_models": [vllm_model] if vllm_model else [],
            }
        ],
        "opencode_config_dir": v2.get("opencode_config_dir", "~/.config/opencode"),
        "expected_plugin": v2.get("expected_plugin", "oh-my-openagent"),
        "environment_hint": "auto",
        "e2e": {
            "enabled": True,
            "agents": ["sisyphus"],
            "prompt": "ping",
            "timeout_sec": 60,
        },
    }


def _parse_providers(raw: Any) -> list:
    if not isinstance(raw, list):
        raise ValueError("providers must be a list")
    out: list = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"providers[{idx}] must be an object")
        name = item.get("name")
        base_url = item.get("base_url")
        if not name or not base_url:
            raise ValueError(f"providers[{idx}] requires name and base_url")
        out.append(
            Provider(
                name=str(name),
                kind=str(item.get("kind", "openai_compatible")),
                base_url=str(base_url),
                priority=int(item.get("priority", 1)),
                required=bool(item.get("required", False)),
                expected_models=list(item.get("expected_models", []) or []),
            )
        )
    return out


def _dict_to_config(data: dict, source: Optional[Path], migrated: bool) -> Config:
    schema_version = int(data.get("schema_version", 0))
    providers = _parse_providers(data.get("providers", []))
    e2e_raw = data.get("e2e", {}) or {}
    e2e = E2EConfig(
        enabled=bool(e2e_raw.get("enabled", True)),
        agents=list(e2e_raw.get("agents", ["sisyphus"]) or ["sisyphus"]),
        prompt=str(e2e_raw.get("prompt", "ping")),
        timeout_sec=int(e2e_raw.get("timeout_sec", 60)),
    )
    return Config(
        schema_version=schema_version,
        providers=providers,
        opencode_config_dir=expand_path(str(data.get("opencode_config_dir", "~/.config/opencode"))),
        expected_plugin=str(data.get("expected_plugin", "oh-my-openagent")),
        environment_hint=str(data.get("environment_hint", "auto")),
        e2e=e2e,
        source_path=source,
        migrated_from_v2=migrated,
    )


def load_config(path: Path) -> Config:
    """Read JSON/JSONC config. Auto-migrates v2 → v3 in-memory."""
    if not path.exists():
        raise ValueError(f"config not found: {path}")
    data = read_jsonc(path)
    if data is None:
        raise ValueError(f"failed to parse config: {path}")
    if "schema_version" not in data and "vllm_url" in data:
        return _dict_to_config(migrate_v2_to_v3(data), source=path, migrated=True)
    if int(data.get("schema_version", 0)) == 3:
        return _dict_to_config(data, source=path, migrated=False)
    raise ValueError(
        f"unknown config schema: schema_version={data.get('schema_version')}, keys={list(data.keys())[:5]}"
    )


def default_config() -> Config:
    """In-memory fallback when no --config is provided."""
    data = {
        "schema_version": 3,
        "providers": [
            {
                "name": "ollama",
                "kind": "openai_compatible",
                "base_url": "http://127.0.0.1:11434",
                "priority": 1,
                "required": False,
                "expected_models": [],
            }
        ],
        "opencode_config_dir": "~/.config/opencode",
        "expected_plugin": "oh-my-openagent",
        "environment_hint": "auto",
        "e2e": {"enabled": True, "agents": ["sisyphus"], "prompt": "ping", "timeout_sec": 60},
    }
    return _dict_to_config(data, source=None, migrated=False)
