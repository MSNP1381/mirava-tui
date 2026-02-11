from __future__ import annotations

from typing import Dict

from .base import BaseRegistry
from .docker import DockerRegistry
from .npm import NpmRegistry
from .pypi import PyPIRegistry
from .os.apt import AptRegistry
from .os.yum import YumRegistry
from .os.pacman import PacmanRegistry
from .os.alpine import AlpineRegistry
from .os.generic import OsRegistry


REGISTRY_MAP: Dict[str, BaseRegistry] = {
    "PyPI": PyPIRegistry(),
    "npm": NpmRegistry(),
    "Docker Registry": DockerRegistry(),
    "Debian": AptRegistry(),
    "Ubuntu": AptRegistry(),
    "Kali": AptRegistry(),
    "Mint": AptRegistry(),
    "Raspbian": AptRegistry(),
    "CentOS": YumRegistry(),
    "Rocky Linux": YumRegistry(),
    "AlmaLinux": YumRegistry(),
    "Almalinux": YumRegistry(),
    "Fedora": YumRegistry(),
    "EPEL": YumRegistry(),
    "Fedora EPEL": YumRegistry(),
    "Arch Linux": PacmanRegistry(),
    "Archlinux": PacmanRegistry(),
    "Manjaro": PacmanRegistry(),
    "Alpine": AlpineRegistry(),
}

OS_NAMES = {
    "Alpine",
    "Arch Linux",
    "CentOS",
    "Debian",
    "Ubuntu",
    "Kali",
    "Mint",
    "Raspbian",
    "Rocky Linux",
    "AlmaLinux",
    "Almalinux",
    "Fedora",
    "EPEL",
    "Fedora EPEL",
    "Manjaro",
    "OpenSuse",
    "OpenBSD",
    "FreeBSD",
    "Archlinux",
}

REGISTRY_NAMES = {
    "PyPI",
    "npm",
    "Docker Registry",
    "Yarn",
    "Composer",
    "Maven",
    "Gradle",
    "NuGet",
    "NodeJS",
}


def registry_for(name: str) -> BaseRegistry:
    return REGISTRY_MAP.get(name, OsRegistry())
