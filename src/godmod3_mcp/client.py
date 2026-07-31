"""HTTP client for the G0DM0D3 REST API."""

from __future__ import annotations

import json
from json import JSONDecodeError, loads
import logging
from typing import Any, AsyncIterator

import httpx

from .config import Config

logger = logging.getLogger(__name__)


class Godmod3ClientError(Exception):
    """Raised when the G0DM0D3 API returns an error or is unreachable."""


class Godmod3Client:
    """Typed async HTTP client for the G0DM0D3 Research Preview API."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_env()
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                **self.config.auth_header,
            },
        )

    async def health(self) -> dict[str, Any]:
        """GET /v1/health"""
        return await self._request("GET", "/v1/health", auth=False)

    async def info(self) -> dict[str, Any]:
        """GET /v1/info"""
        return await self._request("GET", "/v1/info", auth=False)

    async def list_models(self) -> dict[str, Any]:
        """GET /v1/models"""
        return await self._request("GET", "/v1/models", auth=False)

    async def get_tier(self) -> dict[str, Any]:
        """GET /v1/tier"""
        return await self._request("GET", "/v1/tier")

    async def chat_completions(self, payload: dict[str, Any]) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """POST /v1/chat/completions. Returns full response or SSE iterator if stream=True."""
        return await self._chat("/v1/chat/completions", payload)

    async def ultraplinian_completions(self, payload: dict[str, Any]) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """POST /v1/ultraplinian/completions."""
        return await self._chat("/v1/ultraplinian/completions", payload)

    async def consortium_completions(self, payload: dict[str, Any]) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """POST /v1/consortium/completions."""
        return await self._chat("/v1/consortium/completions", payload)

    async def autotune_analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v1/autotune/analyze"""
        return await self._request("POST", "/v1/autotune/analyze", json=payload)

    async def parseltongue_encode(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v1/parseltongue/encode"""
        return await self._request("POST", "/v1/parseltongue/encode", json=payload)

    async def parseltongue_detect(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v1/parseltongue/detect"""
        return await self._request("POST", "/v1/parseltongue/detect", json=payload)

    async def transform_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v1/transform"""
        return await self._request("POST", "/v1/transform", json=payload)

    async def submit_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v1/feedback"""
        return await self._request("POST", "/v1/feedback", json=payload)

    async def dataset_stats(self) -> dict[str, Any]:
        """GET /v1/dataset/stats"""
        return await self._request("GET", "/v1/dataset/stats")

    async def export_dataset(self, format: str = "json") -> str:
        """GET /v1/dataset/export?format=..."""
        response = await self._raw_request("GET", f"/v1/dataset/export?format={format}")
        return response.text

    async def research_info(self) -> dict[str, Any]:
        """GET /v1/research/info"""
        return await self._request("GET", "/v1/research/info")

    async def research_stats(self) -> dict[str, Any]:
        """GET /v1/research/stats"""
        return await self._request("GET", "/v1/research/stats")

    async def research_query(self, params: dict[str, Any]) -> dict[str, Any]:
        """GET /v1/research/query"""
        return await self._request("GET", "/v1/research/query", params=params)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _chat(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Send a chat completion request and either return JSON or stream SSE."""
        if payload.get("stream"):
            return self._stream_sse("POST", path, json=payload)
        return await self._request("POST", path, json=payload)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._raw_request(method, path, auth=auth, params=params, json=json)
        try:
            return response.json()
        except JSONDecodeError as exc:
            raise Godmod3ClientError(f"Non-JSON response from {path}: {response.text[:200]}") from exc

    async def _raw_request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers: dict[str, str] = {}
        if auth:
            headers.update(self.config.auth_header)
        try:
            response = await self._client.request(method, path, params=params, json=json, headers=headers)
        except httpx.RequestError as exc:
            raise Godmod3ClientError(f"Could not reach G0DM0D3 API at {self.config.base_url}: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text[:300]
            raise Godmod3ClientError(f"G0DM0D3 API error {response.status_code} on {path}: {detail}")
        return response

    async def _stream_sse(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield parsed SSE events from G0DM0D3 streaming endpoints."""
        headers: dict[str, str] = {
            "Accept": "text/event-stream",
            **self.config.auth_header,
        }
        async with self._client.stream(method, path, json=json, headers=headers) as response:
            if response.status_code >= 400:
                text = await response.aread()
                raise Godmod3ClientError(f"G0DM0D3 API error {response.status_code} on {path}: {text[:300].decode()}")
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line == "data: [DONE]":
                    yield {"_event": "done"}
                    continue
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        event = loads(data)
                    except JSONDecodeError:
                        event = {"_raw": data}
                    yield event

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "Godmod3Client":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
