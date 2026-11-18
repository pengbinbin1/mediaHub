# 极简媒体中心 — 启动入口（源码运行：python run.py）
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    main()
