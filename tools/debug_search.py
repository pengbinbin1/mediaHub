# 调试搜索功能
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from app.pages.explorer import SearchWorker, _get_drives

app = QApplication(sys.argv)

print("drives:", _get_drives())

received = []


def on_batch(paths):
    received.extend(paths)
    print(f"  batch: {len(paths)}, total {len(received)}, last={paths[-1] if paths else None}")


def on_finished(count):
    print(f"  finished: {count} results")


worker = SearchWorker("演示")
worker.batch_ready.connect(on_batch)
worker.finished_search.connect(on_finished)
worker.start()

start = time.time()
while worker.isRunning() and time.time() - start < 60:
    app.processEvents()
    time.sleep(0.05)

elapsed = time.time() - start
print(f"elapsed: {elapsed:.1f}s, received: {len(received)}")
