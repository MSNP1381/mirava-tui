from __future__ import annotations

from typing import Optional, Tuple

import httpx

from .base import BaseRegistry


class DockerRegistry(BaseRegistry):
    name = "Docker Registry"

    async def check_reachable(self, client: httpx.AsyncClient, url: str):
        base = url.rstrip("/")
        # Docker registry v2 ping
        return await super().check_reachable(client, f"{base}/v2/")

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        package = package.strip()
        if not package:
            return None, "no image"
        base = url.rstrip("/")
        check_url = f"{base}/v2/{package}/tags/list"
        try:
            resp = await client.get(check_url, follow_redirects=True)
            if resp.status_code == 200:
                return True, "found"
            if resp.status_code == 404:
                return False, "not found"
            return False, f"http {resp.status_code}"
        except httpx.RequestError as exc:
            return False, str(exc)
