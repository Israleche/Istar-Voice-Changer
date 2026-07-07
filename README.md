# Istar Voice Changer

> A free, open, real-time voice changer. A community fork of [w-okada/voice-changer](https://github.com/w-okada/voice-changer) with a focus on an easy-to-use launcher, broad hardware support, and the best open-source voice-conversion models.

[![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-blue.svg)](LICENSE)
[![Engine](https://img.shields.io/badge/engine-2.0.78--beta-green.svg)](https://github.com/w-okada/voice-changer/releases)

---

## ✨ What is this?

**Istar Voice Changer** wraps the powerful [w-okada/voice-changer](https://github.com/w-okada/voice-changer) engine behind a simple, friendly GUI launcher. It lets you convert your voice in real time using state-of-the-art open models (RVC, Beatrice v2, DDSP-SVC, MMVC, so-vits-svc) without touching the command line.

This project is a **fork**: we keep the upstream engine and architecture, add our own launcher/packaging, and track upstream releases so improvements can be merged back.

### Credits & License

- **Engine & models:** © w-okada / voice-changer contributors. The engine (`main.exe`) and bundled models are distributed under **CC BY-NC 4.0** (non-commercial). See the upstream [`LICENSE`](https://github.com/w-okada/voice-changer/blob/master/LICENSE).
- **Launcher & packaging:** © Istar Voice Changer project (MIT for our own additions — see `LICENSE.launcher`).
- **Models you add:** you are responsible for using lawfully-obtained, appropriately-licensed model weights. Most community RVC/DDSP/so-vits models are shared under CC BY-NC or unspecified terms.

> ⚠️ **Non-commercial use.** This tool is free and open for personal, educational, and non-commercial use. Do not use it to impersonate others or for commercial purposes without proper rights.

---

## 🚀 Features

- 🎮 **One-click launcher** (GUI) — start/stop the server, no terminal needed
- ⚙️ Configurable **port** and **HTTP/HTTPS** mode
- 🔧 **Auto-download engine** — the 400 MB engine is fetched on demand (repo stays light)
- 🌐 **Web UI** — opens automatically when the server is ready
- 📊 System info, logs, and engine status at a glance
- 🧩 Multi-model: RVC, Beatrice v2, DDSP-SVC, MMVC, so-vits-svc
- 💻 CPU + GPU (CUDA / DirectML / ROCm / OpenVINO) support via the upstream engine

---

## 📦 Installation

### Option A — Launcher only (recommended)

```powershell
# 1. Clone
git clone https://github.com/Israleche/Istar-Voice-Changer.git
cd Istar-Voice-Changer

# 2. Run setup (installs deps + downloads the engine)
python setup.py

# 3. Launch
python launcher.py
# or build an EXE once:
pyinstaller --onefile --windowed --name IstarVoiceChanger launcher.py
```

### Option B — Use the prebuilt engine you already have

If you already have `main.exe` from w-okada's release, just place it at:

```
Istar-Voice-Changer/engine/dist/main.exe
```

The launcher will detect it automatically.

---

## 🖥️ Usage

1. Run `python launcher.py` (or the built `IstarVoiceChanger.exe`).
2. Click **▶ Start Voice Changer**.
3. Wait ~10–60 s while the engine loads models (status shows **● Starting...**).
4. When **● Online** appears, the web UI opens at `http://localhost:18000`.
5. Pick a voice model, set input/output devices, and speak.

> The engine takes time to load AI models on first start — this is normal.

---

## 🧠 Supported Models & Where to Get Them

| Model | License | Notes | Model source |
|-------|---------|-------|--------------|
| **RVC v2** | MIT (code) | Best real-time latency (~170 ms) | [lj1995/VoiceConversionWebUI](https://huggingface.co/lj1995/VoiceConversionWebUI) |
| **DDSP-SVC** | MIT (code) | Lightweight, CPU-friendly | [SVCFusion/DDSP6.1-Pretrain](https://huggingface.co/SVCFusion/DDSP6.1-Pretrain) |
| **Beatrice v2** | CC BY-NC | Japanese TTS/VC | bundled with engine |
| **MMVC / so-vits-svc** | AGPL-3.0 | archived upstream | community HF repos |
| **Seed-VC** | permissive | zero-shot, multilingual | [Plachtaa/seed-vc](https://github.com/Plachtaa/seed-vc) |

Search community models: `https://huggingface.co/models?search=rvc`

---

## 🏗️ Project Structure

```
Istar-Voice-Changer/
├── launcher.py            # GUI launcher (this project, MIT)
├── setup.py              # dependency + engine download script
├── config.json           # launcher config (port, mode)
├── engine/               # downloaded upstream engine (gitignored)
│   └── dist/
│       └── main.exe      # voice-changer engine (CC BY-NC)
├── server/               # upstream server code (forked)
├── client/               # upstream web client (forked)
├── trainer/              # upstream model trainer (forked)
├── docs/                 # upstream docs (forked)
└── logs/                 # launcher logs
```

The `server/`, `client/`, `trainer/`, and `docs/` directories are the **unmodified upstream fork** and inherit w-okada's license. Only `launcher.py`, `setup.py`, and our docs are Istar additions (MIT).

---

## 🔄 Keeping Upstream in Sync

This is a fork with an `upstream` remote:

```powershell
git remote add upstream https://github.com/w-okada/voice-changer.git
git fetch upstream
git merge upstream/master   # or rebase
```

---

## 📋 Roadmap

- [ ] Bundle Applio-style UX improvements
- [ ] ONNX/DirectML portable backend defaults
- [ ] One-click model installer from HuggingFace
- [ ] Preset voice packs (free, properly licensed)
- [ ] Linux/macOS launcher parity

---

## ❤️ Contributing

PRs welcome! Keep launcher code MIT-licensed. Respect upstream's CLA and the non-commercial nature of the engine/models.

---

## 📜 License Summary

| Component | License |
|-----------|---------|
| Launcher, setup, our docs | MIT (`LICENSE.launcher`) |
| Upstream engine & code | CC BY-NC 4.0 (upstream `LICENSE`) |
| Model weights | varies (usually CC BY-NC) — user-supplied |

See [`LICENSE`](LICENSE) (upstream) and [`LICENSE.launcher`](LICENSE.launcher) (ours).
