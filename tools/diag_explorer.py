# 诊断 QFileSystemModel 根节点行为
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtCore import QDir, QModelIndex, QTimer
from PySide6.QtWidgets import QApplication, QFileSystemModel

app = QApplication(sys.argv)
print("CWD =", os.getcwd())
print("QDir.rootPath =", QDir.rootPath())

m = QFileSystemModel()
m.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
m.setReadOnly(False)
m.setRootPath("")


def dump():
    # 方式 A：index("")
    idx = m.index("")
    print("\n[A] index('')  valid=%s  filePath=%r" % (idx.isValid(), m.filePath(idx) if idx.isValid() else None))
    if idx.isValid():
        n = m.rowCount(idx)
        print("    children=%d" % n)
        for i in range(min(n, 10)):
            c = m.index(i, 0, idx)
            print("     -", m.filePath(c))

    # 方式 B：invisible root 的孩子
    print("\n[B] rowCount(QModelIndex()) =", m.rowCount(QModelIndex()))
    for i in range(min(m.rowCount(QModelIndex()), 5)):
        c = m.index(i, 0, QModelIndex())
        print("     -", m.filePath(c))

    # 方式 C：index(QDir.rootPath())
    idx3 = m.index(QDir.rootPath())
    print("\n[C] index(rootPath) filePath=%r  children=%d" % (m.filePath(idx3), m.rowCount(idx3)))
    for i in range(min(m.rowCount(idx3), 5)):
        c = m.index(i, 0, idx3)
        print("     -", m.filePath(c))
    app.quit()


QTimer.singleShot(1500, dump)
app.exec()
