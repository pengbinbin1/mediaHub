# 验证安装器/卸载器是否正确执行（通过检查其副作用）
import os
import sys
import winreg

INSTALL_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "MiniHub")
UNINSTALL_REG = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MiniHub"


def check_desktop_shortcut():
    import ctypes
    from ctypes import wintypes

    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf) != 0:
        return None
    lnk = os.path.join(buf.value, "极简媒体中心.lnk")
    return lnk if os.path.exists(lnk) else None


def check_startmenu_shortcut():
    lnk = os.path.join(os.environ["APPDATA"],
                       "Microsoft", "Windows", "Start Menu", "Programs",
                       "极简媒体中心.lnk")
    return lnk if os.path.exists(lnk) else None


def check_registry():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG) as k:
            name = winreg.QueryValueEx(k, "DisplayName")[0]
            ver = winreg.QueryValueEx(k, "DisplayVersion")[0]
            uninstall = winreg.QueryValueEx(k, "UninstallString")[0]
            return f"DisplayName={name}, Version={ver}, Uninstall={uninstall}"
    except OSError:
        return None


def check_installed_files():
    exe = os.path.join(INSTALL_DIR, "MiniHub.exe")
    uni = os.path.join(INSTALL_DIR, "uninstall.exe")
    internal = os.path.join(INSTALL_DIR, "_internal")
    parts = []
    parts.append(f"MiniHub.exe={'yes' if os.path.exists(exe) else 'NO'}")
    parts.append(f"uninstall.exe={'yes' if os.path.exists(uni) else 'NO'}")
    parts.append(f"_internal={'yes' if os.path.isdir(internal) else 'NO'}")
    if os.path.exists(exe):
        parts.append(f"size={os.path.getsize(exe)}")
    return ", ".join(parts)


def check_all():
    print("=" * 50)
    print("install_dir:", INSTALL_DIR)
    print("  exists:", os.path.isdir(INSTALL_DIR))
    print("  files:", check_installed_files())
    print("  desktop_shortcut:", check_desktop_shortcut())
    print("  startmenu_shortcut:", check_startmenu_shortcut())
    reg = check_registry()
    print("  registry:", reg if reg else "NOT FOUND")


if __name__ == "__main__":
    check_all()
