#!/usr/bin/env python3
"""Simple Python environment self-check script."""

from __future__ import annotations

import argparse
import importlib
import locale
import os
import platform
import shutil
import site
import socket
import subprocess
import sys
import tempfile


def ok(label: str, detail: str) -> tuple[bool, str, str]:
    return True, label, detail


def fail(label: str, detail: str) -> tuple[bool, str, str]:
    return False, label, detail


def check_python() -> tuple[bool, str, str]:
    detail = (
        f"Python {platform.python_version()} | "
        f"executable: {sys.executable}"
    )
    return ok("Python interpreter", detail)


def check_virtualenv() -> tuple[bool, str, str]:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        return ok("Virtual environment", f"active ({sys.prefix})")
    return ok("Virtual environment", "not active (system interpreter in use)")


def check_encoding() -> tuple[bool, str, str]:
    detail = (
        f"default={sys.getdefaultencoding()}, "
        f"filesystem={sys.getfilesystemencoding()}, "
        f"preferred={locale.getpreferredencoding(False)}"
    )
    return ok("Encoding", detail)


def check_pip() -> tuple[bool, str, str]:
    pip_path = shutil.which("pip") or shutil.which("pip3")
    if not pip_path:
        return fail("pip", "pip command not found in PATH")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception as exc:  # pragma: no cover
        return fail("pip", f"unable to run pip: {exc}")

    return ok("pip", result.stdout.strip())


def check_stdlib_imports() -> tuple[bool, str, str]:
    modules = ["json", "sqlite3", "ssl", "venv", "pathlib"]
    failed = []
    for name in modules:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover
            failed.append(f"{name} ({exc})")

    if failed:
        return fail("Standard library imports", ", ".join(failed))
    return ok("Standard library imports", ", ".join(modules))


def check_site_packages() -> tuple[bool, str, str]:
    packages = site.getsitepackages() if hasattr(site, "getsitepackages") else []
    user_site = site.getusersitepackages()
    detail = f"site-packages={packages or 'N/A'}, user-site={user_site}"
    return ok("Package paths", detail)


def check_file_write() -> tuple[bool, str, str]:
    try:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=True) as fh:
            fh.write("python environment test\n")
            fh.seek(0)
            content = fh.read().strip()
    except Exception as exc:  # pragma: no cover
        return fail("File read/write", str(exc))

    return ok("File read/write", f"temporary file success: {content!r}")


def check_dns() -> tuple[bool, str, str]:
    try:
        addr = socket.gethostbyname("localhost")
    except Exception as exc:  # pragma: no cover
        return fail("Network basics", f"localhost resolution failed: {exc}")

    return ok("Network basics", f"localhost -> {addr}")


def check_optional_imports(modules: list[str]) -> list[tuple[bool, str, str]]:
    results = []
    for name in modules:
        try:
            module = importlib.import_module(name)
            version = getattr(module, "__version__", "unknown")
            results.append(ok(f"Optional package: {name}", f"imported, version={version}"))
        except Exception as exc:
            results.append(fail(f"Optional package: {name}", str(exc)))
    return results


def run_checks(optional_modules: list[str]) -> list[tuple[bool, str, str]]:
    results = [
        check_python(),
        check_virtualenv(),
        check_encoding(),
        check_pip(),
        check_stdlib_imports(),
        check_site_packages(),
        check_file_write(),
        check_dns(),
    ]
    results.extend(check_optional_imports(optional_modules))
    return results


def print_report(results: list[tuple[bool, str, str]]) -> int:
    passed = 0
    failed = 0

    print("=" * 72)
    print("Python Environment Test")
    print("=" * 72)
    print(f"Platform : {platform.platform()}")
    print(f"Working dir : {os.getcwd()}")
    print()

    for success, label, detail in results:
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {label}")
        print(f"       {detail}")
        if success:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 72)
    print(f"Summary: passed={passed}, failed={failed}")
    print("=" * 72)
    return 0 if failed == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether a Python environment works normally.")
    parser.add_argument(
        "--check-package",
        action="append",
        default=[],
        metavar="MODULE",
        help="Optional third-party package to import-check. Can be used multiple times.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_checks(args.check_package)
    return print_report(results)


if __name__ == "__main__":
    raise SystemExit(main())
