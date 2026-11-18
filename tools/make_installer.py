# make_installer.py — 生成 Inno Setup 脚本并构建 MiniHub 安装包
# 用法: .venv/Scripts/python.exe tools/make_installer.py
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISCC = os.path.join(BASE, "tools", "innosetup", "iscc.exe")
ISS_PATH = os.path.join(BASE, "installer.iss")
OUT_DIR = os.path.join(BASE, "installer")

TEMPLATE = r"""; 极简媒体中心 Inno Setup 安装脚本 — 由 tools/make_installer.py 生成
#define MyAppName "极简媒体中心"
#define MyAppVersion "1.0.0"
#define MyAppExeName "MiniHub.exe"

[Setup]
AppId={{8C1F2A6D-0E3B-4D18-9E5B-B4D6F9E2A7C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=MiniHub
DefaultDirName={autopf}\MiniHub
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=MiniHub_Setup_1.0.0
SetupIconFile=app\resources\icon.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\MiniHub.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
MinVersion=10.0

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\MiniHub\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
"""


def main():
    # 1. 写 .iss（UTF-8 BOM + CRLF，Inno Setup 6 才能正确读中文）
    with open(ISS_PATH, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write(TEMPLATE)

    if not os.path.exists(ISCC):
        print("ERROR: iscc.exe not found at", ISCC)
        sys.exit(1)

    # 2. 构建
    ret = subprocess.run([ISCC, ISS_PATH]).returncode
    if ret != 0:
        sys.exit(ret)

    # 3. 结果
    exe = os.path.join(OUT_DIR, "MiniHub_Setup_1.0.0.exe")
    if os.path.exists(exe):
        size_mb = os.path.getsize(exe) / 1024 / 1024
        print(f"INSTALLER-OK: {exe} ({size_mb:.1f} MB)")
    else:
        print("ERROR: installer not created")
        sys.exit(1)


if __name__ == "__main__":
    main()
