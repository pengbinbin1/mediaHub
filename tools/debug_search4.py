# 隔离调试：防抖计时器在冒烟测试环境下是否触发
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

fired = []
orig_start = exp._start_search
exp._start_search = lambda *a, **k: (fired.append(time.time()), orig_start())[1]

exp.search_box.setText("演示")
t0 = time.time()

deadline = t0 + 10
while time.time() < deadline:
    app.processEvents()
    time.sleep(0.1)
    if fired:
        break

elapsed = fired[0] - t0 if fired else None
print(f"debounce fired: {bool(fired)}  after {elapsed}s" if fired
      else "debounce NOT fired in 10s")

n = exp.search_view.topLevelItemCount()
w = exp._worker
res = len(w.results) if w else 0
print(f"search_view items: {n}  worker results: {res}")
