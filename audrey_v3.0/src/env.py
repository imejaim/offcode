"""Environment self-awareness (VDI / desktop / laptop / blackwell)."""
from __future__ import annotations

import platform
import socket
import subprocess
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class EnvironmentInfo:
    kind: str
    hostname: str
    os: str
    ip_hints: list
    gpu_hint: Optional[str]
    reasoning: str

    def to_dict(self) -> dict:
        return asdict(self)


def _ip_hints() -> list:
    hints: list = []
    try:
        host = socket.gethostname()
        for info in socket.getaddrinfo(host, None):
            ip = info[4][0]
            if ip and ip not in hints and not ip.startswith("127.") and ":" not in ip:
                hints.append(ip)
    except Exception:
        pass
    return hints


def _gpu_hint() -> Optional[str]:
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="ignore",
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip().splitlines()[0].strip()
    except Exception:
        return None
    return None


def detect_environment(hint: str = "auto") -> EnvironmentInfo:
    host = socket.gethostname()
    os_name = platform.system()
    ips = _ip_hints()
    gpu = _gpu_hint()

    if hint != "auto":
        return EnvironmentInfo(
            kind=hint,
            hostname=host,
            os=os_name,
            ip_hints=ips,
            gpu_hint=gpu,
            reasoning=f"forced hint={hint}",
        )

    host_upper = host.upper()
    if "VDI" in host_upper or any(ip.startswith("10.44.") for ip in ips):
        return EnvironmentInfo("vdi", host, os_name, ips, gpu, "hostname/IP indicates VDI")

    if os_name == "Linux" and gpu and "Blackwell" in gpu:
        return EnvironmentInfo("blackwell", host, os_name, ips, gpu, "Linux + nvidia Blackwell")

    if os_name == "Windows":
        if any(ip.startswith("10.88.21.") for ip in ips):
            return EnvironmentInfo(
                "desktop", host, os_name, ips, gpu, "Windows + 10.88.21.* desktop subnet"
            )
        if gpu and "4070" in gpu:
            return EnvironmentInfo("laptop", host, os_name, ips, gpu, "Windows + RTX 4070")
        if any(ip.startswith("10.88.22.208") for ip in ips):
            return EnvironmentInfo("laptop", host, os_name, ips, gpu, "Windows + laptop IP")

    return EnvironmentInfo("unknown", host, os_name, ips, gpu, "no rule matched")
