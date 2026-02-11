from __future__ import annotations

from typing import Optional, Tuple

import httpx

from .base import BaseRegistry


class PyPIRegistry(BaseRegistry):
    name = "PyPI"

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        package = package.strip().lower()
        if not package:
            return None, "no package"
        if not url.endswith("/"):
            url = url + "/"
        check_url = f"{url}simple/{package}/"
        try:
            resp = await client.get(check_url, follow_redirects=True)
            if resp.status_code == 200:
                return True, "found"
            if resp.status_code == 404:
                return False, "not found"
            return False, f"http {resp.status_code}"
        except httpx.RequestError as exc:
            return False, str(exc)
