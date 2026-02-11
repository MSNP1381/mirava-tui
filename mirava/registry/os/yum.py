from __future__ import annotations

import gzip
import io
from typing import Optional, Tuple

import httpx

from .generic import OsRegistry


class YumRegistry(OsRegistry):
    name = "YUM"

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        package = package.strip()
        if not package:
            return None, "no package"
        base = url.rstrip("/")
        repomd_url = f"{base}/repodata/repomd.xml"
        try:
            repomd = await client.get(repomd_url, follow_redirects=True)
            if repomd.status_code != 200:
                return False, f"repomd http {repomd.status_code}"
            # find primary.xml.gz location
            text = repomd.text
            marker = "<data type=\"primary\">"
            idx = text.find(marker)
            if idx == -1:
                return False, "primary not found"
            loc_marker = "<location href=\""
            loc_idx = text.find(loc_marker, idx)
            if loc_idx == -1:
                return False, "primary location not found"
            loc_idx += len(loc_marker)
            end_idx = text.find("\"", loc_idx)
            href = text[loc_idx:end_idx]
            primary_url = f"{base}/{href}"
            prim = await client.get(primary_url, follow_redirects=True)
            if prim.status_code != 200:
                return False, f"primary http {prim.status_code}"
            data = gzip.GzipFile(fileobj=io.BytesIO(prim.content)).read().decode("utf-8", errors="ignore")
            needle = f"<name>{package}</name>"
            return (needle in data), ("found" if needle in data else "not found")
        except httpx.RequestError as exc:
            return False, str(exc)
        except OSError:
            return False, "invalid primary.xml.gz"
