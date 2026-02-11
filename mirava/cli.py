import asyncio
from typing import Dict, List, Optional, Tuple

import httpx
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout

from .mirrors import load_mirrors, list_package_names
from .models import CheckResult, PackageEndpoint
from .registry.factory import OS_NAMES, REGISTRY_NAMES, registry_for
from .utils import detect_os, os_defaults

BACK = "__back__"
QUIT = "__quit__"


def _title(text: str) -> None:
    print_formatted_text(HTML(f"<b><ansicyan>{text}</ansicyan></b>"))


def _subtle(text: str) -> None:
    print_formatted_text(HTML(f"<style fg='#7f8c8d'>{text}</style>"))


def _banner() -> None:
    print_formatted_text(HTML("<b><ansicyan>MIRAVA</ansicyan></b> <style fg='#95a5a6'>Mirror Health Wizard</style>"))


def _menu(
    session: PromptSession,
    title: str,
    description: str,
    options: List[str],
    default: Optional[str] = None,
    allow_back: bool = False,
) -> str:
    selected_idx = 0
    if default and default in options:
        selected_idx = options.index(default)

    result: Optional[str] = None

    def _get_text() -> FormattedText:
        lines: list[tuple[str, str]] = []
        lines.append(("bold ansicyan", title))
        lines.append(("", "\n"))
        lines.append(("#7f8c8d", description))
        lines.append(("", "\n\n"))

        for i, opt in enumerate(options):
            if i == selected_idx:
                lines.append(("bold ansiwhite bg:ansiblue", f" ▸ {opt} "))
            else:
                lines.append(("", f"   {opt} "))
            lines.append(("", "\n"))

        lines.append(("", "\n"))
        nav = "↑/↓=move  Enter=select  q=quit"
        if allow_back:
            nav = "↑/↓=move  Enter=select  b=back  q=quit"
        lines.append(("#7f8c8d", nav))
        return FormattedText(lines)

    text_control = FormattedTextControl(_get_text)
    window = Window(content=text_control, always_hide_cursor=True)
    layout = Layout(HSplit([window]))

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _up(event):
        nonlocal selected_idx
        selected_idx = (selected_idx - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def _down(event):
        nonlocal selected_idx
        selected_idx = (selected_idx + 1) % len(options)

    @kb.add("enter")
    def _enter(event):
        nonlocal result
        result = options[selected_idx]
        event.app.exit()

    @kb.add("q")
    def _quit(event):
        nonlocal result
        result = QUIT
        event.app.exit()

    if allow_back:
        @kb.add("b")
        @kb.add("escape")
        def _back(event):
            nonlocal result
            result = BACK
            event.app.exit()

    app: Application[None] = Application(layout=layout, key_bindings=kb, full_screen=False)
    app.run()

    return result or QUIT


def _text_input(
    session: PromptSession,
    label: str,
    default: Optional[str] = None,
    allow_blank: bool = True,
    allow_back: bool = True,
) -> str:
    suffix = f" [{default}]" if default else ""
    nav = "(Enter=default, b=back, q=quit)" if allow_back else "(Enter=default, q=quit)"
    while True:
        raw = session.prompt(f"{label}{suffix}: ").strip()
        lowered = raw.lower()
        if lowered in {"q", "quit", "exit"}:
            return QUIT
        if allow_back and lowered in {"b", "back"}:
            return BACK
        if raw == "":
            if default is not None:
                return default
            if allow_blank:
                return ""
            print_formatted_text(HTML(f"<ansired>{label} is required.</ansired>"))
            continue
        return raw


def _package_word(result: CheckResult) -> str:
    if result.package_ok is True:
        return "FOUND"
    if result.package_ok is False:
        return "NOT FOUND"
    return "SKIPPED"


def _shorten(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: max(0, width - 3)] + "..."


def _build_table(rows: List[List[str]], headers: List[str]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt_row(row: List[str]) -> str:
        cells = [f" {cell.ljust(widths[i])} " for i, cell in enumerate(row)]
        return "|" + "|".join(cells) + "|"

    lines = [border, fmt_row(headers), border]
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(border)
    return "\n".join(lines)


async def _run_checks(endpoints: List[PackageEndpoint], package: Optional[str], os_kwargs: Dict[str, str]) -> List[CheckResult]:
    timeout = httpx.Timeout(8.0, connect=4.0)
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        sem = asyncio.Semaphore(10)

        async def worker(ep: PackageEndpoint, url: str) -> CheckResult:
            async with sem:
                registry = registry_for(ep.name)
                reachable, latency, detail, pkg_ok, pkg_detail = await registry.check(
                    client,
                    url,
                    package=package,
                    **os_kwargs,
                )
                detail_full = detail
                if pkg_detail:
                    detail_full = f"{detail_full}; {pkg_detail}" if detail_full else pkg_detail
                return CheckResult(
                    mirror_name=ep.mirror_name,
                    endpoint_name=ep.name,
                    url=url,
                    reachable=reachable,
                    latency_ms=latency,
                    package_ok=pkg_ok,
                    detail=detail_full,
                )

        tasks = [asyncio.create_task(worker(ep, url)) for ep in endpoints for url in ep.urls]
        total = len(tasks)
        done = 0
        results: List[CheckResult] = []
        loop = asyncio.get_running_loop()
        started = loop.time()

        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            done += 1
            elapsed = loop.time() - started
            print_formatted_text(
                HTML(
                    f"<style fg='#7f8c8d'>[{done}/{total}] "
                    f"{result.endpoint_name} on {result.mirror_name} -> "
                    f"{'OK' if result.reachable else 'FAIL'} / {_package_word(result)} "
                    f"({elapsed:.1f}s elapsed)</style>"
                )
            )
        return results


def _collect_os_kwargs(session: PromptSession, os_choice: str, base_kwargs: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    kwargs = dict(base_kwargs)

    if os_choice in {"Debian", "Ubuntu", "Kali", "Mint", "Raspbian"}:
        suite = _text_input(session, "Suite/Codename", kwargs.get("suite", ""), allow_blank=False)
        if suite in {BACK, QUIT}:
            return suite, kwargs
        component = _text_input(session, "Component", kwargs.get("component", "main"), allow_blank=False)
        if component in {BACK, QUIT}:
            return component, kwargs
        arch = _text_input(session, "Architecture", kwargs.get("arch", "amd64"), allow_blank=False)
        if arch in {BACK, QUIT}:
            return arch, kwargs
        kwargs.update({"suite": suite, "component": component, "arch": arch})

    elif os_choice in {"Arch Linux", "Manjaro", "Archlinux"}:
        repo = _text_input(session, "Repository", kwargs.get("repo", "core"), allow_blank=False)
        if repo in {BACK, QUIT}:
            return repo, kwargs
        arch = _text_input(session, "Architecture", kwargs.get("arch", "x86_64"), allow_blank=False)
        if arch in {BACK, QUIT}:
            return arch, kwargs
        kwargs.update({"repo": repo, "arch": arch})

    elif os_choice in {"Alpine"}:
        branch = _text_input(session, "Branch", kwargs.get("branch", "v3.18"), allow_blank=False)
        if branch in {BACK, QUIT}:
            return branch, kwargs
        repo = _text_input(session, "Repository", kwargs.get("repo", "main"), allow_blank=False)
        if repo in {BACK, QUIT}:
            return repo, kwargs
        arch = _text_input(session, "Architecture", kwargs.get("arch", "x86_64"), allow_blank=False)
        if arch in {BACK, QUIT}:
            return arch, kwargs
        kwargs.update({"branch": branch, "repo": repo, "arch": arch})

    return "ok", kwargs


def _run_and_show(endpoints: List[PackageEndpoint], package: Optional[str], os_kwargs: Dict[str, str]) -> None:
    _title("Checking mirrors")
    _subtle("Live progress:")
    results = asyncio.run(_run_checks(endpoints, package, os_kwargs))
    sorted_results = sorted(results, key=lambda r: (not r.reachable, r.latency_ms or 1e9))

    rows: List[List[str]] = []
    for result in sorted_results:
        latency = f"{result.latency_ms:.0f}ms" if result.latency_ms is not None else "-"
        rows.append(
            [
                "OK" if result.reachable else "FAIL",
                _package_word(result),
                latency,
                _shorten(result.mirror_name, 36),
                _shorten(result.url, 52),
                _shorten(result.detail or "-", 44),
            ]
        )

    print()
    _title("Results")
    print(
        _build_table(
            rows,
            headers=["Reach", "Package", "Latency", "Mirror", "Endpoint", "Reason"],
        )
    )
    _subtle("Reach=OK means endpoint responded successfully. Reach=FAIL means endpoint unreachable or returned an error status.")
    _subtle("Package=FOUND means the package/image index lookup succeeded. Package=NOT FOUND means mirror reachable but item missing.")
    _subtle("Package=SKIPPED means no package/image name was provided for that run.")


def _os_flow(session: PromptSession, mirrors, all_names: List[str], os_default: Optional[str], base_kwargs: Dict[str, str]) -> str:
    os_names = [name for name in all_names if name in OS_NAMES]

    while True:
        print()
        choice = _menu(
            session,
            title="OS Mirror Checks",
            description="Choose your OS mirror type. Your local OS is preselected when detected.",
            options=os_names,
            default=os_default,
            allow_back=True,
        )
        if choice == QUIT:
            return QUIT
        if choice == BACK:
            return BACK

        pkg_prompt = f"OS package for {choice} (optional, e.g. curl, gcc, linux-headers)"
        package = _text_input(session, pkg_prompt, default="", allow_blank=True)
        if package == QUIT:
            return QUIT
        if package == BACK:
            continue

        status, os_kwargs = _collect_os_kwargs(session, choice, base_kwargs)
        if status == QUIT:
            return QUIT
        if status == BACK:
            continue

        endpoints: List[PackageEndpoint] = []
        for mirror in mirrors:
            endpoints.extend(mirror.packages_by_name(choice))

        if not endpoints:
            print_formatted_text(HTML("<ansired>No mirrors found for that OS choice.</ansired>"))
            continue

        _run_and_show(endpoints, package or None, os_kwargs)

        post = _menu(
            session,
            title="Next Step",
            description="Choose what to do now.",
            options=["Run another OS check", "Back to main menu", "Exit"],
            default="Run another OS check",
            allow_back=False,
        )
        if post in {QUIT, "Exit"}:
            return QUIT
        if post == "Back to main menu":
            return BACK


def _registry_flow(session: PromptSession, mirrors, all_names: List[str]) -> str:
    registry_names = [name for name in all_names if name in REGISTRY_NAMES]

    while True:
        print()
        choice = _menu(
            session,
            title="Registry Mirror Checks",
            description="Choose the package registry you want to test.",
            options=registry_names,
            default="PyPI" if "PyPI" in registry_names else None,
            allow_back=True,
        )
        if choice == QUIT:
            return QUIT
        if choice == BACK:
            return BACK

        example = "python package" if choice == "PyPI" else "image name" if choice == "Docker Registry" else "package name"
        package = _text_input(
            session,
            f"Package/Image for {choice} (required, {example})",
            allow_blank=False,
        )
        if package == QUIT:
            return QUIT
        if package == BACK:
            continue

        endpoints: List[PackageEndpoint] = []
        for mirror in mirrors:
            endpoints.extend(mirror.packages_by_name(choice))

        if not endpoints:
            print_formatted_text(HTML("<ansired>No mirrors found for that registry choice.</ansired>"))
            continue

        _run_and_show(endpoints, package, {})

        post = _menu(
            session,
            title="Next Step",
            description="Choose what to do now.",
            options=["Run another registry check", "Back to main menu", "Exit"],
            default="Run another registry check",
            allow_back=False,
        )
        if post in {QUIT, "Exit"}:
            return QUIT
        if post == "Back to main menu":
            return BACK


def main() -> None:
    mirrors = load_mirrors("mirava_full_json.json")
    all_names = list_package_names(mirrors)

    os_info = detect_os()
    os_default, base_os_kwargs = os_defaults(os_info)

    session = PromptSession()

    _banner()
    _subtle("Type b for back, q to quit. Press Enter to accept defaults and continue.")

    while True:
        print()
        mode = _menu(
            session,
            title="Main Menu",
            description="Pick what you want to verify.",
            options=["OS mirrors", "Registry mirrors", "Exit"],
            default="OS mirrors",
            allow_back=False,
        )

        if mode in {QUIT, "Exit"}:
            return

        if mode == "OS mirrors":
            action = _os_flow(session, mirrors, all_names, os_default, base_os_kwargs)
            if action == QUIT:
                return
            continue

        if mode == "Registry mirrors":
            action = _registry_flow(session, mirrors, all_names)
            if action == QUIT:
                return
            continue


if __name__ == "__main__":
    main()
