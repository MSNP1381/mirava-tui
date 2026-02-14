from __future__ import annotations

import json
from typing import Iterable, List

from .models import Mirror, PackageEndpoint
from .utils import normalize_url


def _coerce_urls(value) -> List[str]:
    if isinstance(value, list):
        return [normalize_url(v) for v in value]
    return [normalize_url(str(value))]


def load_mirrors(path: str) -> List[Mirror]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    mirrors: List[Mirror] = []
    for item in data.get("mirrors", []):
        mirror = Mirror(
            name=item.get("name", ""),
            url=normalize_url(item.get("url", "")),
            description=item.get("description", ""),
        )
        packages = item.get("packages", [])
        for entry in packages:
            if isinstance(entry, str):
                mirror.packages.append(
                    PackageEndpoint(
                        name=entry,
                        urls=[mirror.url],
                        mirror_name=mirror.name,
                        mirror_url=mirror.url,
                    )
                )
            elif isinstance(entry, dict):
                for name, value in entry.items():
                    mirror.packages.append(
                        PackageEndpoint(
                            name=name,
                            urls=_coerce_urls(value),
                            mirror_name=mirror.name,
                            mirror_url=mirror.url,
                        )
                    )
        mirrors.append(mirror)
    return mirrors


def list_package_names(mirrors: Iterable[Mirror]) -> List[str]:
    names = set()
    for mirror in mirrors:
        for pkg in mirror.packages:
            names.add(pkg.name)
    return sorted(names)
