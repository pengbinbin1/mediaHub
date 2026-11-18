# 查看实际运行的 _on_context_menu 源码
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.main import MainWindow
from app.pages import explorer as exp_mod
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
win = MainWindow()
exp = win.pages["explorer"]

print("=== _on_context_menu 源码 ===")
print(inspect.getsource(exp._on_context_menu))
