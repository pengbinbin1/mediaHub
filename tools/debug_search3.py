# 隔离调试：搜索功能是否触发、结果是否有
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtWidgets import QApplication

from app.main import MainWindow

app = QApplication(sys.argv)
win = MainWindow()
win.show()

exp = win.pages["explorer"]

print("=== 1. 直接调用 _start_search ===")
exp.search_box.setText("演示")
exp._start_search()  # 绕过防抖直接搜

print("worker:", exp._worker)
print("worker running:", exp._worker.isRunning() if exp._worker else None)

deadline = time.time() + 20
found = 0
while time.time() < deadline:
    app.processEvents()
    time.sleep(0.2)
    n = exp.search_view.topLevelItemCount()
    if n > 0:
        found = n
        break
    if exp._worker and not exp._worker.isRunning():
        # 搜索结束
        found = len(exp._worker.results)
        break

print("search_view items:", exp.search_view.topLevelItemCount())
print("worker results:", len(exp._worker.results) if exp._worker else 0)
print("worker still running:", exp._worker.isRunning() if exp._worker else None)
