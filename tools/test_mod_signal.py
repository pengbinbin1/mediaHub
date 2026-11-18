# 隔离测试：setPlainText 是否触发 modificationChanged
import sys

from PySide6.QtWidgets import QApplication, QTextEdit

app = QApplication(sys.argv)
edit = QTextEdit()
edit.setPlainText("original")
fired = []
edit.document().modificationChanged.connect(lambda m: fired.append(m))

edit.setPlainText("modified")
print("setPlainText fired:", fired, "isModified:", edit.document().isModified())

fired.clear()
edit.append("more")
print("append fired:", fired, "isModified:", edit.document().isModified())

edit.document().setModified(False)
fired.clear()
cursor = edit.textCursor()
cursor.movePosition(cursor.End)
cursor.insertText("X")
print("cursor fired:", fired, "isModified:", edit.document().isModified())
