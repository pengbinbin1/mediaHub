# 复现 uninstall 的延迟删除逻辑
import os
import subprocess
import sys

target = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "MiniHub")

# 先杀掉可能占用文件的进程
subprocess.run(["taskkill", "/IM", "MiniHub.exe", "/F"], capture_output=True)
subprocess.run(["taskkill", "/IM", "uninstall.exe", "/F"], capture_output=True)

cmd = 'ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{}"'.format(target)
print("cmd:", cmd)

p = subprocess.Popen(cmd, shell=True, creationflags=0x08000000)
print("started, pid:", p.pid)

# 等 ping(2s) + rmdir 完成
try:
    rc = p.wait(timeout=30)
    print("cmd exit code:", rc)
except subprocess.TimeoutExpired:
    print("TIMEOUT waiting for cmd")

for i in range(5):
    if not os.path.exists(target):
        print("REMOVED-OK")
        sys.exit(0)
    import time
    time.sleep(1)
print("STILL-THERE")
sys.exit(1)
