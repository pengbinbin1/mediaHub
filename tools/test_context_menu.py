# 自动化右键菜单测试：验证菜单能弹出且包含 复制/删除 等
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QMenu

from app.main import MainWindow
from app.theme import GLOBAL_QSS

# monkey-patch QMenu.exec 拦截菜单
menu_calls = []
_orig_exec = QMenu.exec


def traced_exec(self, *args):
    actions = [a.text() for a in self.actions() if not a.isSeparator()]
    menu_calls.append(actions)
    return None  # 模拟用户取消


QMenu.exec = traced_exec

app = QApplication(sys.argv)
app.setStyleSheet(GLOBAL_QSS)
win = MainWindow()
win.show()

exp = win.pages["explorer"]

# 等待模型加载盘符
import time

deadline = time.time() + 5
while time.time() < deadline:
    app.processEvents()
    if exp.model.rowCount(exp.tree.rootIndex()) > 0:
        break

# 用 samples 里的真实文件测试
target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples", "笔记.txt")
idx = exp.model.index(os.path.abspath(target))
assert idx.isValid(), "索引无效"

# 选中并在该 item 的可视位置模拟右键
exp.tree.scrollTo(idx)
exp.tree.setCurrentIndex(idx)
app.processEvents()
rect = exp.tree.visualRect(idx)
pos = rect.center()
print("visualRect:", rect.x(), rect.y(), rect.width(), rect.height())
idx_at = exp.tree.indexAt(pos)
print("indexAt valid:", idx_at.isValid(),
      "path:", exp.model.filePath(idx_at) if idx_at.isValid() else "(invalid)")

# 1) 手动调用 context menu 处理函数（拦截 exec 验证菜单构建）
menu_calls.clear()
exp._on_context_menu(pos)
print("菜单项:", menu_calls[0] if menu_calls else "（未弹出）")

# 2) 通过信号触发（完整链路验证）
menu_calls.clear()
exp.tree.customContextMenuRequested.emit(pos)
app.processEvents()
print("信号链路菜单项:", menu_calls[0] if menu_calls else "（未弹出）")

ok = (
    menu_calls
    and "复制" in menu_calls[0]
    and "删除（移到回收站）" in menu_calls[0]
    and "重命名" in menu_calls[0]
)
print("RIGHT-CLICK-MENU-OK" if ok else "RIGHT-CLICK-MENU-FAIL")
sys.exit(0 if ok else 1)
