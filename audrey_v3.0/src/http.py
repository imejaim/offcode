"""Stdlib HTTP helpers (GET/POST JSON) with timeout + proxy env respect."""
from __future__ import annotations

import json as _json
import time
import urllib.error
import urllib.request
from typing import Any, Optional


def http_get(url: str, timeout: float = 10.0, headers: Optional[dict] = None) -> tuple[int, str, Optional[int]]:
    """GET url → (status_code, body_or_err, latency_ms).

    status == -1 means transport error; body holds the message.
    Honors HTTP(S)_PROXY env vars via urllib's default handlers.
    """
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, method="GET", headers=req_headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc), int((time.time() - t0) * 1000)
    except Exception as exc:
        return -1, str(exc), int((time.time() - t0) * 1000)


def http_post_json(
    url: str,
    payload: dict,
    timeout: float = 30.0,
    headers: Optional[dict] = None,
) -> tuple[int, str, Optional[int]]:
    """POST JSON → (status_code, body_or_err, latency_ms)."""
    data = _json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc), int((time.time() - t0) * 1000)
    except Exception as exc:
        return -1, str(exc), int((time.time() - t0) * 1000)


def parse_json(body: str) -> Optional[Any]:
    try:
        return _json.loads(body)
    except Exception:
        return None
