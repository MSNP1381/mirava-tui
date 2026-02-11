from __future__ import annotations

import os
import platform
import re
from typing import Dict, Optional, Tuple


def normalize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url):
        return f"https://{url}"
    return url


def detect_os() -> Dict[str, str]:
    info: Dict[str, str] = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                info[key] = value.strip().strip('"')
    except FileNotFoundError:
        info["ID"] = platform.system().lower()
    return info


def os_defaults(info: Dict[str, str]) -> Tuple[Optional[str], Dict[str, str]]:
    os_id = info.get("ID", "").lower()
    os_like = info.get("ID_LIKE", "").lower()
    codename = info.get("VERSION_CODENAME") or ""
    version_id = info.get("VERSION_ID") or ""

    defaults: Dict[str, str] = {
        "arch": "amd64",
        "component": "main",
        "repo": "core",
        "branch": "stable",
    }

    if os_id in {"ubuntu", "debian", "linuxmint", "kali", "raspbian"} or "debian" in os_like:
        defaults["suite"] = codename or version_id
        if os_id == "ubuntu":
            return "Ubuntu", defaults
        if os_id == "kali":
            return "Kali", defaults
        if os_id == "linuxmint":
            return "Mint", defaults
        if os_id == "raspbian":
            return "Raspbian", defaults
        return "Debian", defaults
    if os_id in {"centos", "rocky", "almalinux", "fedora"} or "rhel" in os_like:
        defaults["releasever"] = version_id or "9"
        if os_id == "rocky":
            return "Rocky Linux", defaults
        if os_id == "almalinux":
            return "AlmaLinux", defaults
        if os_id == "fedora":
            return "Fedora", defaults
        return "CentOS", defaults
    if os_id in {"arch", "manjaro"} or "arch" in os_like:
        defaults["arch"] = os.uname().machine or "x86_64"
        defaults["repo"] = "core"
        return "Arch Linux", defaults
    if os_id in {"alpine"}:
        defaults["branch"] = f"v{version_id}" if version_id else "v3.18"
        defaults["repo"] = "main"
        defaults["arch"] = os.uname().machine or "x86_64"
        return "Alpine", defaults

    return None, defaults
