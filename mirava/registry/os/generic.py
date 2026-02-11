from __future__ import annotations

from typing import Optional, Tuple

import httpx

from ..base import BaseRegistry


class OsRegistry(BaseRegistry):
    name = "OS"

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        return None, "package check not supported for this OS"
