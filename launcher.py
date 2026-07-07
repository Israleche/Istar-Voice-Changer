#!/usr/bin/env python3
"""
Istar Voice Changer - Launcher
A user-friendly GUI launcher for the Istar Voice Changer (fork of w-okada/voice-changer).

This launcher wraps the original voice-changer engine (main.exe) with a simple
interface: start/stop the server, configure port/mode, open the web UI, and
download the engine if it is missing.

Credits:
- Original engine: w-okada/voice-changer (https://github.com/w-okada/voice-changer)
  Licensed under CC BY-NC 4.0 (see LICENSE in the upstream repo).
- This launcher and packaging: Istar Voice Changer project.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import json
import time
import sys
import shutil
import urllib.request
import urllib.error
import webbrowser
import platform
import threading
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_NAME = "Istar Voice Changer"
APP_VERSION = "0.1.0"
UPSTREAM_REPO = "w-okada/voice-changer"          # original project (credit)
FORK_REPO = "Israleche/Istar-Voice-Changer"      # this project
ENGINE_VERSION = "2.0.78-beta"                    # engine release tag

# The engine (main.exe) is downloaded separately to keep the repo light.
ENGINE_RELEASE_URL = (
    f"https://github.com/{UPSTREAM_REPO}/releases/download/{ENGINE_VERSION}"
)

BASE_DIR = Path(__file__).parent
ENGINE_DIR = BASE_DIR / "engine"
DIST_DIR = ENGINE_DIR / "dist"
MAIN_EXE = DIST_DIR / "main.exe"
LOG_FILE = BASE_DIR / "logs" / "launcher.log"
CONFIG_FILE = BASE_DIR / "config.json"

# Colors (modern, light theme)
COLORS = {
    "primary": "#6366F1",      # indigo
    "secondary": "#10B981",    # emerald
    "danger": "#EF4444",       # red
    "warning": "#F59E0B",      # amber
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "text": "#1E293B",
    "muted": "#64748B",
    "header": "#1E1B4B",       # deep indigo
    "success": "#10B981",
    "border": "#E2E8F0",
}


class VoiceChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("920x680")
        self.root.minsize(820, 580)
        self.root.configure(bg=COLORS["background"])

        self.server_process = None
        self.is_running = False

        self._create_widgets()
        self._load_config()
        self._refresh_engine_status()

    # ------------------------------------------------------------------ UI
    def _create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=COLORS["header"], height=84)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=APP_NAME, font=("Segoe UI", 22, "bold"),
                 fg="white", bg=COLORS["header"]).pack(side=tk.LEFT, padx=22, pady=8)
        tk.Label(header, text=f"v{APP_VERSION}  ·  fork of {UPSTREAM_REPO}",
                 font=("Segoe UI", 10), fg="#A5B4FC", bg=COLORS["header"]).pack(side=tk.LEFT, padx=8)

        self.header_status = tk.Label(header, text="● Offline",
                                       font=("Segoe UI", 10, "bold"),
                                       fg=COLORS["danger"], bg=COLORS["header"])
        self.header_status.pack(side=tk.RIGHT, padx=22)

        # Main content
        main = tk.Frame(self.root, bg=COLORS["background"])
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        left = tk.Frame(main, bg=COLORS["background"])
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left.pack_propagate(False)
        left.configure(width=360)

        right = tk.Frame(main, bg=COLORS["background"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._create_left_panel(left)
        self._create_right_panel(right)

    def _create_left_panel(self, parent):
        # Engine status card
        card0 = self._card(parent, "🔧 Engine")
        self.engine_status_var = tk.StringVar(value="Checking...")
        tk.Label(card0, textvariable=self.engine_status_var, font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor=tk.W, padx=15, pady=(0, 8))
        self.download_btn = tk.Button(card0, text="⬇ Download Engine",
                                      command=self._download_engine,
                                      font=("Segoe UI", 10, "bold"),
                                      bg=COLORS["primary"], fg="white",
                                      relief=tk.FLAT, padx=10, pady=6, cursor="hand2")
        self.download_btn.pack(fill=tk.X, padx=15, pady=(0, 10))
        self.download_btn.pack_forget()  # hidden until needed

        # Control card
        card1 = self._card(parent, "🎮 Control")
        self.start_btn = tk.Button(card1, text="▶  Start Voice Changer",
                                    command=self.toggle_server,
                                    font=("Segoe UI", 12, "bold"),
                                    bg=COLORS["secondary"], fg="white",
                                    relief=tk.FLAT, padx=20, pady=12, cursor="hand2")
        self.start_btn.pack(fill=tk.X, padx=15, pady=10)

        self.status_var = tk.StringVar(value="Status: Stopped")
        tk.Label(card1, textvariable=self.status_var, font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(pady=(0, 10))

        # Config card
        card2 = self._card(parent, "⚙️ Configuration")
        port_frame = tk.Frame(card2, bg=COLORS["surface"])
        port_frame.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(port_frame, text="Port:", font=("Segoe UI", 10),
                 bg=COLORS["surface"]).pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="18000")
        tk.Entry(port_frame, textvariable=self.port_var, font=("Segoe UI", 10), width=8).pack(side=tk.LEFT, padx=10)

        mode_frame = tk.Frame(card2, bg=COLORS["surface"])
        mode_frame.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(mode_frame, text="Mode:", font=("Segoe UI", 10),
                 bg=COLORS["surface"]).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="http")
        tk.Radiobutton(mode_frame, text="HTTP", variable=self.mode_var, value="http",
                       bg=COLORS["surface"]).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="HTTPS", variable=self.mode_var, value="https",
                       bg=COLORS["surface"]).pack(side=tk.LEFT, padx=10)

        # Actions card
        card3 = self._card(parent, "🚀 Actions")
        tk.Button(card3, text="📁 Open Engine Folder", command=self.open_engine_dir,
                  font=("Segoe UI", 10), bg=COLORS["primary"], fg="white",
                  relief=tk.FLAT, padx=10, pady=5).pack(fill=tk.X, padx=15, pady=3)
        tk.Button(card3, text="🌐 Open Web UI", command=self.open_web_interface,
                  font=("Segoe UI", 10), bg=COLORS["primary"], fg="white",
                  relief=tk.FLAT, padx=10, pady=5).pack(fill=tk.X, padx=15, pady=3)
        tk.Button(card3, text="📊 System Info", command=self.show_system_info,
                  font=("Segoe UI", 10), bg=COLORS["primary"], fg="white",
                  relief=tk.FLAT, padx=10, pady=5).pack(fill=tk.X, padx=15, pady=3)
        tk.Button(card3, text="⭐ Project / Source", command=lambda: webbrowser.open(f"https://github.com/{FORK_REPO}"),
                  font=("Segoe UI", 10), bg=COLORS["warning"], fg="white",
                  relief=tk.FLAT, padx=10, pady=5).pack(fill=tk.X, padx=15, pady=3)

    def _create_right_panel(self, parent):
        info_card = self._card(parent, "ℹ️ System Information")
        self.info_text = tk.Text(info_card, height=8, font=("Consolas", 9),
                                 bg="#F8FAFC", relief=tk.FLAT, bd=0, padx=10, pady=10)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.info_text.config(state=tk.DISABLED)

        log_card = self._card(parent, "📋 Logs")
        self.log_text = tk.Text(log_card, height=12, font=("Consolas", 9),
                                bg="#1E1E1E", fg="#D4D4D4", relief=tk.FLAT, bd=0, padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.log_text.config(state=tk.DISABLED)

        self._update_system_info()

    def _card(self, parent, title):
        card = tk.Frame(parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, pady=(0, 10))
        card.configure(highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Label(card, text=title, font=("Segoe UI", 11, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor=tk.W, padx=15, pady=(10, 5))
        return card

    # -------------------------------------------------------------- engine
    def _refresh_engine_status(self):
        if MAIN_EXE.exists():
            size_mb = MAIN_EXE.stat().st_size / (1024 * 1024)
            self.engine_status_var.set(f"✓ Engine found ({size_mb:.0f} MB)")
            self.download_btn.pack_forget()
        else:
            self.engine_status_var.set("✗ Engine not found (main.exe missing)")
            self.download_btn.pack(fill=tk.X, padx=15, pady=(0, 10))

    def _download_engine(self):
        if MAIN_EXE.exists():
            return
        threading.Thread(target=self._download_engine_thread, daemon=True).start()

    def _download_engine_thread(self):
        self.download_btn.config(state=tk.DISABLED, text="⬇ Downloading...")
        self._log(f"Downloading engine from {ENGINE_RELEASE_URL} ...", "INFO")
        try:
            ENGINE_DIR.mkdir(parents=True, exist_ok=True)
            # The upstream release provides a zip; we download and extract.
            candidates = [
                f"voice-changer_{ENGINE_VERSION}_cpu.7z",
                f"voice-changer_{ENGINE_VERSION}_std.7z",
                f"voice-changer_{ENGINE_VERSION}.7z",
            ]
            downloaded = False
            for cand in candidates:
                url = f"{ENGINE_RELEASE_URL}/{cand}"
                dest = ENGINE_DIR / cand
                try:
                    urllib.request.urlretrieve(url, dest)
                    downloaded = True
                    self._log(f"Downloaded {cand}", "SUCCESS")
                    break
                except urllib.error.URLError:
                    continue
            if not downloaded:
                self._log("Could not auto-download. Open the release page manually.", "ERROR")
                webbrowser.open(f"https://github.com/{UPSTREAM_REPO}/releases/tag/{ENGINE_VERSION}")
                self.download_btn.config(state=tk.NORMAL, text="⬇ Download Engine")
                return
            self._extract_engine(dest)
        except Exception as e:
            self._log(f"Download failed: {e}", "ERROR")
            self.download_btn.config(state=tk.NORMAL, text="⬇ Download Engine")

    def _extract_engine(self, archive_path):
        try:
            import py7zr
            py7zr.unpack_7z(str(archive_path), str(ENGINE_DIR))
            archive_path.unlink(missing_ok=True)
            self._log("Engine extracted.", "SUCCESS")
            self._refresh_engine_status()
            self.download_btn.config(state=tk.NORMAL, text="⬇ Download Engine")
        except ImportError:
            self._log("py7zr not installed. Run: pip install py7zr", "WARNING")
            self.download_btn.config(state=tk.NORMAL, text="⬇ Download Engine")
        except Exception as e:
            self._log(f"Extraction failed: {e}", "ERROR")
            self.download_btn.config(state=tk.NORMAL, text="⬇ Download Engine")

    # -------------------------------------------------------------- server
    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if not MAIN_EXE.exists():
            messagebox.showerror("Engine missing",
                                 "The voice-changer engine (main.exe) was not found.\n"
                                 "Click 'Download Engine' or place it in engine/dist/main.exe")
            self._refresh_engine_status()
            return
        try:
            mode = self.mode_var.get()
            https_flag = "true" if mode == "https" else "false"
            cmd = [str(MAIN_EXE), "cui", "--https", https_flag, "--no_cui", "True"]

            self.server_process = subprocess.Popen(
                cmd, cwd=str(DIST_DIR),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            self.is_running = True
            self.status_var.set("Status: Starting...")
            self.header_status.config(text="● Starting...", fg=COLORS["warning"])
            self.start_btn.config(text="⏹  Stop Voice Changer", bg=COLORS["danger"])
            self._log(f"Server starting in {mode.upper()} mode...", "INFO")
            self._save_config()
            threading.Thread(target=self._wait_for_server, args=(mode,), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Could not start server:\n{e}")
            self._log(f"Start error: {e}", "ERROR")

    def _wait_for_server(self, mode):
        port = self.port_var.get()
        url = f"http://localhost:{port}" if mode == "http" else f"https://localhost:{port}"
        for _ in range(90):  # up to 90s
            if not self.is_running:
                return
            try:
                req = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(req, timeout=2) as r:
                    if r.status == 200:
                        self.root.after(0, lambda: self._on_server_ready(mode, port))
                        return
            except Exception:
                pass
            time.sleep(1)
        self.root.after(0, lambda: self._log("Warning: server took too long. Check manually.", "WARNING"))

    def _on_server_ready(self, mode, port):
        self.status_var.set("Status: Running")
        self.header_status.config(text="● Online", fg=COLORS["success"])
        self._log(f"Server ready at http://localhost:{port}", "SUCCESS")
        webbrowser.open(f"http://localhost:{port}")

    def stop_server(self):
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
        self.is_running = False
        self.status_var.set("Status: Stopped")
        self.header_status.config(text="● Offline", fg=COLORS["danger"])
        self.start_btn.config(text="▶  Start Voice Changer", bg=COLORS["secondary"])
        self._log("Server stopped", "WARNING")

    # -------------------------------------------------------------- helpers
    def open_engine_dir(self):
        if ENGINE_DIR.exists():
            os.startfile(str(ENGINE_DIR))
        else:
            messagebox.showwarning("Warning", f"Folder not found: {ENGINE_DIR}")

    def open_web_interface(self):
        mode = self.mode_var.get()
        port = self.port_var.get()
        url = f"http://localhost:{port}" if mode == "http" else f"https://localhost:{port}"
        webbrowser.open(url)

    def show_system_info(self):
        info = [f"OS: {platform.system()} {platform.release()}",
                f"Python: {platform.python_version()}",
                f"Arch: {platform.machine()}"]
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                info.append(f"RAM: {mem.total/1e9:.1f} GB ({mem.percent}% used)")
            except Exception:
                pass
        messagebox.showinfo("System Info", "\n".join(info))

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                cfg = json.load(open(CONFIG_FILE))
                self.port_var.set(cfg.get("port", "18000"))
                self.mode_var.set(cfg.get("mode", "http"))
            except Exception:
                pass

    def _save_config(self):
        json.dump({"port": self.port_var.get(), "mode": self.mode_var.get()},
                  open(CONFIG_FILE, "w"), indent=2)

    def _log(self, message, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{ts}] [{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] [{level}] {message}\n")

    def _update_system_info(self):
        info = [f"OS: {platform.system()} {platform.release()}",
                f"Python: {platform.python_version()}",
                f"Engine dir: {ENGINE_DIR}"]
        if MAIN_EXE.exists():
            info.append(f"✓ main.exe present ({MAIN_EXE.stat().st_size/1e6:.0f} MB)")
        else:
            info.append("✗ main.exe missing — use Download Engine")
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                info.append(f"RAM: {mem.total/1e9:.1f} GB total, {mem.percent}% used")
            except Exception:
                pass
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "\n".join(info))
        self.info_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.is_running and messagebox.askyesno("Confirm", "Stop the server before closing?"):
            self.stop_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = VoiceChangerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
