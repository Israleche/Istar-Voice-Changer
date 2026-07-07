# Istar Voice Changer

> Un cambiador de voz en tiempo real, gratuito y de código abierto. Un fork comunitario de [w-okada/voice-changer](https://github.com/w-okada/voice-changer) centrado en un launcher fácil de usar, amplia compatibilidad de hardware y los mejores modelos de conversión de voz open-source.

[![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-blue.svg)](LICENSE)
[![Engine](https://img.shields.io/badge/engine-2.0.78--beta-green.svg)](https://github.com/w-okada/voice-changer/releases)

---

## ✨ ¿Qué es esto?

**Istar Voice Changer** envuelve el potente motor de [w-okada/voice-changer](https://github.com/w-okada/voice-changer) tras una GUI amigable y simple. Te permite convertir tu voz en tiempo real usando modelos open-source de última generación (RVC, Beatrice v2, DDSP-SVC, MMVC, so-vits-svc) sin tocar la línea de comandos.

Este proyecto es un **fork**: mantenemos el motor y la arquitectura del upstream, añadimos nuestro propio launcher/empaquetado, y seguimos los releases del upstream para poder fusionar mejoras de vuelta.

### Créditos y licencia

- **Motor y modelos:** © w-okada / colaboradores de voice-changer. El motor (`main.exe`) y los modelos incluidos se distribuyen bajo **CC BY-NC 4.0** (no comercial). Ver el [`LICENSE`](https://github.com/w-okada/voice-changer/blob/master/LICENSE) del upstream.
- **Launcher y empaquetado:** © Proyecto Istar Voice Changer (MIT para nuestras aportaciones — ver `LICENSE.launcher`).
- **Modelos que añadas tú:** tú eres responsable de usar pesos de modelos obtenidos legalmente y con la licencia adecuada. La mayoría de los modelos comunitarios RVC/DDSP/so-vits se comparten bajo CC BY-NC o términos no especificados.

> ⚠️ **Uso no comercial.** Esta herramienta es gratuita y está abierta para uso personal, educativo y no comercial. No la uses para suplantar a otras personas ni con fines comerciales sin los derechos correspondientes.

---

## 🚀 Características

- 🎮 **Instalador EXE de un clic** — sin Python, sin configuración, sin terminal
- 📦 **Autocontenido** — el motor va dentro del EXE; solo ejecútalo
- ⚙️ **Puerto** y modo **HTTP/HTTPS** configurables
- 🌐 **Interfaz web** — se abre automáticamente cuando el servidor está listo
- 📊 Información del sistema, logs y estado del motor a simple vista
- 🧩 Multimodelo: RVC, Beatrice v2, DDSP-SVC, MMVC, so-vits-svc
- 💻 Soporte de CPU + GPU (CUDA / DirectML / ROCm / OpenVINO) vía el motor del upstream

---

## 📦 Instalación — Para usuarios (sin configuración)

1. Descarga **`IstarVoiceChanger.exe`** desde la [página de releases](https://github.com/Israleche/Istar-Voice-Changer/releases).
2. Haz doble clic. En la primera ejecución, pulsa **⬇ Install / Extract Engine** (un botón).
3. Pulsa **▶ Start Voice Changer**.
4. La interfaz web se abre en `http://localhost:18000` cuando esté lista (~10–60 s).

Eso es todo. Sin instalar Python, sin línea de comandos.

> Si ya tienes `main.exe` en algún sitio, pulsa **📂 Use existing main.exe** y selecciónalo — sin necesidad de descargar nada.

---

## 🛠️ Instalación — Para desarrolladores

### Ejecutar desde el código fuente

```powershell
git clone https://github.com/Israleche/Istar-Voice-Changer.git
cd Istar-Voice-Changer
python setup.py          # instala dependencias (psutil, py7zr, pyinstaller)
python launcher.py      # ejecuta la GUI
```

### Compilar el EXE instalador todo-en-uno

```powershell
# Empaqueta el motor que ya tienes y luego compila un EXE autocontenido:
python build_installer.py --engine-dir "C:/ruta/a/voice-changer/dist"
# o deja que detecte ubicaciones comunes automáticamente:
python build_installer.py
```

El resultado `dist/IstarVoiceChanger.exe` es totalmente autocontenido y se puede compartir tal cual.

### Opción — Usar un motor ya compilado que tengas

Si ya tienes `main.exe` de un release de w-okada, simplemente colócalo en:

```
Istar-Voice-Changer/engine/dist/main.exe
```

El launcher lo detectará automáticamente.

---

## 🖥️ Uso

1. Ejecuta `python launcher.py` (o el `IstarVoiceChanger.exe` compilado).
2. Pulsa **▶ Start Voice Changer**.
3. Espera ~10–60 s mientras el motor carga los modelos (el estado muestra **● Starting...**).
4. Cuando aparece **● Online**, la interfaz web se abre en `http://localhost:18000`.
5. Elige un modelo de voz, configura los dispositivos de entrada/salida y habla.

> El motor tarda en cargar los modelos de IA en el primer arranque — esto es normal.

---

## 🧠 Modelos soportados y dónde conseguirlos

| Modelo | Licencia | Notas | Fuente del modelo |
|--------|----------|-------|-------------------|
| **RVC v2** | MIT (código) | Mejor latencia en tiempo real (~170 ms) | [lj1995/VoiceConversionWebUI](https://huggingface.co/lj1995/VoiceConversionWebUI) |
| **DDSP-SVC** | MIT (código) | Ligero, amigable con CPU | [SVCFusion/DDSP6.1-Pretrain](https://huggingface.co/SVCFusion/DDSP6.1-Pretrain) |
| **Beatrice v2** | CC BY-NC | TTS/VC en japonés | incluido con el motor |
| **MMVC / so-vits-svc** | AGPL-3.0 | upstream archivado | repos comunitarios HF |
| **Seed-VC** | permisiva | zero-shot, multilingüe | [Plachtaa/seed-vc](https://github.com/Plachtaa/seed-vc) |

Busca modelos comunitarios: `https://huggingface.co/models?search=rvc`

---

## 🏗️ Estructura del proyecto

```
Istar-Voice-Changer/
├── launcher.py            # GUI launcher (este proyecto, MIT)
├── setup.py              # script de dependencias + descarga del motor
├── config.json           # config del launcher (puerto, modo)
├── engine/               # motor del upstream descargado (gitignored)
│   └── dist/
│       └── main.exe      # motor voice-changer (CC BY-NC)
├── server/               # código del servidor del upstream (fork)
├── client/               # cliente web del upstream (fork)
├── trainer/              # entrenador de modelos del upstream (fork)
├── docs/                 # docs del upstream (fork)
└── logs/                 # logs del launcher
```

Los directorios `server/`, `client/`, `trainer/` y `docs/` son el **fork del upstream sin modificar** y heredan la licencia de w-okada. Solo `launcher.py`, `setup.py` y nuestros docs son aportaciones de Istar (MIT).

---

## 🔄 Mantener el upstream sincronizado

Este es un fork con un remoto `upstream`:

```powershell
git remote add upstream https://github.com/w-okada/voice-changer.git
git fetch upstream
git merge upstream/master   # o rebase
```

---

## 📋 Hoja de ruta

- [ ] Mejoras de UX estilo Applio
- [ ] Backend portable ONNX/DirectML por defecto
- [ ] Instalador de modelos de un clic desde HuggingFace
- [ ] Packs de voces preset (gratuitos, con licencia adecuada)
- [ ] Paridad de launcher en Linux/macOS

---

## ❤️ Contribuir

¡Los PR son bienvenidos! Mantén el código del launcher con licencia MIT. Respeta la CLA del upstream y el carácter no comercial del motor/modelos.

---

## 📜 Resumen de licencias

- **Motor y modelos incluidos:** CC BY-NC 4.0 (no comercial) — © w-okada / colaboradores.
- **Launcher, instalador y docs de Istar:** MIT — © Proyecto Istar Voice Changer.
- **Modelos que añadas:** según la licencia de cada modelo; usa solo pesos obtenidos legalmente.

Consulta `LICENSE`, `LICENSE.launcher` y `LICENSE-CLA` para el texto completo.
