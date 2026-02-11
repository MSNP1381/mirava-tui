from __future__ import annotations

import io
import tarfile
from typing import Optional, Tuple

import httpx

from .generic import OsRegistry


class AlpineRegistry(OsRegistry):
    name = "Alpine"

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        package = package.strip()
        if not package:
            return None, "no package"
        base = url.rstrip("/")
        # If base already ends in main/community, use it directly.
        if base.endswith("/main") or base.endswith("/community"):
            index_url = f"{base}/APKINDEX.tar.gz"
        else:
            branch = kwargs.get("branch") or "v3.18"
            repo = kwargs.get("repo") or "main"
            arch = kwargs.get("arch") or "x86_64"
            index_url = f"{base}/{branch}/{repo}/{arch}/APKINDEX.tar.gz"
        try:
            resp = await client.get(index_url, follow_redirects=True)
            if resp.status_code != 200:
                return False, f"index http {resp.status_code}"
            with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tf:
                for member in tf.getmembers():
                    if member.name.endswith("APKINDEX"):
                        f = tf.extractfile(member)
                        if not f:
                            continue
                        content = f.read().decode("utf-8", errors="ignore")
                        if f"P:{package}\n" in content:
                            return True, "found"
            return False, "not found"
        except httpx.RequestError as exc:
            return False, str(exc)
        except tarfile.TarError:
            return False, "invalid APKINDEX"
