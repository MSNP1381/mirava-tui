from __future__ import annotations

import gzip
import io
from typing import Optional, Tuple

import httpx

from .generic import OsRegistry


class AptRegistry(OsRegistry):
    name = "APT"

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        package = package.strip()
        if not package:
            return None, "no package"
        suite = kwargs.get("suite") or kwargs.get("codename") or ""
        component = kwargs.get("component") or "main"
        arch = kwargs.get("arch") or "amd64"
        if not suite:
            return None, "missing suite/codename"
        base = url.rstrip("/")
        index_url = f"{base}/dists/{suite}/{component}/binary-{arch}/Packages.gz"
        try:
            resp = await client.get(index_url, follow_redirects=True)
            if resp.status_code != 200:
                return False, f"index http {resp.status_code}"
            data = gzip.GzipFile(fileobj=io.BytesIO(resp.content)).read().decode("utf-8", errors="ignore")
            needle = f"Package: {package}\n"
            return (needle in data), ("found" if needle in data else "not found")
        except httpx.RequestError as exc:
            return False, str(exc)
        except OSError:
            return False, "invalid Packages.gz"
