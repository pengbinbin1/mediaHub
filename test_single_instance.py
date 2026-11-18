# -*- coding: utf-8 -*-
"""单实例行为测试：第二个进程应快速退出，不创建新窗口。

运行：.venv/Scripts/python.exe test_single_instance.py
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
RUN = os.path.join(ROOT, "run.py")


def main():
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")

    # 启动第一个实例
    p1 = subprocess.Popen([PY, RUN], env=env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # 等第一个实例的本地服务器就绪（Qt 冷启动约 2-5 秒）
        time.sleep(8)
        if p1.poll() is not None:
            sys.exit(f"第一个实例意外退出 (code={p1.returncode})")

        # 启动第二个实例，应当把请求转发给第一个实例后退出
        t0 = time.time()
        p2 = subprocess.Popen([PY, RUN], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            rc = p2.wait(timeout=25)
        except subprocess.TimeoutExpired:
            p2.kill()
            print("FAIL - 第二个实例未退出（单实例逻辑未生效）")
            sys.exit(1)
        dt = time.time() - t0
        print(f"第二个实例退出码: {rc}，耗时 {dt:.1f}s")

        # 第一个实例应仍在运行（收到唤醒请求而不崩溃）
        time.sleep(1)
        alive = p1.poll() is None
        print(f"第一个实例仍在运行: {alive}")

        ok = (rc == 0) and alive
        print("PASS" if ok else "FAIL", "- 单实例行为")
        if not ok:
            sys.exit(1)
    finally:
        p1.terminate()
        try:
            p1.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p1.kill()


if __name__ == "__main__":
    main()
