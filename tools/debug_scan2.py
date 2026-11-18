# 测试 SearchWorker._scan 直接调用
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtWidgets import QApplication

from app.pages.explorer import SearchWorker

app = QApplication(sys.argv)

worker = SearchWorker("演示")
print("keyword:", repr(worker.keyword))
worker._scan("D:\\")
print("results:", worker._results)
print("pending:", worker._pending)
