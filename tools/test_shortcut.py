# 复现 setup_main.py 的 make_shortcut 逻辑，查看真实报错
import base64
import subprocess


def ps_quote(s):
    return "'" + s.replace("'", "''") + "'"


def run_ps(script):
    enc = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-EncodedCommand", enc],
        capture_output=True, timeout=60)


lnk = r"C:\Users\pengb\Desktop\极简媒体中心.lnk"
target = r"C:\Users\pengb\AppData\Local\Programs\MiniHub\MiniHub.exe"
workdir = r"C:\Users\pengb\AppData\Local\Programs\MiniHub"

script = (
    "$ErrorActionPreference='Stop';"
    "$ws=New-Object -ComObject WScript.Shell;"
    f"$s=$ws.CreateShortcut({ps_quote(lnk)});"
    f"$s.TargetPath={ps_quote(target)};"
    f"$s.WorkingDirectory={ps_quote(workdir)};"
    f"$s.IconLocation={ps_quote(target)},0;"
    "$s.Save()")
r = run_ps(script)
print("returncode:", r.returncode)
print("stderr:", r.stderr.decode("gbk", errors="replace"))
print("stdout:", r.stdout.decode("gbk", errors="replace"))
