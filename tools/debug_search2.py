# 调试 SearchWorker：加 print 看信号是否发出
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtWidgets import QApplication

from app.pages.explorer import SearchWorker


def on_batch(paths):
    print(f"BATCH: {len(paths)}")


def on_finished(count):
    print(f"FINISHED: {count}")


app = QApplication(sys.argv)

worker = SearchWorker("演示")
worker.batch_ready.connect(on_batch)
worker.finished_search.connect(on_finished)

# monkey-patch run 加打印
orig_run = worker.run


def traced_run():
    print("run() entered")
    orig_run()
    print("run() exited")


worker.run = traced_run
worker.start()

start = time.time()
while worker.isRunning() and time.time() - start < 60:
    app.processEvents()
    time.sleep(0.05)

print(f"elapsed {time.time() - start:.1f}s")
