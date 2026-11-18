# -*- coding: utf-8 -*-
"""生成应用真实截图（offscreen 渲染，用于 README）。

用法：.venv/Scripts/python.exe tools/take_screenshot.py
产出：tools/app_screenshot.png
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtWidgets import QApplication

from app.main import MainWindow


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1280, 800)
    win.show()
    app.processEvents()

    # 打开三个不同类型的文档，展示多标签页
    samples = os.path.join(ROOT, "samples")
    docs = win.pages["docs"]
    docs.load(os.path.join(samples, "笔记.txt"))
    docs.load(os.path.join(samples, "示例文档.docx"))
    docs.load(os.path.join(samples, "示例文档.pdf"))
    win.switch_page("docs")
    app.processEvents()

    pix = win.grab()
    out = os.path.join(ROOT, "tools", "app_screenshot.png")
    ok = pix.save(out)
    print("saved" if ok else "save failed:", out, f"({pix.width()}x{pix.height()})")
    win.close()


if __name__ == "__main__":
    main()
