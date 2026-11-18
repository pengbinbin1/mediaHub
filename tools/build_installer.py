# build_installer.py — 构建 MiniHub 安装包
# 产出: installer\MiniHub_Setup_1.0.0.exe（单文件，可直接分享）
import os
import shutil
import subprocess
import sys
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(BASE, "installer_build")
SRC = os.path.join(BASE, "tools", "installer")
APP_DIR = os.path.join(BASE, "dist", "MiniHub")


def run(cmd):
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main():
    os.makedirs(BUILD, exist_ok=True)
    distpath = BUILD
    workpath = os.path.join(BUILD, "work")

    # 1. 压缩应用文件
    print("1/4 packing app files ...")
    payload = os.path.join(BUILD, "payload.zip")
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # dist\MiniHub 下的相对路径结构保留
        for root, dirs, files in os.walk(APP_DIR):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, APP_DIR)
                zf.write(full, rel)
    print(f"   payload.zip: {os.path.getsize(payload)/1e6:.1f} MB")

    # 2. uninstall.exe
    print("2/4 building uninstall.exe ...")
    run([os.path.join(BASE, ".venv", "Scripts", "pyinstaller.exe"),
         "--noconfirm", "--clean", "--onefile", "--windowed",
         "--distpath", distpath, "--workpath", workpath,
         "--name", "uninstall",
         "--icon", os.path.join(BASE, "app", "resources", "icon.ico"),
         os.path.join(SRC, "uninstall_main.py")])

    # 3. setup.exe（嵌入 payload.zip + uninstall.exe）
    print("3/4 building setup.exe ...")
    run([os.path.join(BASE, ".venv", "Scripts", "pyinstaller.exe"),
         "--noconfirm", "--clean", "--onefile", "--windowed",
         "--distpath", distpath, "--workpath", workpath,
         "--name", "setup",
         "--icon", os.path.join(BASE, "app", "resources", "icon.ico"),
         "--add-data", f"{payload};payload",
         "--add-data", f"{os.path.join(BUILD, 'uninstall.exe')};payload",
         os.path.join(SRC, "setup_main.py")])

    # 4. 重命名
    out = os.path.join(BUILD, "MiniHub_Setup_1.0.0.exe")
    shutil.copy2(os.path.join(BUILD, "setup.exe"), out)
    print(f"4/4 done: {out} ({os.path.getsize(out)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
