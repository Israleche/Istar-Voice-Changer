# Istar Voice Changer

> A free, open-source, real-time voice changer. Simple to use, MIT-friendly, and
> shipped as a single portable EXE **or** a professional Windows installer.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.launcher)

---

## ✨ What is this?

**Istar Voice Changer** is a lightweight, user-friendly voice changer built on
**RVC (Retrieval-based Voice Conversion)** exported to **ONNX**. It converts your
voice in real time using AI voice models — no terminal, no Python setup, no 2 GB
downloads.

Unlike heavy forks that bundle a 2 GB engine, this project uses a **pure-ONNX
pipeline** (ContentVec + voice generator) that runs on CPU with `onnxruntime`.
The whole app is ~500 MB and the code is MIT-licensed.

### Why ONNX?
- ✅ No PyTorch, no fairseq, no CUDA build step
- ✅ Small, fast, portable executable
- ✅ MIT-friendly licensing (RVC-Project is MIT)

---

## 🎮 Features

- 🎤 **Real-time voice conversion** — speak into your mic, hear the changed voice
- 🖥️ **Simple GUI** — pick a voice, pick input/output devices, hit Start
- 🎚️ **Pitch shift** — slide semitones up/down
- 📦 **Portable EXE** — one file, double-click to run
- 💿 **Installer (NSIS)** — Start Menu + desktop shortcut + uninstaller
- 🔌 **Virtual cable ready** — route output to VB-Audio / Voicemeeter for Discord,
  games, etc.
- ➕ **Bring your own voices** — drop any RVC v2 `.onnx` into `models/voices/`

---

## 📥 Download

Go to the [Releases](https://github.com/Israleche/Istar-Voice-Changer/releases) page:

| File | Use it if |
|------|-----------|
| `IstarVoiceChanger.exe` | You want the **portable** app — just run it |
| `IstarVoiceChanger-Setup.exe` | You want a **professional install** with shortcuts |

---

## 🚀 Quick start (portable)

1. Download `IstarVoiceChanger.exe`.
2. Double-click it.
3. Pick a **Voice**, your **Microphone**, and your **Speaker** (or a virtual cable).
4. Click **▶ Start** and speak.

That's it.

> 💡 For Discord/games: install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/),
> set the app's **output** to "CABLE Input", and set your app's input to
> "CABLE Output".

---

## 🛠️ Build from source

```powershell
# 1. Use Python 3.10 or 3.11 (onnxruntime + librosa are tested there)
py -3.11 -m pip install -r requirements.txt   # or: python setup.py

# 2. Run the GUI
py -3.11 launcher.py

# 3. (optional) Build the portable EXE
py -3.11 build_installer.py

# 4. (optional) Build the NSIS installer (needs NSIS installed)
makensis installer\IstarVoiceChanger.nsi
```

---

## 🧠 How it works

```
mic ─▶ ContentVec-768 (ONNX) ─▶ features
    └▶ Yin F0 (librosa)      ─▶ pitch
features + pitch ─▶ net_g voice generator (ONNX) ─▶ changed audio ─▶ speakers
```

All three stages run on CPU via `onnxruntime`. No network calls, no telemetry.

---

## 📂 Project structure

```
Istar-Voice-Changer/
├── launcher.py          # tkinter GUI (MIT)
├── voice_engine.py      # RVC-ONNX inference engine (MIT)
├── build_installer.py   # PyInstaller build script
├── setup.py             # dependency installer
├── requirements.txt     # pinned deps
├── installer/           # NSIS script for the Windows installer
├── models/
│   ├── contentvec.onnx  # HuBERT feature extractor (MIT)
│   ├── voices/          # your RVC v2 .onnx voice models
│   └── README.md        # model sources & licensing
└── LICENSE.launcher     # MIT license for our code
```

---

## 📜 License

- **Code (launcher, engine, build scripts):** MIT — see `LICENSE.launcher`.
- **Models:** RVC is MIT (RVC-Project). Bundled ONNX models are MIT exports;
  community voice models you add may carry their own terms. Use only
  lawfully-obtained, appropriately-licensed weights.

---

## ❤️ Credits

- [RVC-Project / Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) (MIT)
- [TigreGotico/voiceclonnx-rvc](https://huggingface.co/TigreGotico/voiceclonnx-rvc) — ContentVec-768 ONNX
- [Cycl0/voice-changer-models](https://huggingface.co/Cycl0/voice-changer-models) — example voice ONNX
