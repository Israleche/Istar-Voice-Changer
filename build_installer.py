#!/usr/bin/env python3
"""
Istar Voice Changer - Build the all-in-one EXE (MIT)
=====================================================

Bundles the RVC-ONNX engine + models into a single self-contained Windows EXE
using PyInstaller. The result is a *portable* executable: double-click and run.

Usage:
    python build_installer.py            # build IstarVoiceChanger.exe
    python build_installer.py --clean    # remove build/ and dist/ first

Notes:
  * Run this with the SAME Python that has the dependencies installed
    (onnxruntime, librosa, numpy, soundfile, pyaudio, tkinter).
  * The models/ folder is embedded via --add-data.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent
LAUNCHER = APP_DIR / "launcher.py"
MODELS = APP_DIR / "models"
DIST_NAME = "IstarVoiceChanger"


def build(clean: bool):
    if clean:
        for d in (APP_DIR / "build", APP_DIR / "dist"):
            if d.exists():
                shutil.rmtree(d)

    if not MODELS.exists():
        print(f"ERROR: models/ folder not found at {MODELS}")
        sys.exit(1)

    pyinstaller = shutil.which("pyinstaller")
    cmd = []
    if pyinstaller:
        cmd = [pyinstaller]
    else:
        cmd = [sys.executable, "-m", "PyInstaller"]

    cmd += [
        "--onefile", "--windowed",
        "--name", DIST_NAME,
        "--add-data", f"{MODELS};models",
        "--hidden-import", "pyaudio",
        "--hidden-import", "onnxruntime",
        "--hidden-import", "librosa",
        str(LAUNCHER),
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    exe = APP_DIR / "dist" / f"{DIST_NAME}.exe"
    if exe.exists():
        size_gb = exe.stat().st_size / (1024 ** 3)
        print(f"\nDONE: {exe} ({size_gb:.2f} GB)")
    else:
        print("Build finished but EXE not found.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    build(args.clean)
