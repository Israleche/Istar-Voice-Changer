#!/usr/bin/env python3
"""
Istar Voice Changer - All-in-One Launcher & Installer
=====================================================

A single, user-friendly GUI that:
  * Installs everything with ONE click (extracts the bundled engine, installs
    Python deps if needed).
  * Starts/stops the voice-changer server.
  * Opens the web UI automatically when ready.

No prior setup required. If the engine is bundled next to this EXE (in an
`engine_dist` folder), it is extracted on first run. Otherwise the user can
point the installer at an existing main.exe, or download it.

Credits:
- Original engine: w-okada/voice-changer (CC BY-NC 4.0).
- Launcher/installer: Istar Voice Changer project (MIT).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
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
APP_VERSION = "0.2.1"
UPSTREAM_REPO = "w-okada/voice-changer"
FORK_REPO = "Israleche/Istar-Voice-Changer"
ENGINE_VERSION = "2.0.78-beta"

# When bundled as an EXE, resources live next to the executable. When run from
# source, they live next to this script.
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
    # PyInstaller extracts --add-data into a temp folder named _MEIPASS.
    _MEIPASS = Path(getattr(sys, "_MEIPASS", str(APP_DIR)))
else:
    APP_DIR = Path(__file__).parent
    _MEIPASS = APP_DIR

# The engine is stored either bundled (engine_dist/) or extracted (engine/).
# When frozen, the bundled engine may live inside _MEIPASS (PyInstaller) or
# next to the EXE (if the user dropped engine_dist beside it).
BUNDLED_ENGINE_DIRS = [APP_DIR / "engine_dist", _MEIPASS / "engine_dist"]
BUNDLED_ENGINE = APP_DIR / "engine_dist"          # primary (used for extraction source)
EXTRACTED_ENGINE = APP_DIR / "engine"            # where it gets extracted to
DIST_DIR = EXTRACTED_ENGINE / "dist"
MAIN_EXE = DIST_DIR / "main.exe"


def _find_bundled_engine() -> Path | None:
    """Return the first existing bundled engine_dist directory, or None."""
    for d in BUNDLED_ENGINE_DIRS:
        if d.exists() and (d / "dist" / "main.exe").exists():
            return d
        if d.exists() and (d / "main.exe").exists():
            return d
    return None
LOG_FILE = APP_DIR / "logs" / "launcher.log"
CONFIG_FILE = APP_DIR / "config.json"

# Colors (modern, light theme)
COLORS = {
    "primary": "#6366F1",
    "secondary": "#10B981",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "text": "#1E293B",
    "muted": "#64748B",
    "header": "#1E1B4B",
    "success": "#10B981",
    "border": "#E2E8F0",
}


class VoiceChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("920x700")
        self.root.minsize(820, 600)
        self.root.configure(bg=COLORS["background"])

        self.server_process = None
        self.is_running = False

        self._create_widgets()
        self._load_config()
        self._refresh_engine_status()

    # ------------------------------------------------------------------ UI
    def _create_widgets(self):
        header = tk.Frame(self.root, bg=COLORS["header"], height=84)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=APP_NAME, font=("Segoe UI", 22, "bold"),
                 fg="white", bg=COLORS["header"]).pack(side=tk.LEFT, padx=22, pady=8)
        tk.Label(header, text=f"v{APP_VERSION}  ·  one-click installer",
                 font=("Segoe UI", 10), fg="#A5B4FC", bg=COLORS["header"]).pack(side=tk.LEFT, padx=8)

        self.header_status = tk.Label(header, text="● Offline",
                                       font=("Segoe UI", 10, "bold"),
                                       fg=COLORS["danger"], bg=COLORS["header"])
        self.header_status.pack(side=tk.RIGHT, padx=22)

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
        # Install card
        card0 = self._card(parent, "🔧 Setup (one click)")
        self.engine_status_var = tk.StringVar(value="Checking...")
        tk.Label(card0, textvariable=self.engine_status_var, font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor=tk.W, padx=15, pady=(0, 8))

        self.install_btn = tk.Button(card0, text="⬇ Install / Extract Engine",
                                     command=self._install_engine,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=COLORS["primary"], fg="white",
                                     relief=tk.FLAT, padx=10, pady=6, cursor="hand2")
        self.install_btn.pack(fill=tk.X, padx=15, pady=(0, 6))

        self.browse_btn = tk.Button(card0, text="📂 Use existing main.exe",
                                    command=self._browse_engine,
                                    font=("Segoe UI", 9),
                                    bg=COLORS["surface"], fg=COLORS["text"],
                                    relief=tk.FLAT, padx=10, pady=4, cursor="hand2")
        self.browse_btn.pack(fill=tk.X, padx=15, pady=(0, 10))

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
        tk.Button(card3, text="⭐ Source / Help", command=lambda: webbrowser.open(f"https://github.com/{FORK_REPO}"),
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
            self.engine_status_var.set(f"✓ Engine ready ({size_mb:.0f} MB)")
            self.install_btn.pack_forget()
            self.browse_btn.pack_forget()
        elif _find_bundled_engine() is not None:
            self.engine_status_var.set("⚠ Engine bundled — click Install")
            self.install_btn.config(text="⬇ Extract Bundled Engine")
            self.install_btn.pack(fill=tk.X, padx=15, pady=(0, 6))
            self.browse_btn.pack(fill=tk.X, padx=15, pady=(0, 10))
        else:
            self.engine_status_var.set("✗ Engine missing")
            self.install_btn.config(text="⬇ Install / Extract Engine")
            self.install_btn.pack(fill=tk.X, padx=15, pady=(0, 6))
            self.browse_btn.pack(fill=tk.X, padx=15, pady=(0, 10))

    def _install_engine(self):
        if MAIN_EXE.exists():
            return
        threading.Thread(target=self._install_engine_thread, daemon=True).start()

    def _install_engine_thread(self):
        self.install_btn.config(state=tk.DISABLED, text="⬇ Installing...")
        try:
            bundled = _find_bundled_engine()
            if bundled is not None:
                self._log("Extracting bundled engine...", "INFO")
                EXTRACTED_ENGINE.mkdir(parents=True, exist_ok=True)
                # Copy the bundled dist folder to engine/dist
                bundled_dist = bundled / "dist"
                if bundled_dist.exists():
                    if DIST_DIR.exists():
                        shutil.rmtree(DIST_DIR)
                    shutil.copytree(bundled_dist, DIST_DIR)
                else:
                    # Copy whole bundled folder content
                    for item in bundled.iterdir():
                        dest = EXTRACTED_ENGINE / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)
                self._log("Engine extracted.", "SUCCESS")
            else:
                # Try to download (best-effort; may fail if no release)
                self._log("No bundled engine. Attempting download...", "INFO")
                if not self._try_download():
                    self._log("Auto-install unavailable. Use 'Browse' to select main.exe.", "ERROR")
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Engine needed",
                        "The engine (main.exe) could not be downloaded automatically.\n\n"
                        "Click 'Use existing main.exe' and select the main.exe you already have,\n"
                        "or download it from the upstream project."))
            self.root.after(0, self._refresh_engine_status)
        except Exception as e:
            self._log(f"Install failed: {e}", "ERROR")
        finally:
            self.root.after(0, lambda: self.install_btn.config(state=tk.NORMAL, text="⬇ Install / Extract Engine"))

    def _try_download(self):
        # Best-effort download from known upstream release patterns.
        candidates = [
            f"https://github.com/{UPSTREAM_REPO}/releases/download/{ENGINE_VERSION}/voice-changer_{ENGINE_VERSION}_cpu.7z",
            f"https://github.com/{UPSTREAM_REPO}/releases/download/{ENGINE_VERSION}/voice-changer_{ENGINE_VERSION}_std.7z",
        ]
        EXTRACTED_ENGINE.mkdir(parents=True, exist_ok=True)
        for url in candidates:
            try:
                dest = EXTRACTED_ENGINE / "engine.7z"
                urllib.request.urlretrieve(url, dest)
                try:
                    import py7zr
                    py7zr.unpack_7z(str(dest), str(EXTRACTED_ENGINE))
                    dest.unlink(missing_ok=True)
                    return MAIN_EXE.exists()
                except ImportError:
                    self._log("py7zr missing; cannot extract.", "WARNING")
                    return False
            except urllib.error.URLError:
                continue
        return False

    def _browse_engine(self):
        path = filedialog.askopenfilename(
            title="Select main.exe (voice-changer engine)",
            filetypes=[("Executable", "main.exe"), ("All", "*.*")])
        if not path:
            return
        EXTRACTED_ENGINE.mkdir(parents=True, exist_ok=True)
        if DIST_DIR.exists():
            shutil.rmtree(DIST_DIR)
        DIST_DIR.mkdir(parents=True)
        # Copy the selected exe and its sibling files (start_*.bat, web_front, etc.)
        src_dir = Path(path).parent
        for item in src_dir.iterdir():
            dest = DIST_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        self._log(f"Engine installed from {src_dir}", "SUCCESS")
        self._refresh_engine_status()

    # -------------------------------------------------------------- server
    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if not MAIN_EXE.exists():
            messagebox.showerror("Engine missing",
                                 "The engine is not installed yet.\nClick 'Install / Extract Engine' "
                                 "or 'Use existing main.exe' first.")
            self._refresh_engine_status()
            return
        try:
            mode = self.mode_var.get()
            https_flag = "true" if mode == "https" else "false"
            port = self.port_var.get()
            # The engine listens on -p (default 18888). We must pass the port the
            # user configured, otherwise the launcher waits on the wrong port and
            # the server is never detected as ready.
            cmd = [str(MAIN_EXE), "cui", "-p", port, "--https", https_flag, "--no_cui", "True"]
            self.server_process = subprocess.Popen(
                cmd, cwd=str(DIST_DIR),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
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
        for _ in range(90):
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
        scheme = "https" if mode == "https" else "http"
        self._log(f"Server ready at {scheme}://localhost:{port}", "SUCCESS")
        webbrowser.open(f"{scheme}://localhost:{port}")

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
        d = DIST_DIR if DIST_DIR.exists() else EXTRACTED_ENGINE
        if d.exists():
            os.startfile(str(d))
        else:
            messagebox.showwarning("Warning", f"Folder not found: {d}")

    def open_web_interface(self):
        mode = self.mode_var.get()
        port = self.port_var.get()
        webbrowser.open(f"http://localhost:{port}" if mode == "http" else f"https://localhost:{port}")

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
                f"App dir: {APP_DIR}"]
        if MAIN_EXE.exists():
            info.append(f"✓ main.exe present ({MAIN_EXE.stat().st_size/1e6:.0f} MB)")
        elif _find_bundled_engine() is not None:
            info.append("⚠ Bundled engine not extracted yet")
        else:
            info.append("✗ main.exe missing — install first")
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
