from __future__ import annotations

import io
import tarfile
from typing import Optional, Tuple

import httpx

from .generic import OsRegistry


class PacmanRegistry(OsRegistry):
    name = "Pacman"

    async def check_package(self, client: httpx.AsyncClient, url: str, package: str, **kwargs) -> Tuple[Optional[bool], str]:
        package = package.strip()
        if not package:
            return None, "no package"
        repo = kwargs.get("repo") or "core"
        arch = kwargs.get("arch") or "x86_64"
        base = url.rstrip("/")
        base = base.replace("$repo", repo).replace("$arch", arch)
        db_url = f"{base}/{repo}.db"
        try:
            resp = await client.get(db_url, follow_redirects=True)
            if resp.status_code != 200:
                return False, f"db http {resp.status_code}"
            with tarfile.open(fileobj=io.BytesIO(resp.content)) as tf:
                for member in tf.getmembers():
                    if member.name.endswith("/desc"):
                        f = tf.extractfile(member)
                        if not f:
                            continue
                        content = f.read().decode("utf-8", errors="ignore")
                        if f"%NAME%\n{package}\n" in content:
                            return True, "found"
            return False, "not found"
        except httpx.RequestError as exc:
            return False, str(exc)
        except tarfile.TarError:
            return False, "invalid db"
