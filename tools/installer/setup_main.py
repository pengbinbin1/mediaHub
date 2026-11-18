# setup_main.py — 极简媒体中心 安装器（用户级安装，无需管理员权限）
# 静默安装：MiniHub_Setup.exe --silent [--dir=自定义路径]
import base64
import os
import shutil
import subprocess
import sys
import threading
import traceback
import winreg
import zipfile

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_NAME = "极简媒体中心"
APP_VERSION = "1.0.0"
APP_PUBLISHER = "MiniHub"
EXE_NAME = "MiniHub.exe"
UNINSTALL_REG = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MiniHub"
DEFAULT_INSTALL_DIR = os.path.join(os.environ["LOCALAPPDATA"],
                                   "Programs", "MiniHub")


# ---------------- 路径 ----------------

def get_install_dir():
    return DEFAULT_INSTALL_DIR


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, rel)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel)


def get_desktop_dir():
    import ctypes
    from ctypes import wintypes

    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf) == 0:
        return buf.value
    return os.path.join(os.environ["USERPROFILE"], "Desktop")


def get_startmenu_dir():
    return os.path.join(os.environ["APPDATA"],
                        "Microsoft", "Windows", "Start Menu", "Programs")


# ---------------- 快捷方式（PowerShell + COM，中文路径安全） ----------------

def ps_quote(s):
    return "'" + s.replace("'", "''") + "'"


def run_ps(script):
    enc = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-EncodedCommand", enc],
        capture_output=True, timeout=60)


def make_shortcut(lnk, target, workdir):
    script = (
        "$ErrorActionPreference='Stop';"
        "$ws=New-Object -ComObject WScript.Shell;"
        f"$s=$ws.CreateShortcut({ps_quote(lnk)});"
        f"$s.TargetPath={ps_quote(target)};"
        f"$s.WorkingDirectory={ps_quote(workdir)};"
        f"$s.IconLocation={ps_quote(target + ',0')};"
        "$s.Save()")
    r = run_ps(script)
    if r.returncode != 0:
        err = r.stderr.decode("gbk", errors="replace") if r.stderr else ""
        raise RuntimeError(f"创建快捷方式失败: {lnk}\n{err}")


# ---------------- 安装 ----------------

def do_install(progress, target=None, desktop_shortcut=True):
    if target:
        target = os.path.abspath(target)
    else:
        target = get_install_dir()

    if not target or (os.path.exists(target)
                      and not os.path.isdir(target)):
        raise ValueError("安装路径无效: " + str(target))

    progress(0, 1, "准备安装…")

    # 升级场景：关闭正在运行的应用
    subprocess.run(["taskkill", "/IM", EXE_NAME, "/F"], capture_output=True)

    payload_zip = resource_path(os.path.join("payload", "payload.zip"))
    uninstall_src = resource_path(os.path.join("payload", "uninstall.exe"))

    os.makedirs(target, exist_ok=True)

    with zipfile.ZipFile(payload_zip) as zf:
        entries = [i for i in zf.infolist() if not i.is_dir()]
        total = len(entries)
        for i, info in enumerate(entries):
            zf.extract(info, target)
            if i % 20 == 0 or i == total - 1:
                progress(i + 1, total, "正在释放文件…")

    shutil.copy2(uninstall_src, os.path.join(target, "uninstall.exe"))

    exe = os.path.join(target, EXE_NAME)
    lnk_name = APP_NAME + ".lnk"
    if desktop_shortcut:
        make_shortcut(os.path.join(get_desktop_dir(), lnk_name), exe, target)
    make_shortcut(os.path.join(get_startmenu_dir(), lnk_name), exe, target)

    size_kb = sum(f.stat().st_size for f in pathlib_rglob(target)) // 1024
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG) as k:
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, target)
        winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, exe)
        winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                          '"' + os.path.join(target, "uninstall.exe") + '" /S')
        winreg.SetValueEx(k, "QuietUninstallString", 0, winreg.REG_SZ,
                          '"' + os.path.join(target, "uninstall.exe") + '" /S')
        winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, size_kb)
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
    progress(1, 1, "安装完成")


def pathlib_rglob(path):
    import pathlib
    return [p for p in pathlib.Path(path).rglob("*") if p.is_file()]


# ---------------- UI ----------------

BG = "#fafafa"
FG = "#1f2329"
MUTED = "#8a919c"
FONT = "Microsoft YaHei UI"


class InstallerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME + " 安装")
        self.root.configure(bg=BG)
        self.root.geometry("460x330")
        self.root.minsize(460, 330)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TButton", font=(FONT, 10), padding=(16, 6))
        style.configure("Primary.TButton", foreground="#ffffff",
                        background="#1f2329", padding=(18, 6))
        style.map("Primary.TButton",
                  background=[("active", "#34383e"), ("disabled", "#c5c9ce")],
                  foreground=[("disabled", "#f0f0f0")])
        style.configure("TProgressbar", thickness=4, background="#1f2329",
                        troughcolor="#e5e7ea", borderwidth=0)
        style.configure("TCheckbutton", background=BG, font=(FONT, 10))

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(outer, text=APP_NAME, font=(FONT, 17, "bold"),
                 bg=BG, fg=FG).pack(anchor="w")
        tk.Label(outer, text=f"v{APP_VERSION} · 视频 / 图片 / 文件 / 文档",
                 font=(FONT, 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 14))

        self.body = tk.Frame(outer, bg=BG)
        self.body.pack(fill="both", expand=True)

        self.btns = tk.Frame(outer, bg=BG)
        self.btns.pack(fill="x", pady=(10, 0))

        self.show_welcome()

    # ---- 状态页 ----

    def show_welcome(self):
        self._clear_body()
        tk.Label(self.body, text="安装位置", font=(FONT, 10, "bold"),
                 bg=BG, fg=FG).pack(anchor="w")

        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x", pady=(4, 10))
        self.path_var = tk.StringVar(value=get_install_dir())
        entry = tk.Entry(row, textvariable=self.path_var, font=(FONT, 10))
        entry.pack(side="left", fill="x", expand=True, ipady=4)
        browse = ttk.Button(row, text="浏览…", width=10,
                            command=self._browse_dir)
        browse.pack(side="left", padx=(8, 0))

        self.desktop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.body, text="创建桌面快捷方式",
                       variable=self.desktop_var, font=(FONT, 10),
                       bg=BG, fg=FG, activebackground=BG,
                       selectcolor="#ffffff").pack(anchor="w")
        tk.Label(self.body,
                 text="开始菜单快捷方式将自动创建 · 无需管理员权限",
                 font=(FONT, 9), bg=BG, fg=MUTED).pack(anchor="w", pady=(8, 0))

        cancel = ttk.Button(self.btns, text="取消", command=self.root.destroy)
        cancel.pack(side="left")
        ok = ttk.Button(self.btns, text="立即安装", style="Primary.TButton",
                        command=self.start_install)
        ok.pack(side="right")

    def show_installing(self):
        self._clear_body()
        for w in self.btns.winfo_children():
            w.destroy()
        self.status = tk.Label(self.body, text="正在安装…", font=(FONT, 10),
                               bg=BG, fg=MUTED)
        self.status.pack(anchor="w", pady=(0, 6))
        self.bar = ttk.Progressbar(self.body, mode="determinate", length=380)
        self.bar.pack(anchor="w")
        self.root.update()

    def show_done(self):
        self._clear_body()
        for w in self.btns.winfo_children():
            w.destroy()
        tk.Label(self.body, text="安装完成", font=(FONT, 13, "bold"),
                 bg=BG, fg=FG).pack(anchor="w", pady=(4, 6))
        self.run_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.body, text="立即运行 " + APP_NAME, variable=self.run_var,
                       font=(FONT, 10), bg=BG, fg=FG, activebackground=BG,
                       selectcolor="#ffffff").pack(anchor="w")
        ok = ttk.Button(self.btns, text="完成", style="Primary.TButton",
                        command=self.finish)
        ok.pack(side="right")

    def show_error(self, tb_text):
        self._clear_body()
        for w in self.btns.winfo_children():
            w.destroy()
        tk.Label(self.body, text="安装失败", font=(FONT, 13, "bold"),
                 bg=BG, fg="#c0392b").pack(anchor="w", pady=(4, 6))
        tk.Label(self.body, text=tb_text, font=("Consolas", 8), bg=BG,
                 fg=MUTED, wraplength=380, justify="left").pack(anchor="w")
        ttk.Button(self.btns, text="关闭", command=self.root.destroy
                   ).pack(side="right")

    # ---- 逻辑 ----

    def _browse_dir(self):
        initial = os.path.dirname(get_install_dir())
        d = filedialog.askdirectory(initialdir=initial, parent=self.root,
                                    title="选择安装位置")
        if d:
            self.path_var.set(os.path.join(d, "MiniHub"))

    def start_install(self):
        target = self.path_var.get().strip().strip('"')
        if not target:
            messagebox.showwarning("提示", "请填写安装位置", parent=self.root)
            return
        self.install_target = target
        self.install_desktop = self.desktop_var.get()
        for w in self.btns.winfo_children():
            w.configure(state="disabled")
        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self):
        try:
            do_install(progress=self._progress, target=self.install_target,
                       desktop_shortcut=self.install_desktop)
        except Exception:
            tb = traceback.format_exc()
            self.root.after(0, lambda: self.show_error(tb))
            return
        self.root.after(0, self.show_done)

    def _progress(self, done, total, text):
        self.root.after(0, lambda: self._update_bar(done, total, text))

    def _update_bar(self, done, total, text):
        if hasattr(self, "bar"):
            self.bar["maximum"] = max(total, 1)
            self.bar["value"] = done
        if hasattr(self, "status"):
            self.status.config(text=text)

    def finish(self):
        if self.run_var.get():
            subprocess.Popen([os.path.join(self.install_target, EXE_NAME)])
        self.root.destroy()

    def _clear_body(self):
        for w in self.body.winfo_children():
            w.destroy()

    def run(self):
        self.root.mainloop()


def parse_dir(argv):
    for a in argv:
        if a.startswith("--dir="):
            return a[len("--dir="):]
    return None


def main():
    silent = any(a in ("/S", "-S", "--silent") for a in sys.argv[1:])
    if silent:
        try:
            do_install(progress=lambda *a: None, target=parse_dir(sys.argv[1:]))
        except Exception:
            traceback.print_exc()
            sys.exit(1)
        sys.exit(0)
    InstallerApp().run()


if __name__ == "__main__":
    main()
