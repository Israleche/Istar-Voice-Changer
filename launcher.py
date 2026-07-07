#!/usr/bin/env python3
"""
Istar Voice Changer - Simple GUI launcher (MIT)
================================================

A clean, user-friendly tkinter GUI that wraps the RVC-ONNX engine for
real-time voice changing. Minimal controls:

  * Voice model   (dropdown of bundled .onnx voices)
  * Input device  (microphone)
  * Output device (speakers / virtual cable)
  * Pitch shift   (semitones)
  * Start / Stop

No terminal, no setup. Bundled as a single EXE (portable) or installed via NSIS.

Credits:
  * RVC engine & ONNX models: RVC-Project / community (MIT). See models/README.md.
  * This GUI & packaging: Istar Voice Changer (MIT).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import threading
import platform
from pathlib import Path

try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False

from voice_engine import RVCEngine, list_voice_models, RVC_SR

# --------------------------------------------------------------------------
# Paths: when frozen (PyInstaller) resources live in _MEIPASS or next to EXE.
# --------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
    _MEI = Path(getattr(sys, "_MEIPASS", str(APP_DIR)))
else:
    APP_DIR = Path(__file__).parent
    _MEI = APP_DIR

MODELS_DIR = APP_DIR / "models"
if not MODELS_DIR.exists():
    MODELS_DIR = _MEI / "models"
CONTENTVEC = MODELS_DIR / "contentvec.onnx"
VOICES_DIR = MODELS_DIR / "voices"

APP_NAME = "Istar Voice Changer"
APP_VERSION = "1.0.0"

COLORS = {
    "primary": "#6366F1", "secondary": "#10B981", "danger": "#EF4444",
    "background": "#F8FAFC", "surface": "#FFFFFF", "text": "#1E293B",
    "muted": "#64748B", "header": "#1E1B4B", "border": "#E2E8F0",
}


class VoiceChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("560x520")
        self.root.minsize(520, 480)
        self.root.configure(bg=COLORS["background"])
        self.engine = None
        self.stream = None
        self.pyaudio = None
        self.running = False
        self._build()
        self._load_voices()
        self._load_devices()

    # ------------------------------------------------------------------ UI
    def _build(self):
        header = tk.Frame(self.root, bg=COLORS["header"], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=APP_NAME, font=("Segoe UI", 20, "bold"),
                 fg="white", bg=COLORS["header"]).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(header, text=f"v{APP_VERSION}", font=("Segoe UI", 10),
                 fg="#A5B4FC", bg=COLORS["header"]).pack(side=tk.LEFT)

        body = tk.Frame(self.root, bg=COLORS["background"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # Voice model
        self._field(body, "Voice", self._voice_row)
        # Input device
        self._field(body, "Microphone (input)", self._input_row)
        # Output device
        self._field(body, "Speaker (output)", self._output_row)
        # Pitch
        self._field(body, "Pitch shift (semitones)", self._pitch_row)

        # Start / Stop
        self.start_btn = tk.Button(
            body, text="▶  Start", command=self.toggle,
            font=("Segoe UI", 13, "bold"), bg=COLORS["secondary"], fg="white",
            relief=tk.FLAT, padx=20, pady=12, cursor="hand2")
        self.start_btn.pack(fill=tk.X, pady=(14, 6))

        self.status = tk.Label(body, text="Status: Stopped",
                                font=("Segoe UI", 10), fg=COLORS["muted"],
                                bg=COLORS["background"])
        self.status.pack()

        self.log = tk.Text(body, height=5, font=("Consolas", 9),
                            bg="#1E1E1E", fg="#D4D4D4", relief=tk.FLAT, bd=0)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.log.config(state=tk.DISABLED)

    def _field(self, parent, label, builder):
        f = tk.Frame(parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        f.pack(fill=tk.X, pady=(0, 10))
        f.configure(highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Label(f, text=label, font=("Segoe UI", 10, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor=tk.W, padx=12, pady=(8, 2))
        builder(f)

    def _voice_row(self, parent):
        self.voice_var = tk.StringVar()
        self.voice_cb = ttk.Combobox(parent, textvariable=self.voice_var,
                                     font=("Segoe UI", 10), state="readonly")
        self.voice_cb.pack(fill=tk.X, padx=12, pady=(0, 8))

    def _input_row(self, parent):
        self.input_var = tk.StringVar()
        self.input_cb = ttk.Combobox(parent, textvariable=self.input_var,
                                     font=("Segoe UI", 10), state="readonly")
        self.input_cb.pack(fill=tk.X, padx=12, pady=(0, 8))

    def _output_row(self, parent):
        self.output_var = tk.StringVar()
        self.output_cb = ttk.Combobox(parent, textvariable=self.output_var,
                                      font=("Segoe UI", 10), state="readonly")
        self.output_cb.pack(fill=tk.X, padx=12, pady=(0, 8))

    def _pitch_row(self, parent):
        self.pitch_var = tk.IntVar(value=0)
        scl = tk.Scale(parent, from_=-12, to=12, orient=tk.HORIZONTAL,
                       variable=self.pitch_var, font=("Segoe UI", 9),
                       bg=COLORS["surface"], fg=COLORS["text"],
                       troughcolor=COLORS["border"], highlightthickness=0)
        scl.pack(fill=tk.X, padx=12, pady=(0, 8))

    # -------------------------------------------------------------- data
    def _load_voices(self):
        voices = list_voice_models(str(VOICES_DIR)) if VOICES_DIR.exists() else []
        if not voices:
            voices = ["(no voice models found)"]
            self.voice_cb.config(state="disabled")
        self.voice_cb["values"] = voices
        self.voice_var.set(voices[0])

    def _load_devices(self):
        if not PYAUDIO_OK:
            self.input_cb["values"] = ["(pyaudio missing)"]
            self.output_cb["values"] = ["(pyaudio missing)"]
            self.input_var.set("(pyaudio missing)")
            self.output_var.set("(pyaudio missing)")
            return
        pa = pyaudio.PyAudio()
        ins, outs = [], []
        for i in range(pa.get_device_count()):
            d = pa.get_device_info_by_index(i)
            if d["maxInputChannels"] > 0:
                ins.append(f"{i}: {d['name']}")
            if d["maxOutputChannels"] > 0:
                outs.append(f"{i}: {d['name']}")
        pa.terminate()
        self.input_cb["values"] = ins
        self.output_cb["values"] = outs
        if ins:
            self.input_var.set(ins[0])
        if outs:
            self.output_var.set(outs[0])

    # -------------------------------------------------------------- control
    def _log(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if not PYAUDIO_OK:
            messagebox.showerror("Missing dependency", "PyAudio is not installed.")
            return
        if not CONTENTVEC.exists():
            messagebox.showerror("Missing model", f"ContentVec not found:\n{CONTENTVEC}")
            return
        voice = self.voice_var.get()
        if voice.startswith("("):
            messagebox.showerror("No voice", "No voice model available.")
            return
        voice_path = VOICES_DIR / f"{voice}.onnx"
        if not voice_path.exists():
            messagebox.showerror("Missing voice", f"Voice not found:\n{voice_path}")
            return

        try:
            self.engine = RVCEngine(str(CONTENTVEC), str(voice_path))
        except Exception as e:
            messagebox.showerror("Engine error", str(e))
            return

        self.pyaudio = pyaudio.PyAudio()
        in_idx = int(self.input_var.get().split(":")[0])
        out_idx = int(self.output_var.get().split(":")[0])
        self._state = self.engine.open_stream()
        self._pitch = self.pitch_var.get()

        try:
            self.stream_out = self.pyaudio.open(
                format=pyaudio.paFloat32, channels=1, rate=RVC_SR,
                output=True, output_device_index=out_idx)
            self.stream_in = self.pyaudio.open(
                format=pyaudio.paFloat32, channels=1, rate=RVC_SR,
                input=True, input_device_index=in_idx,
                frames_per_buffer=RVC_HOP * 8,
                stream_callback=self._callback)
            self.stream_in.start_stream()
        except Exception as e:
            messagebox.showerror("Audio error", str(e))
            self._cleanup_audio()
            return

        self.running = True
        self.start_btn.config(text="⏹  Stop", bg=COLORS["danger"])
        self.status.config(text="Status: Running — speak into your mic")
        self._log("Started. Voice conversion is live.")

    def _callback(self, in_data, frame_count, time_info, status):
        import numpy as np
        chunk = np.frombuffer(in_data, dtype=np.float32)
        out = self.engine.process_chunk(self._state, chunk, pitch_shift=self._pitch)
        if out is None or len(out) == 0:
            out = np.zeros(frame_count, dtype=np.float32)
        if len(out) < frame_count:
            out = np.pad(out, (0, frame_count - len(out)))
        elif len(out) > frame_count:
            out = out[:frame_count]
        out = out.astype(np.float32)
        self.stream_out.write(out.tobytes())
        return (out.tobytes(), pyaudio.paContinue)

    def stop(self):
        self.running = False
        self._cleanup_audio()
        self.start_btn.config(text="▶  Start", bg=COLORS["secondary"])
        self.status.config(text="Status: Stopped")
        self._log("Stopped.")

    def _cleanup_audio(self):
        for attr in ("stream_in", "stream_out"):
            s = getattr(self, attr, None)
            if s is not None:
                try:
                    s.stop_stream(); s.close()
                except Exception:
                    pass
        if self.pyaudio is not None:
            try:
                self.pyaudio.terminate()
            except Exception:
                pass
            self.pyaudio = None

    def on_close(self):
        if self.running:
            self.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = VoiceChangerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
