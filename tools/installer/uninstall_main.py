# uninstall_main.py — 极简媒体中心 卸载器（双阶段设计）
#
# 阶段 1（安装目录里的 uninstall.exe）：
#   UI 确认（非静默时）→ 复制自身到 %TEMP% → 启动 TEMP 副本 → 原进程退出
# 阶段 2（%TEMP% 里的副本）：
#   删快捷方式 → 删注册表 → 删安装目录（此时无文件锁定）→ 自删 TEMP 副本
#
# 静默卸载：uninstall.exe /S
import os
import shutil
import subprocess
import sys
import time
import winreg

APP_NAME = "极简媒体中心"
EXE_NAME = "MiniHub.exe"
UNINSTALL_REG = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MiniHub"


def get_install_dir():
    """从注册表读取实际安装路径；读不到时回退到默认路径。"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG) as k:
            loc = winreg.QueryValueEx(k, "InstallLocation")[0]
            if loc and os.path.isdir(loc):
                return loc
    except OSError:
        pass
    return os.path.join(os.environ["LOCALAPPDATA"], "Programs", "MiniHub")


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


def remove_shortcuts():
    lnk = APP_NAME + ".lnk"
    for d in (get_desktop_dir(), get_startmenu_dir()):
        try:
            os.remove(os.path.join(d, lnk))
        except OSError:
            pass


def remove_registry():
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG)
    except OSError:
        pass


def remove_install_dir(install_dir):
    # 关闭正在运行的应用（升级/卸载场景）
    subprocess.run(["taskkill", "/IM", EXE_NAME, "/F"], capture_output=True)
    target = install_dir  # 用启动时缓存的路径（此时注册表可能已删）
    # MiniHub.exe 退出释放句柄需要一点时间，循环重试
    for _ in range(20):
        try:
            shutil.rmtree(target)
            return True
        except OSError:
            if not os.path.exists(target):
                return True
            time.sleep(0.5)
    return not os.path.exists(target)


def do_uninstall(install_dir):
    remove_shortcuts()
    remove_registry()
    return remove_install_dir(install_dir)


def ask_confirm():
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    return messagebox.askyesno(
        "卸载确认",
        f"确定要卸载 {APP_NAME} 吗？\n\n安装目录及快捷方式将被删除。")


def show_done():
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("卸载完成", f"{APP_NAME} 已成功卸载。")


def self_delete(tmp_exe):
    # TEMP 副本自删：等本进程退出后由 cmd 删除
    cmd = 'ping 127.0.0.1 -n 2 > nul & del "{}"'.format(tmp_exe)
    subprocess.Popen(cmd, shell=True, creationflags=0x08000000)


def main():
    me = os.path.abspath(sys.argv[0])
    install_dir = get_install_dir()
    in_install = (os.path.normcase(os.path.dirname(me))
                  == os.path.normcase(install_dir))

    if in_install:
        # ---- 阶段 1：确认 → 复制到 TEMP → 启动副本 ----
        silent = any(a in ("/S", "-S", "--silent") for a in sys.argv[1:])
        if not silent and not ask_confirm():
            return
        tmp_exe = os.path.join(os.environ["TEMP"],
                               "uninstall_%d.exe" % os.getpid())
        try:
            shutil.copy2(me, tmp_exe)
            # 关键：把 --silent / --ui 等参数透传给 TEMP 副本
            subprocess.Popen([tmp_exe] + sys.argv[1:],
                             creationflags=0x08000000)
            return  # 原进程立即退出，TEMP 副本接管剩余工作
        except OSError:
            pass  # 复制失败 → 直接在本进程卸载（可能残留 uninstall.exe 自身）
        ui_mode = not silent
        ok = do_uninstall(install_dir)
        if ui_mode and ok:
            show_done()
        sys.exit(0 if ok else 1)

    # ---- 阶段 2：TEMP 副本执行卸载并自删 ----
    ui_mode = "--ui" in sys.argv[1:]
    silent = any(a in ("/S", "-S", "--silent") for a in sys.argv[1:])
    ok = do_uninstall(install_dir)
    if (ui_mode or not silent) and ok:
        show_done()
    self_delete(me)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
