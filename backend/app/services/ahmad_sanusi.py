import asyncio
import random
from typing import Any

import httpx

from app.config import settings


class AhmadSanusiError(RuntimeError):
    pass


class AhmadSanusiClient:
    def __init__(self) -> None:
        self.base_url = settings.ahmad_sanusi_base_url.rstrip("/")
        self.api_key = settings.ahmad_sanusi_api_key

    @property
    def headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "Fathul-Bari-Research/0.1",
        }

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}{endpoint}"

        if not self.api_key or self.api_key == "PUT_YOUR_API_KEY_HERE":
            raise AhmadSanusiError("AHMAD_SANUSI_API_KEY belum diisi di .env")

        last_error: Exception | None = None

        for attempt in range(settings.sync_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(url, headers=self.headers, params=params)

                if response.status_code in {429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        f"Retryable HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                payload = response.json()

                if payload.get("status") == "error":
                    raise AhmadSanusiError(str(payload))

                return payload

            except (httpx.RequestError, httpx.HTTPStatusError, ValueError, AhmadSanusiError) as exc:
                last_error = exc
                if isinstance(exc, AhmadSanusiError) and "status" not in str(exc):
                    raise
                if attempt >= settings.sync_max_retries:
                    break

                delay = max(settings.sync_delay_seconds, 1.0) * (2 ** attempt)
                delay += random.uniform(0, 0.25)
                await asyncio.sleep(delay)

        raise AhmadSanusiError(f"Request gagal setelah retry: {url}: {last_error}")

    async def list_collections(self) -> dict:
        return await self.get("/v1/hadits")

    async def list_hadiths(self, kitab: str, page: int = 1, limit: int = 100) -> dict:
        return await self.get(f"/v1/hadits/{kitab}", {"page": page, "limit": limit})

    async def get_hadith(self, kitab: str, nomor: int) -> dict:
        return await self.get(f"/v1/hadits/{kitab}/{nomor}")

    async def search(self, query: str, limit: int = 20) -> dict:
        return await self.get("/v1/hadits/search", {"q": query, "limit": limit})
