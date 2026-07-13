"""Minimal, rate-limited and token-safe Tushare HTTP client."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Callable
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

import pandas as pd


API_URL = "https://api.tushare.pro"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
Transport = Callable[[dict[str, Any], int], bytes]


@dataclass
class ProbeCall:
    interface: str
    request_parameters_sanitized: dict[str, Any]
    request_sequence: int
    response_status: str
    permission_status: str
    retrieved_at: str
    query_hash: str
    raw_payload_hash: str
    frame: pd.DataFrame = field(repr=False)
    raw_payload: dict[str, Any] = field(repr=False)
    error_class: str = ""
    error_message_sanitized: str = ""
    attempts: int = 1

    @property
    def row_count(self) -> int:
        return int(len(self.frame))


class TushareMinimalClient:
    def __init__(
        self,
        *,
        project_root: Path,
        max_requests: int,
        timeout_seconds: int = 25,
        request_interval_seconds: float = 0.35,
        max_network_retries: int = 1,
        token: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self._token = token if token is not None else load_token(self.project_root)
        self.max_requests = int(max_requests)
        self.timeout_seconds = int(timeout_seconds)
        self.request_interval_seconds = float(request_interval_seconds)
        self.max_network_retries = int(max_network_retries)
        self.transport = transport or _http_transport
        self.request_count = 0
        self._last_request_monotonic = 0.0

    @property
    def token_configured(self) -> bool:
        return bool(self._token)

    def request(self, interface: str, params: dict[str, Any], fields: str) -> ProbeCall:
        sanitized_params = sanitize_params(params)
        query_hash = canonical_hash({"interface": interface, "params": sanitized_params, "fields": fields})
        retrieved_at = datetime.now(SHANGHAI_TZ).isoformat(timespec="seconds")
        if not self._token:
            return ProbeCall(
                interface=interface,
                request_parameters_sanitized=sanitized_params,
                request_sequence=self.request_count,
                response_status="BLOCKED_TOKEN_MISSING",
                permission_status="TOKEN_MISSING",
                retrieved_at=retrieved_at,
                query_hash=query_hash,
                raw_payload_hash="",
                frame=pd.DataFrame(),
                raw_payload={},
                error_class="TOKEN_MISSING",
                error_message_sanitized="Tushare token is not configured.",
                attempts=0,
            )
        if self.request_count >= self.max_requests:
            raise RuntimeError(f"API request budget exceeded: max_requests={self.max_requests}")

        request_payload = {
            "api_name": interface,
            "token": self._token,
            "params": params,
            "fields": fields,
        }
        attempts = 0
        last_error: Exception | None = None
        while attempts <= self.max_network_retries:
            if self.request_count >= self.max_requests:
                raise RuntimeError(f"API request budget exceeded: max_requests={self.max_requests}")
            attempts += 1
            self._respect_rate_limit()
            self.request_count += 1
            try:
                body = self.transport(request_payload, self.timeout_seconds)
                self._last_request_monotonic = time.monotonic()
                raw_hash = hashlib.sha256(body).hexdigest()
                decoded = json.loads(body.decode("utf-8", errors="replace"))
                return self._decode_response(
                    interface=interface,
                    sanitized_params=sanitized_params,
                    query_hash=query_hash,
                    retrieved_at=retrieved_at,
                    raw_hash=raw_hash,
                    payload=decoded,
                    attempts=attempts,
                )
            except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                self._last_request_monotonic = time.monotonic()
                last_error = exc
                if attempts > self.max_network_retries:
                    break
            except (json.JSONDecodeError, UnicodeError, TypeError, ValueError) as exc:
                self._last_request_monotonic = time.monotonic()
                last_error = exc
                break
        message = sanitize_message(str(last_error or "network request failed"), self._token)
        return ProbeCall(
            interface=interface,
            request_parameters_sanitized=sanitized_params,
            request_sequence=self.request_count,
            response_status="NETWORK_FAILED",
            permission_status="UNKNOWN",
            retrieved_at=retrieved_at,
            query_hash=query_hash,
            raw_payload_hash="",
            frame=pd.DataFrame(),
            raw_payload={},
            error_class=type(last_error).__name__ if last_error else "NETWORK_ERROR",
            error_message_sanitized=message,
            attempts=attempts,
        )

    def _decode_response(
        self,
        *,
        interface: str,
        sanitized_params: dict[str, Any],
        query_hash: str,
        retrieved_at: str,
        raw_hash: str,
        payload: dict[str, Any],
        attempts: int,
    ) -> ProbeCall:
        raw_code = payload.get("code", -1)
        code = int(-1 if raw_code is None else raw_code)
        message = sanitize_message(str(payload.get("msg", "")), self._token)
        if code != 0:
            permission_blocked = is_permission_error(message)
            return ProbeCall(
                interface=interface,
                request_parameters_sanitized=sanitized_params,
                request_sequence=self.request_count,
                response_status="PERMISSION_BLOCKED" if permission_blocked else "VALIDATION_FAILED",
                permission_status="PERMISSION_BLOCKED" if permission_blocked else "API_ERROR",
                retrieved_at=retrieved_at,
                query_hash=query_hash,
                raw_payload_hash=raw_hash,
                frame=pd.DataFrame(),
                raw_payload=_sanitized_response(payload, self._token),
                error_class="PERMISSION_ERROR" if permission_blocked else "API_ERROR",
                error_message_sanitized=message,
                attempts=attempts,
            )
        table = payload.get("data") or {}
        table_fields = table.get("fields") or []
        items = table.get("items") or []
        frame = pd.DataFrame(items, columns=table_fields)
        return ProbeCall(
            interface=interface,
            request_parameters_sanitized=sanitized_params,
            request_sequence=self.request_count,
            response_status="ACCESS_PASS" if not frame.empty else "EMPTY_UNEXPECTED",
            permission_status="ACCESS_PASS",
            retrieved_at=retrieved_at,
            query_hash=query_hash,
            raw_payload_hash=raw_hash,
            frame=frame,
            raw_payload=_sanitized_response(payload, self._token),
            attempts=attempts,
        )

    def _respect_rate_limit(self) -> None:
        if not self._last_request_monotonic:
            return
        remaining = self.request_interval_seconds - (time.monotonic() - self._last_request_monotonic)
        if remaining > 0:
            time.sleep(remaining)


def load_token(project_root: Path) -> str:
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if token:
        return token
    env_path = project_root / ".env"
    if not env_path.exists():
        return ""
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            if key == "TUSHARE_TOKEN":
                return value.strip().strip('"').strip("'")
    except OSError:
        return ""
    return ""


def sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in sorted(params.items()):
        if "token" in str(key).lower() or "auth" in str(key).lower():
            result[str(key)] = "***"
        else:
            result[str(key)] = value
    return result


def sanitize_message(message: str, token: str = "") -> str:
    text = str(message)
    if token:
        text = text.replace(token, "***")
    text = re.sub(r"(?i)(token\s*[=:]\s*)[^\s,;]+", r"\1***", text)
    return text.replace("\n", " ")[:500]


def is_permission_error(message: str) -> bool:
    lowered = message.lower()
    markers = ("无权限", "没有权限", "权限", "积分", "抱歉", "permission", "privilege", "access denied")
    return any(marker in lowered for marker in markers)


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _http_transport(payload: dict[str, Any], timeout_seconds: int) -> bytes:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "a-share-swing-system/tushare-minimal-proof"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


def _sanitized_response(payload: dict[str, Any], token: str) -> dict[str, Any]:
    copied = json.loads(json.dumps(payload, ensure_ascii=False))
    if "msg" in copied:
        copied["msg"] = sanitize_message(str(copied.get("msg", "")), token)
    copied.pop("token", None)
    return copied
