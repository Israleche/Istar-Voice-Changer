#!/usr/bin/env python3
"""
Istar Voice Changer - Setup script

Prepares the environment for Istar Voice Changer:
  1. Installs Python dependencies (psutil, py7zr, pyinstaller).
  2. Downloads the upstream voice-changer engine (main.exe) if missing.

The engine is downloaded from the upstream w-okada/voice-changer release when
available. The upstream project does not publish a 2.0.78-beta GitHub release, so
this step is best-effort only. For a zero-setup experience, use the bundled
IstarVoiceChanger.exe (engine included) or point the launcher at an existing
main.exe. The engine is licensed separately (CC BY-NC 4.0).

Usage:
    python setup.py            # install deps + download engine
    python setup.py --deps     # only install dependencies
    python setup.py --engine   # only download the engine
"""

import argparse
import json
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

UPSTREAM_REPO = "w-okada/voice-changer"
ENGINE_VERSION = "2.0.78-beta"
ENGINE_RELEASE_URL = f"https://github.com/{UPSTREAM_REPO}/releases/download/{ENGINE_VERSION}"

BASE_DIR = Path(__file__).parent
ENGINE_DIR = BASE_DIR / "engine"
DIST_DIR = ENGINE_DIR / "dist"
MAIN_EXE = DIST_DIR / "main.exe"

PY_DEPS = ["psutil", "py7zr", "pyinstaller"]


def run(cmd):
    print(f">>> {' '.join(cmd)}")
    subprocess.check_call(cmd)


def install_deps():
    print("Installing Python dependencies...")
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install"] + PY_DEPS)
    print("Dependencies installed.")


def download_engine():
    if MAIN_EXE.exists():
        print(f"Engine already present: {MAIN_EXE}")
        return

    ENGINE_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [
        f"voice-changer_{ENGINE_VERSION}_cpu.7z",
        f"voice-changer_{ENGINE_VERSION}_std.7z",
        f"voice-changer_{ENGINE_VERSION}.7z",
    ]
    for cand in candidates:
        url = f"{ENGINE_RELEASE_URL}/{cand}"
        dest = ENGINE_DIR / cand
        try:
            print(f"Downloading {url} ...")
            urllib.request.urlretrieve(url, dest)
            print(f"Downloaded {cand}")
            extract_engine(dest)
            return
        except urllib.error.URLError as e:
            print(f"  candidate not found: {e}")
            continue

    # Best-effort only: the upstream project does not publish a 2.0.78-beta
    # GitHub release, so auto-download is expected to fail. The recommended
    # path is the self-contained IstarVoiceChanger.exe (engine bundled), or
    # pointing the launcher at an existing main.exe via "Use existing main.exe".
    print("NOTE: could not auto-download the engine (no upstream release for this version).")
    print("This is expected. Options:")
    print("  - Use the bundled IstarVoiceChanger.exe (engine included).")
    print("  - In the launcher, click 'Use existing main.exe' and select your main.exe.")
    print(f"  - Or get it from upstream: https://github.com/{UPSTREAM_REPO}")


def extract_engine(archive_path: Path):
    try:
        import py7zr
    except ImportError:
        print("py7zr is required to extract the engine. Install with: pip install py7zr")
        return
    print(f"Extracting {archive_path.name} ...")
    py7zr.unpack_7z(str(archive_path), str(ENGINE_DIR))
    archive_path.unlink(missing_ok=True)
    if MAIN_EXE.exists():
        print(f"Engine ready at {MAIN_EXE}")
    else:
        print("Extraction finished but main.exe was not found. Check the archive layout.")


def main():
    parser = argparse.ArgumentParser(description="Istar Voice Changer setup")
    parser.add_argument("--deps", action="store_true", help="only install dependencies")
    parser.add_argument("--engine", action="store_true", help="only download the engine")
    args = parser.parse_args()

    if args.deps:
        install_deps()
    elif args.engine:
        download_engine()
    else:
        install_deps()
        download_engine()

    print("Setup complete.")


if __name__ == "__main__":
    main()
