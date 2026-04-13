"""Shared CheckContext + subprocess helper."""
from __future__ import annotations

import locale
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

from .env import EnvironmentInfo
from .provider import ProviderStatus

_DEFAULT_TIMEOUT = 30


def _console_encoding() -> str:
    """Best-effort child-process console encoding.

    Windows child processes write stderr in the legacy OEM/ACP code page
    (cp949 on Korean systems), not utf-8 — decoding as utf-8 produces
    mojibake. We probe the preferred encoding and fall back sanely.
    """
    if sys.platform != "win32":
        return "utf-8"
    enc = locale.getpreferredencoding(False) or ""
    if enc and enc.lower() not in ("ascii", "us-ascii"):
        return enc
    return "cp949"


_CHILD_ENC = _console_encoding()


@dataclass
class CheckContext:
    env: EnvironmentInfo
    provider_statuses: list = field(default_factory=list)
    actual_provider: Optional[ProviderStatus] = None
    opencode_json: Optional[dict] = None
    omo_config: Optional[dict] = None
    auto_fix: bool = False


def run_command(cmd: list, timeout: int = _DEFAULT_TIMEOUT) -> tuple:
    """Run command → (rc, stdout, stderr). Shell fallback on FileNotFoundError.

    Ported from v2.31. Never raises — returns negative rc on errors.
    Decodes child output with the platform console encoding (cp949 on
    Korean Windows), not utf-8, to avoid mojibake.
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding=_CHILD_ENC,
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return -2, "", f"TIMEOUT after {timeout}s: {' '.join(str(a) for a in cmd)}"
    except FileNotFoundError:
        cmdline = " ".join(shlex.quote(str(x)) for x in cmd)
        try:
            proc = subprocess.run(
                cmdline,
                capture_output=True,
                text=True,
                encoding=_CHILD_ENC,
                errors="replace",
                shell=True,
                timeout=timeout,
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            return -2, "", f"TIMEOUT after {timeout}s: {cmdline}"
        except Exception as exc:
            return -3, "", str(exc)
    except Exception as exc:
        return -3, "", str(exc)
