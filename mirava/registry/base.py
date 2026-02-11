from __future__ import annotations

import asyncio
import time
from typing import Optional, Tuple

import httpx


class BaseRegistry:
    name = "base"

    async def check_reachable(self, client: httpx.AsyncClient, url: str) -> Tuple[bool, Optional[float], str]:
        start = time.perf_counter()
        try:
            resp = await client.get(url, follow_redirects=True)
            latency = (time.perf_counter() - start) * 1000
            if resp.status_code < 400:
                return True, latency, "ok"
            return False, latency, f"http {resp.status_code}"
        except httpx.RequestError as exc:
            return False, None, str(exc)

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        return None, "package check not supported"

    async def check(self, client: httpx.AsyncClient, url: str, package: Optional[str] = None, **kwargs):
        reachable, latency, detail = await self.check_reachable(client, url)
        package_ok = None
        pkg_detail = ""
        if package:
            package_ok, pkg_detail = await self.check_package(client, url, package, **kwargs)
        return reachable, latency, detail, package_ok, pkg_detail
