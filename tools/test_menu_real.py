# 正确的右键菜单测试：切到 explorer 页，模拟右键，截图验证
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from app.main import MainWindow
from app.theme import GLOBAL_QSS

app = QApplication(sys.argv)
app.setStyleSheet(GLOBAL_QSS)
win = MainWindow()
win.show()

exp = win.pages["explorer"]

# 切换到文件页（让页面可见）
win.switch_page("explorer")

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples", "笔记.txt")
idx = exp.model.index(os.path.abspath(target))
assert idx.isValid()

exp.tree.scrollTo(idx)
exp.tree.setCurrentIndex(idx)
app.processEvents()

rect = exp.tree.visualRect(idx)
pos = rect.center()

# 模拟右键点击
QTest.mouseClick(exp.tree.viewport(), Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, pos)

# 等菜单显示
deadline = time.time() + 3
while time.time() < deadline:
    app.processEvents()

screen = win.grab()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu_screenshot.png")
screen.save(out)
print("screenshot saved:", out)
