# Mirava

Mirava is an interactive terminal app that helps you find working mirror endpoints for:

- Linux package repositories (Debian/Ubuntu/Arch/Alpine and more)
- Language/package registries (PyPI, npm, Docker Registry, etc.)

It checks both:

- Reachability (`OK`/`FAIL`)
- Package availability (`FOUND`/`NOT FOUND`)

## Quick Start

### Option 1: Run a prebuilt binary (recommended)

1. Open the repository's **Releases** page.
2. Download the binary for your platform.
3. Run it from your terminal.

Examples:

```bash
# Linux / macOS
chmod +x mirava-<target>
./mirava-<target>
```

```powershell
# Windows PowerShell
.\mirava-windows-x64.exe
```

### Option 2: Run from source

Requirements:

- Python 3.9+

Install and run:

```bash
pip install -e .
mirava
```

Or without installation:

```bash
python -m mirava
```

## How to Use

When Mirava starts, choose one of these modes:

- `OS mirrors`: Check OS repository mirrors. Package input is optional.
- `Registry mirrors`: Check registries like PyPI/npm/Docker. Package/image input is required.

Keyboard controls:

- `Up` / `Down` (or `k` / `j`) to move
- `Enter` to select
- `b` to go back
- `q` to quit

## Understanding Results

Mirava prints a results table with these columns:

- `Reach`: Endpoint health (`OK` or `FAIL`)
- `Package`: `FOUND`, `NOT FOUND`, or `SKIPPED`
- `Latency`: Lower is typically better
- `Mirror`, `Endpoint`, `Reason`: Context and failure details

Tips:

- Prefer rows with `Reach=OK` and lower latency.
- `NOT FOUND` usually means the mirror is reachable, but that specific package/image is missing.
- `SKIPPED` appears when package checking was optional and no package name was given.

## Notes

- Mirror checks use live network requests, so results can change over time.
- Some mirrors may be reachable but slow; run multiple checks if needed.
