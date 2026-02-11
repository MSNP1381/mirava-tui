from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class PackageEndpoint:
    name: str
    urls: List[str]
    mirror_name: str
    mirror_url: str


@dataclass
class Mirror:
    name: str
    url: str
    description: str
    packages: List[PackageEndpoint] = field(default_factory=list)

    def packages_by_name(self, name: str) -> List[PackageEndpoint]:
        return [p for p in self.packages if p.name == name]


@dataclass
class CheckResult:
    mirror_name: str
    endpoint_name: str
    url: str
    reachable: bool
    latency_ms: Optional[float]
    package_ok: Optional[bool]
    detail: str = ""
