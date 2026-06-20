#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Build native ifURI binary for the current OS (PyInstaller)."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "ifuri_app"
DIST = ROOT / "dist"
APPS = DIST / "apps"
BUILD = ROOT / "build" / "pyinstaller"


def read_version() -> str:
    version_file = ROOT / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.0.0"


def platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        system = "macos"
    if machine in {"x86_64", "amd64"}:
        machine = "x86_64"
    elif machine in {"aarch64", "arm64"}:
        machine = "arm64"
    return f"{system}-{machine}"


def add_data_arg(src: Path, dest: str) -> str:
    sep = ";" if platform.system() == "Windows" else ":"
    return f"{src}{sep}{dest}"


def run_pyinstaller(*, onefile: bool) -> Path:
    APPS.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    exe_name = "ifuri-app.exe" if platform.system() == "Windows" else "ifuri-app"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "ifuri-app",
        "--distpath",
        str(APPS),
        "--workpath",
        str(BUILD / "work"),
        "--specpath",
        str(BUILD),
        "--paths",
        str(SRC),
        "--add-data",
        add_data_arg(PKG / "web", "ifuri_app/web"),
        "--add-data",
        add_data_arg(PKG / "assets", "ifuri_app/assets"),
        "--collect-submodules",
        "ifuri_app",
        "--hidden-import",
        "yaml",
    ]
    # Executable icon from the brand kit. PyInstaller embeds .ico on Windows and
    # .icns on macOS; Linux has no exe icon (the window icon is set at runtime).
    icon = PKG / "assets" / ("icon.ico" if platform.system() == "Windows" else "icon.icns")
    if icon.is_file():
        cmd += ["--icon", str(icon)]
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    cmd.append(str(ROOT / "scripts" / "ifuri_app_entry.py"))
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)
    binary = APPS / exe_name
    if not binary.is_file() and (APPS / "ifuri-app" / exe_name).is_file():
        binary = APPS / "ifuri-app" / exe_name
    if not binary.is_file():
        raise SystemExit(f"PyInstaller output not found under {APPS}")
    return binary


def package_artifact(binary: Path, version: str, tag: str) -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        out = DIST / f"ifuri-{version}-{tag}.zip"
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(binary, arcname=binary.name)
            readme = ROOT / "README.md"
            if readme.is_file():
                zf.write(readme, arcname="README.md")
        return out
    out = DIST / f"ifuri-{version}-{tag}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        tar.add(binary, arcname=binary.name)
        readme = ROOT / "README.md"
        if readme.is_file():
            tar.add(readme, arcname="README.md")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ifURI native app for this platform")
    parser.add_argument("--onefile", action="store_true", default=True)
    parser.add_argument("--onedir", dest="onefile", action="store_false")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args(argv)

    if not args.skip_install:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "pyinstaller", "pyyaml"],
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-e", ".[flows]"],
            cwd=ROOT,
            check=True,
        )

    version = read_version()
    tag = platform_tag()
    binary = run_pyinstaller(onefile=args.onefile)
    artifact = package_artifact(binary, version, tag)
    print(f"binary: {binary}")
    print(f"artifact: {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
