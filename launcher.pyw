# -*- coding: utf-8 -*-
"""Лаунчер Pharmacy Ask: одна кнопка — сервис поднят и открыт в браузере.

Запуск без консоли: pythonw launcher.pyw  (или ярлык «Pharmacy Ask.bat»).
"""
import os
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import ttk

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE, ".env")
DB = os.path.join(BASE, "pharmacy.db")
DEFAULT_PORT = 8077

BG = "#f8fafc"
CARD = "#ffffff"
INK = "#202124"
MUTED = "#5f6368"
BLUE = "#1a73e8"
GREEN = "#1e8e3e"
RED = "#d93025"
BORDER = "#e8eaed"


def free_port(start=DEFAULT_PORT):
    for p in range(start, start + 20):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start


def read_env():
    data = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip()
    return data


def write_env(data):
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        for k, v in data.items():
            if v:
                f.write(f"{k}={v}\n")


class Launcher:
    def __init__(self, root):
        self.root = root
        self.proc = None
        self.port = DEFAULT_PORT
        self.env = read_env()

        root.title("Pharmacy Ask — лаунчер")
        root.configure(bg=BG)
        root.geometry("560x430")
        root.resizable(False, False)

        head = tk.Frame(root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        head.pack(fill="x", padx=14, pady=(14, 0))
        tk.Label(head, text="Pharmacy Ask", bg=CARD, fg=INK,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(head, text="вопросы к данным аптечной сети на русском", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 12))

        card = tk.Frame(root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=16, pady=(14, 6))
        self.dot = tk.Canvas(row, width=10, height=10, bg=CARD, highlightthickness=0)
        self.dot.pack(side="left", pady=(4, 0))
        self.oval = self.dot.create_oval(1, 1, 9, 9, fill="#bdc1c6", outline="")
        self.status = tk.Label(row, text="остановлен", bg=CARD, fg=MUTED,
                               font=("Segoe UI", 10, "bold"))
        self.status.pack(side="left", padx=8)

        tk.Label(card, text="КЛЮЧ CLAUDE API (без него — демо-режим на готовых вопросах)",
                 bg=CARD, fg="#80868b", font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=16)
        keyrow = tk.Frame(card, bg=CARD)
        keyrow.pack(fill="x", padx=16, pady=(4, 12))
        self.key = tk.Entry(keyrow, show="•", font=("Consolas", 9), relief="solid", bd=1)
        self.key.pack(side="left", fill="x", expand=True, ipady=5)
        self.key.insert(0, self.env.get("ANTHROPIC_API_KEY", ""))
        self.show_var = tk.IntVar()
        tk.Checkbutton(keyrow, text="показать", bg=CARD, fg=MUTED, font=("Segoe UI", 8),
                       variable=self.show_var, command=self.toggle_key,
                       activebackground=CARD).pack(side="left", padx=(8, 0))

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x", padx=16)
        self.b_start = tk.Button(btns, text="Запустить", command=self.start, bg=BLUE, fg="white",
                                 font=("Segoe UI", 10, "bold"), relief="flat", padx=18, pady=7,
                                 cursor="hand2", activebackground="#1557b0", activeforeground="white")
        self.b_start.pack(side="left")
        self.b_open = tk.Button(btns, text="Открыть в браузере", command=self.open_browser,
                                bg="#e8f0fe", fg=BLUE, font=("Segoe UI", 10, "bold"), relief="flat",
                                padx=14, pady=7, cursor="hand2", state="disabled")
        self.b_open.pack(side="left", padx=8)
        self.b_stop = tk.Button(btns, text="Остановить", command=self.stop, bg="#f1f3f4", fg=MUTED,
                                font=("Segoe UI", 10), relief="flat", padx=14, pady=7,
                                cursor="hand2", state="disabled")
        self.b_stop.pack(side="left")

        self.url_lbl = tk.Label(card, text="", bg=CARD, fg=BLUE, font=("Segoe UI", 9, "underline"),
                                cursor="hand2")
        self.url_lbl.pack(anchor="w", padx=16, pady=(10, 0))
        self.url_lbl.bind("<Button-1>", lambda e: self.open_browser())

        tk.Label(card, text="ЖУРНАЛ", bg=CARD, fg="#80868b",
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=16, pady=(10, 2))
        self.log = tk.Text(card, height=8, font=("Consolas", 8), bg="#1a1a2e", fg="#cbd5e1",
                           relief="flat", wrap="word", padx=8, pady=6)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.say("Готов к запуску. Логин admin / пароль admin.")

    # ------------------------------------------------------------------ utils
    def toggle_key(self):
        self.key.config(show="" if self.show_var.get() else "•")

    def say(self, text):
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")

    def set_state(self, color, text):
        self.dot.itemconfig(self.oval, fill=color)
        self.status.config(text=text, fg=color if color != "#bdc1c6" else MUTED)

    # ----------------------------------------------------------------- запуск
    def start(self):
        if self.proc:
            return
        key = self.key.get().strip()
        self.env["ANTHROPIC_API_KEY"] = key
        write_env(self.env)

        if not os.path.exists(DB):
            self.say("Витрины нет — собираю из Excel (это займёт несколько секунд)…")
            self.set_state("#f9ab00", "сборка витрины")
            self.root.update()
            subprocess.run([sys.executable, os.path.join(BASE, "etl.py")], cwd=BASE,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        self.port = free_port()
        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = key
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--port", str(self.port)],
            cwd=BASE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        self.set_state("#f9ab00", "запускается…")
        self.b_start.config(state="disabled")
        self.b_stop.config(state="normal")
        self.say(f"Режим: {'модель Claude' if key else 'демо (готовые вопросы)'}")
        threading.Thread(target=self.pump_log, daemon=True).start()
        threading.Thread(target=self.wait_ready, daemon=True).start()

    def pump_log(self):
        for line in self.proc.stdout:
            if any(x in line for x in ("INFO:", "ERROR", "Traceback", "error")):
                self.root.after(0, self.say, line.replace("INFO:     ", ""))

    def wait_ready(self):
        url = f"http://127.0.0.1:{self.port}/api/health"
        for _ in range(40):
            time.sleep(0.5)
            if self.proc is None:
                return
            try:
                urllib.request.urlopen(url, timeout=1)
                self.root.after(0, self.ready)
                return
            except Exception:
                continue
        self.root.after(0, self.say, "Не удалось запустить сервис — смотрите журнал.")

    def ready(self):
        self.set_state(GREEN, f"работает на порту {self.port}")
        self.b_open.config(state="normal")
        self.url_lbl.config(text=self.url())
        self.say(f"Сервис поднят: {self.url()}  (логин admin / пароль admin)")
        self.open_browser()

    def url(self):
        return f"http://127.0.0.1:{self.port}/"

    def open_browser(self):
        webbrowser.open(self.url())

    # ------------------------------------------------------------------- стоп
    def stop(self):
        if not self.proc:
            return
        p, self.proc = self.proc, None
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            p.kill()
        self.set_state("#bdc1c6", "остановлен")
        self.b_start.config(state="normal")
        self.b_stop.config(state="disabled")
        self.b_open.config(state="disabled")
        self.url_lbl.config(text="")
        self.say("Сервис остановлен.")

    def on_close(self):
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    Launcher(root)
    root.mainloop()
