"""Async HTTP client for the Dispatcharr REST API.

Dispatcharr's REST API only accepts JWT Bearer tokens — there is no static
API key support for the REST endpoints. Credentials live in environment
variables so they can be rotated without touching code:
  DISPATCHARR_URL       - base URL, e.g. http://dispatcharr.example.com
  DISPATCHARR_USERNAME  - Dispatcharr username
  DISPATCHARR_PASSWORD  - Dispatcharr password

Tokens are fetched lazily (on first request) to avoid a login round-trip at
import time. A 401 response re-uses the refresh token before falling back to
a full password login, keeping credential exposure to a minimum.
"""

import os
from typing import Any

import httpx

_TIMEOUT = 30.0


class DispatcharrClient:
    def __init__(self) -> None:
        base_url = os.environ.get("DISPATCHARR_URL", "").rstrip("/")
        username = os.environ.get("DISPATCHARR_USERNAME", "")
        password = os.environ.get("DISPATCHARR_PASSWORD", "")

        if not base_url:
            raise ValueError("DISPATCHARR_URL environment variable is required")
        if not username or not password:
            raise ValueError(
                "DISPATCHARR_USERNAME and DISPATCHARR_PASSWORD environment variables are required"
            )

        self._base = base_url
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    async def _login(self) -> None:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.post(
                self._url("/api/accounts/token/"),
                json={"username": self._username, "password": self._password},
            )
            r.raise_for_status()
            data = r.json()
            self._access_token = data["access"]
            self._refresh_token = data.get("refresh")

    async def _refresh(self) -> bool:
        if not self._refresh_token:
            return False
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.post(
                self._url("/api/accounts/token/refresh/"),
                json={"refresh": self._refresh_token},
            )
            if r.status_code == 200:
                self._access_token = r.json()["access"]
                return True
        return False

    async def _ensure_token(self) -> None:
        if not self._access_token:
            await self._login()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        await self._ensure_token()
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.request(method, self._url(path), headers=self._auth_headers(), **kwargs)
            if r.status_code == 401:
                # Access tokens are short-lived; prefer refresh over re-login
                # to avoid sending the password over the wire unnecessarily.
                if not await self._refresh():
                    await self._login()
                r = await c.request(method, self._url(path), headers=self._auth_headers(), **kwargs)
            r.raise_for_status()
            return r.json() if r.content else {}

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: dict | None = None) -> Any:
        return await self._request("POST", path, json=data or {})

    async def patch(self, path: str, data: dict) -> Any:
        return await self._request("PATCH", path, json=data)

    async def delete(self, path: str) -> dict:
        return await self._request("DELETE", path)
