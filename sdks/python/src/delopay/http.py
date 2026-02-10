from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from .errors import ApiError

IDEMPOTENT_METHODS = {"GET", "HEAD"}


class HttpClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_ms: int,
        max_retries: int,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = timeout_ms / 1000
        self._max_retries = max_retries

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        method_upper = method.upper()
        retries = self._max_retries if method_upper in IDEMPOTENT_METHODS else 0

        for attempt in range(retries + 1):
            try:
                return self._send_once(method_upper, path, payload, query)
            except HTTPError as exc:
                body_text = exc.read().decode("utf-8") if exc.fp else ""
                parsed = _parse_json(body_text)
                request_id = exc.headers.get("x-request-id") if exc.headers else None
                code = None
                message = exc.msg or "Request failed"

                if isinstance(parsed, dict):
                    message = str(parsed.get("message") or parsed.get("error") or message)
                    code = parsed.get("code") or parsed.get("errorCode")
                    request_id = request_id or parsed.get("requestId")

                if exc.code >= 500 and attempt < retries:
                    _sleep(attempt)
                    continue

                raise ApiError(
                    status=exc.code,
                    message=message,
                    code=str(code) if code is not None else None,
                    request_id=str(request_id) if request_id is not None else None,
                    raw=parsed if parsed is not None else body_text,
                ) from exc
            except URLError as exc:
                if attempt < retries:
                    _sleep(attempt)
                    continue

                raise ApiError(status=0, message="Network request failed", raw=str(exc.reason)) from exc

        raise ApiError(status=0, message="Request exhausted retries")

    def _send_once(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        query: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        url = self._build_url(path, query)
        data = json.dumps(payload).encode("utf-8") if payload is not None else None

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"

        request = Request(url=url, data=data, method=method, headers=headers)
        with urlopen(request, timeout=self._timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)

    def _build_url(self, path: str, query: dict[str, Any] | None) -> str:
        base = self._base_url if self._base_url.endswith("/") else f"{self._base_url}/"
        clean_path = path[1:] if path.startswith("/") else path
        url = urljoin(base, clean_path)

        if not query:
            return url

        filtered = {key: value for key, value in query.items() if value is not None}
        if not filtered:
            return url

        return f"{url}?{urlencode(filtered)}"


def _parse_json(raw: str) -> Any:
    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _sleep(attempt: int) -> None:
    delay = min(1.0, 0.1 * (2**attempt))
    time.sleep(delay)
