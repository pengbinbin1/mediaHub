# 最小化 monkey-patch 测试
import sys

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QMenu

app = QApplication(sys.argv)

menu_calls = []


def traced_exec(self, *args):
    actions = [a.text() for a in self.actions() if not a.isSeparator()]
    menu_calls.append(actions)
    return None


QMenu.exec = traced_exec

menu = QMenu()
menu.addAction("测试项1")
menu.addAction("测试项2")

result = menu.exec(QPoint(100, 100))

print("result:", result)
print("menu_calls:", menu_calls)
print("PATCH-WORKS" if menu_calls else "PATCH-FAILED")
