#!/usr/bin/env python3
"""
Istar Voice Changer - Installer Builder
========================================

Builds a single, ready-to-use EXE that bundles the voice-changer engine so the
end user needs ZERO setup: just run the EXE, click "Install", and go.

What it does:
  1. Locates the engine (main.exe + siblings) from --engine-dir or a default path.
  2. Copies it into engine_dist/ next to the launcher.
  3. Compiles launcher.py into a one-file EXE with PyInstaller, embedding engine_dist.

Usage:
    python build_installer.py --engine-dir "C:/path/to/voice-changer/dist"
    python build_installer.py   # auto-detects common locations
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent
LAUNCHER = APP_DIR / "launcher.py"
BUNDLED = APP_DIR / "engine_dist"
DIST = BUNDLED / "dist"


def find_engine() -> Path | None:
    candidates = [
        APP_DIR / "engine" / "dist",
        Path.home() / "Documents" / "GitHub" / "w-okada" / "voice-changer" / "dist",
        Path("C:/Users/Isra/Documents/GitHub/w-okada/voice-changer/dist"),
    ]
    for c in candidates:
        if (c / "main.exe").exists():
            return c
    return None


def bundle_engine(engine_dir: Path):
    print(f"Bundling engine from: {engine_dir}")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for item in engine_dir.iterdir():
        dest = DIST / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    print(f"Engine bundled at: {DIST}")


def build_exe():
    print("Building EXE with PyInstaller...")
    # Prefer the pyinstaller console script; fall back to `python -m PyInstaller`
    # (the module is importable even when the `pyinstaller` script is not on PATH).
    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller:
        cmd = [pyinstaller]
    else:
        pyinstaller = f"{sys.executable} -m PyInstaller"
        cmd = [sys.executable, "-m", "PyInstaller"]
    print(f"Using: {pyinstaller}")
    cmd += [
        "--onefile", "--windowed",
        "--name", "IstarVoiceChanger",
        "--add-data", f"{BUNDLED};engine_dist",
        str(LAUNCHER),
    ]
    subprocess.check_call(cmd)
    print("EXE built at: dist/IstarVoiceChanger.exe")


def main():
    parser = argparse.ArgumentParser(description="Build Istar Voice Changer installer EXE")
    parser.add_argument("--engine-dir", type=str, default=None,
                        help="Path to the voice-changer dist folder containing main.exe")
    args = parser.parse_args()

    engine_dir = Path(args.engine_dir) if args.engine_dir else find_engine()
    if not engine_dir or not (engine_dir / "main.exe").exists():
        print("ERROR: could not find main.exe. Pass --engine-dir.")
        sys.exit(1)

    bundle_engine(engine_dir)
    build_exe()
    print("\nDone! Distribute dist/IstarVoiceChanger.exe — it is fully self-contained.")


if __name__ == "__main__":
    main()
