"""Official Finget public API client (/api/v1)."""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .errors import ApiError, FingetError

VERSION = "1.0.0"
DEFAULT_BASE_URL = "https://finget.ir/api/v1"
DEFAULT_AUTH_URL = "https://finget.ir/auth"


class Client:
    """Server-side client for Finget login and notifications.

    Keep the API key on the server only. Never expose ``FINGET_API_KEY``
    in browsers or mobile apps.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        auth_url: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        key = api_key.strip()
        if not key:
            raise FingetError("Finget API key is empty.")
        if timeout < 1:
            raise FingetError("Request timeout must be at least 1 second.")

        self._api_key = key
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._auth_url = (auth_url or DEFAULT_AUTH_URL).rstrip("/")
        self._timeout = timeout

    @classmethod
    def from_env(cls, api_key_env: str = "FINGET_API_KEY") -> Client:
        """Build a client from environment variables.

        Reads ``FINGET_API_KEY`` (or ``api_key_env``), and optional
        ``FINGET_BASE_URL`` / ``FINGET_AUTH_URL``.
        """
        key = os.environ.get(api_key_env, "")
        if not str(key).strip():
            raise FingetError(f"Environment variable {api_key_env} is not set.")

        base = os.environ.get("FINGET_BASE_URL") or None
        auth = os.environ.get("FINGET_AUTH_URL") or None
        return cls(str(key), base_url=base, auth_url=auth)

    def get_site(self) -> dict[str, Any]:
        """Validate the API key and return site metadata."""
        return self._request("GET", "/site")

    def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange a one-time callback code for ``{user, isNew}``."""
        trimmed = code.strip()
        if not trimmed:
            raise FingetError("Login code is empty.")
        return self._request("POST", "/auth/token", {"code": trimmed})

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Fetch a linked user's current profile."""
        uid = user_id.strip()
        if not uid:
            raise FingetError("User id is empty.")
        return self._request("GET", f"/users/{urllib.parse.quote(uid, safe='')}")

    def send_notification(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a notification for linked users (expects HTTP 201)."""
        return self._request("POST", "/notifications", payload, ok_statuses=(201,))

    def get_notification(self, notification_id: str) -> dict[str, Any]:
        """Fetch notification delivery status."""
        nid = notification_id.strip()
        if not nid:
            raise FingetError("Notification id is empty.")
        return self._request(
            "GET",
            f"/notifications/{urllib.parse.quote(nid, safe='')}",
        )

    def create_state(self, nbytes: int = 16) -> str:
        """Return a cryptographically secure hex state string."""
        if nbytes < 8:
            raise FingetError("State length is too short.")
        return secrets.token_hex(nbytes)

    def login_url(
        self,
        client_id: str,
        state: str | None = None,
    ) -> dict[str, str]:
        """Build the Sign-in-with-Finget redirect URL and CSRF state."""
        cid = client_id.strip()
        if not cid:
            raise FingetError("Site client_id is empty.")

        s = state if state is not None else self.create_state()
        query = urllib.parse.urlencode({"client_id": cid, "state": s})
        return {"url": f"{self._auth_url}?{query}", "state": s}

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        ok_statuses: tuple[int, ...] = (200,),
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": f"finget-python/{VERSION}",
        }
        data: bytes | None = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = getattr(resp, "status", 200)
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            status = exc.code
            payload = self._decode_json(raw)
            message = payload.get("message") if isinstance(payload.get("message"), str) else (
                f"Finget request failed (HTTP {status})."
            )
            code = payload.get("code") if isinstance(payload.get("code"), str) else None
            raise ApiError(message, status, code, payload) from None
        except urllib.error.URLError as exc:
            raise ApiError(str(exc.reason) or "Could not reach Finget.", 0) from None

        payload = self._decode_json(raw)
        if status not in ok_statuses:
            message = payload.get("message") if isinstance(payload.get("message"), str) else (
                f"Finget request failed (HTTP {status})."
            )
            code = payload.get("code") if isinstance(payload.get("code"), str) else None
            raise ApiError(message, status, code, payload)
        return payload

    @staticmethod
    def _decode_json(raw: str) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
