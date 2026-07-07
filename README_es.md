# Istar Voice Changer

> Un cambiador de voz en tiempo real, gratuito y de código abierto. Fácil de usar,
> compatible con MIT, y distribuido como un EXE portable **o** un instalador
> profesional de Windows.

[![Licencia: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.launcher)

---

## ✨ ¿Qué es esto?

**Istar Voice Changer** es un cambiador de voz ligero y amigable basado en
**RVC (Retrieval-based Voice Conversion)** exportado a **ONNX**. Convierte tu voz
en tiempo real usando modelos de IA — sin terminal, sin instalar Python, sin
descargas de 2 GB.

A diferencia de forks pesados que empaquetan un engine de 2 GB, este proyecto usa
un **pipeline puramente ONNX** (ContentVec + generador de voz) que corre en CPU con
`onnxruntime`. Toda la app pesa ~500 MB y el código es MIT.

### ¿Por qué ONNX?
- ✅ Sin PyTorch, sin fairseq, sin compilación de CUDA
- ✅ Ejecutable pequeño, rápido y portable
- ✅ Licencia compatible con MIT (RVC-Project es MIT)

---

## 🎮 Características

- 🎤 **Conversión de voz en tiempo real** — habla al micrófono, escucha la voz cambiada
- 🖥️ **Interfaz simple** — elige voz, dispositivo de entrada/salida, pulsa Iniciar
- 🎚️ **Cambio de tono** — desliza semitonos hacia arriba/abajo
- 📦 **EXE portable** — un solo archivo, doble clic para ejecutar
- 💿 **Instalador (NSIS)** — acceso directo en Inicio + escritorio + desinstalador
- 🔌 **Listo para cable virtual** — enruta la salida a VB-Audio / Voicemeeter para Discord
- ➕ **Trae tus propias voces** — suelta cualquier RVC v2 `.onnx` en `models/voices/`

---

## 📥 Descargar

Ve a la página de [Releases](https://github.com/Israleche/Istar-Voice-Changer/releases):

| Archivo | Úsalo si |
|---------|----------|
| `IstarVoiceChanger.exe` | Quieres la app **portable** — solo ejecútala |
| `IstarVoiceChanger-Setup.exe` | Quieres una **instalación profesional** con accesos directos |

---

## 🚀 Inicio rápido (portable)

1. Descarga `IstarVoiceChanger.exe`.
2. Haz doble clic.
3. Elige una **Voz**, tu **Micrófono** y tus **Altavoces** (o un cable virtual).
4. Pulsa **▶ Start** y habla.

Eso es todo.

> 💡 Para Discord/juegos: instala [VB-Audio Virtual Cable](https://vb-audio.com/Cable/),
> pon la **salida** de la app en "CABLE Input" y la entrada de tu app en "CABLE Output".

---

## 🛠️ Compilar desde el código

```powershell
# 1. Usa Python 3.10 o 3.11
py -3.11 -m pip install -r requirements.txt   # o: python setup.py

# 2. Ejecuta la interfaz
py -3.11 launcher.py

# 3. (opcional) Compila el EXE portable
py -3.11 build_installer.py

# 4. (opcional) Compila el instalador NSIS (requiere NSIS)
makensis installer\IstarVoiceChanger.nsi
```

---

## 🧠 Cómo funciona

```
mic ─▶ ContentVec-768 (ONNX) ─▶ características
    └▶ Yin F0 (librosa)      ─▶ tono
características + tono ─▶ generador de voz net_g (ONNX) ─▶ audio cambiado ─▶ altavoces
```

Las tres etapas corren en CPU vía `onnxruntime`. Sin llamadas de red, sin telemetría.

---

## 📂 Estructura del proyecto

```
Istar-Voice-Changer/
├── launcher.py          # interfaz tkinter (MIT)
├── voice_engine.py      # motor de inferencia RVC-ONNX (MIT)
├── build_installer.py   # script de build PyInstaller
├── setup.py             # instalador de dependencias
├── requirements.txt     # dependencias fijadas
├── installer/           # script NSIS del instalador
├── models/
│   ├── contentvec.onnx  # extractor HuBERT (MIT)
│   ├── voices/          # tus modelos de voz RVC v2 .onnx
│   └── README.md        # fuentes y licencias de modelos
└── LICENSE.launcher     # licencia MIT de nuestro código
```

---

## 📜 Licencia

- **Código (launcher, motor, scripts):** MIT — ver `LICENSE.launcher`.
- **Modelos:** RVC es MIT (RVC-Project). Los ONNX incluidos son exportes MIT;
  los modelos de voz de la comunidad que añadas pueden tener sus propios términos.
  Usa solo pesos obtenidos legalmente y con la licencia adecuada.

---

## ❤️ Créditos

- [RVC-Project / Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) (MIT)
- [TigreGotico/voiceclonnx-rvc](https://huggingface.co/TigreGotico/voiceclonnx-rvc) — ContentVec-768 ONNX
- [Cycl0/voice-changer-models](https://huggingface.co/Cycl0/voice-changer-models) — voz de ejemplo ONNX
