#!/usr/bin/env python3
"""
Istar Voice Changer - Setup (MIT)
=================================

Installs the Python dependencies needed to run the launcher from source.

    python setup.py

Requirements:
  * Python 3.10 or 3.11 (onnxruntime + librosa are tested here).
  * The RVC engine uses ONNX Runtime, so NO PyTorch / fairseq / CUDA build
    is required.

The voice models live in models/ (ContentVec + .onnx voices) and are
downloaded separately or bundled with the EXE.
"""

import subprocess
import sys

DEPS = [
    "onnxruntime",
    "librosa",
    "numpy",
    "soundfile",
    "pyaudio",
    "pyinstaller",
]


def main():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + DEPS)
    print("\nDependencies installed. Run:  python launcher.py")


if __name__ == "__main__":
    main()
