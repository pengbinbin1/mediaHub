# -*- coding: utf-8 -*-
"""多标签文档功能自动化测试（offscreen 运行，不弹真实窗口）。

运行：.venv/Scripts/python.exe test_multitab.py
"""
import os
import sys
import tempfile
import shutil

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app.pages.documents as docs_mod
from app.pages.documents import DocumentsPage

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(("PASS" if cond else "FAIL"), "-", name)


class FakeWindow:
    """模拟 MainWindow.set_current_file。"""

    def set_current_file(self, path):
        self.current = path


def schedule_click_button(text, delay=50):
    """在模态对话框 exec() 期间自动点击指定文本的按钮。"""

    def auto_click():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMessageBox):
                for b in w.buttons():
                    if b.text() == text:
                        b.click()
                        return

    QTimer.singleShot(delay, auto_click)


def main():
    app = QApplication(sys.argv)
    router = FakeWindow()
    page = DocumentsPage(router)
    page.resize(1000, 700)
    page.show()

    samples = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    txt = os.path.join(samples, "笔记.txt")
    docx = os.path.join(samples, "示例文档.docx")
    pdf = os.path.join(samples, "示例文档.pdf")

    # ---- 1. 同时打开 3 个不同类型文档 → 3 个页签 ----
    page.load(txt)
    page.load(docx)
    page.load(pdf)
    check("打开 3 个文档后标签数为 3", page.tab_widget.count() == 3)
    check("文档页容器切换到标签视图", page.holder.currentIndex() == 0)
    kinds = {page.tab_widget.widget(i).doc_kind for i in range(3)}
    check("三个标签类型分别为 txt/docx/pdf", kinds == {"txt", "docx", "pdf"})

    # ---- 2. 重复打开同一文件 → 不新增标签，而是切换过去 ----
    page.load(txt)
    check("重复打开同一文件不新增标签", page.tab_widget.count() == 3)
    cur = page.current_tab()
    check("重复打开后当前标签切换到该文件",
          cur is not None and os.path.abspath(cur.file_path) == os.path.abspath(txt))

    # ---- 3. 修改当前编辑器 → 标签标题带 ●，save() 落盘 ----
    # 注意：setPlainText 会把 modified 重置为 False（Qt 行为），
    # 所以这里用 append 模拟真实用户输入。
    cur.editor.append("hello world 多标签测试")
    tab_text = page.tab_widget.tabText(page.tab_widget.currentIndex())
    check("修改后标签标题带 ●", tab_text.endswith("●"))
    page.save()
    check("保存后 is_modified 为 False", not cur.is_modified())
    with open(txt, encoding="utf-8") as f:
        content = f.read()
    check("保存内容正确写入文件", "hello world 多标签测试" in content)

    # ---- 4. 切到 PDF 标签 → 页码/缩放状态栏刷新（parentWidget bug 修复验证） ----
    for i in range(page.tab_widget.count()):
        t = page.tab_widget.widget(i)
        if t.doc_kind == "pdf":
            page.tab_widget.setCurrentIndex(i)
            break
    pdf_tab = page.current_tab()
    check("PDF 页码状态栏已更新", page.page_label.text().strip() != "")
    check("PDF 缩放状态栏已更新", page.zoom_label.text().strip() != "")
    print("      page_label =", repr(page.page_label.text()),
          " zoom_label =", repr(page.zoom_label.text()))

    # ---- 5. PDF 翻页 → 页码变化 ----
    before = page.page_label.text()
    pdf_tab.pdf_turn(1)
    check("PDF 翻页后页码刷新", page.page_label.text() != before)

    # ---- 6. 关闭未修改的 PDF 标签（走 tabCloseRequested 路径） ----
    page._close_tab(page.tab_widget.currentIndex())
    check("关闭 PDF 标签后剩余 2 个标签", page.tab_widget.count() == 2)
    cur_after = page.current_tab()
    check("关闭后自动切到相邻标签", cur_after is not None)

    # ---- 7. 关闭非当前标签：保存的必须是【被关闭】的标签（核心 bug 回归测试） ----
    tmpdir = tempfile.mkdtemp()
    try:
        txt_a = os.path.join(tmpdir, "草稿A.txt")
        txt_b = os.path.join(tmpdir, "草稿B.txt")
        for p, init in ((txt_a, "A-初始内容"), (txt_b, "B-初始内容")):
            with open(p, "w", encoding="utf-8") as f:
                f.write(init)

        page.load(txt_a)
        page.load(txt_b)   # 当前标签 = B
        check("再打开 2 个文档后标签数为 4", page.tab_widget.count() == 4)

        # 找到 A 标签的索引并修改 A 的内容
        idx_a = -1
        for i in range(page.tab_widget.count()):
            if os.path.abspath(page.tab_widget.widget(i).file_path) == os.path.abspath(txt_a):
                idx_a = i
                break
        page.tab_widget.widget(idx_a).editor.append("A-改过的内容")
        check("标签 A 修改后 is_modified 为 True",
              page.tab_widget.widget(idx_a).is_modified())

        # 关闭 A（非当前标签）→ 弹窗 → 自动点“保存”
        schedule_click_button("保存")
        page._close_tab(idx_a)
        check("关闭标签 A 后标签数减一", page.tab_widget.count() == 3)

        with open(txt_a, encoding="utf-8") as f:
            a_content = f.read()
        check("保存的是被关闭的标签 A（内容已写入）",
              a_content == "A-初始内容\nA-改过的内容")

        # 当前标签 B 的文件内容不应被误写
        with open(txt_b, encoding="utf-8") as f:
            b_content = f.read()
        check("当前标签 B 的文件未被误写", b_content == "B-初始内容")

        # ---- 8. 关闭有修改的标签时点“不保存” → 直接关闭且不落盘 ----
        txt_c = os.path.join(tmpdir, "草稿C.txt")
        with open(txt_c, "w", encoding="utf-8") as f:
            f.write("C-初始内容")
        page.load(txt_c)
        cur_c = page.current_tab()
        cur_c.editor.append("C-改过的内容")
        schedule_click_button("不保存")
        page._close_tab(page.tab_widget.currentIndex())
        check("点“不保存”后标签已关闭", page.tab_widget.count() == 3)
        with open(txt_c, encoding="utf-8") as f:
            check("不保存时文件未被写入", f.read() == "C-初始内容")

        # ---- 9. 关闭全部标签后回到空状态 ----
        while page.tab_widget.count() > 0:
            # 剩余标签均未修改，直接关
            page._close_tab(0)
        check("全部关闭后回到空状态提示", page.holder.currentIndex() == 1)
        check("全部关闭后路径标签复位", page.path_label.text() == "未打开文件")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print()
    print(f"结果：{len(PASS)} 通过，{len(FAIL)} 失败")
    if FAIL:
        for f in FAIL:
            print("  FAIL:", f)
        sys.exit(1)


def test_drag_drop():
    """模拟拖放：一次拖多个文件 + 已打开页签后继续拖入。"""
    from PySide6.QtCore import QMimeData, QPointF, QUrl, Qt
    from PySide6.QtGui import QDropEvent
    from app.main import MainWindow

    win = MainWindow()
    win.resize(1100, 750)
    docs = win.pages["docs"]

    samples = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    txt = os.path.join(samples, "笔记.txt")
    docx = os.path.join(samples, "示例文档.docx")
    pdf = os.path.join(samples, "示例文档.pdf")

    def drop(paths):
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
        ev = QDropEvent(QPointF(50, 300), Qt.CopyAction, mime,
                        Qt.NoButton, Qt.NoModifier)
        # 直接调用 dropEvent（PySide6 的 sendEvent 无法投递 QDropEvent）
        win.dropEvent(ev)

    # ---- 1. 一次拖入 3 个文件 → 3 个页签 ----
    drop([txt, docx, pdf])
    check("一次拖入 3 个文件后标签数为 3", docs.tab_widget.count() == 3)

    # ---- 2. 已打开页签后继续拖入 1 个 txt → 第 4 个页签 ----
    tmpdir = tempfile.mkdtemp()
    try:
        txt2 = os.path.join(tmpdir, "第二个.txt")
        with open(txt2, "w", encoding="utf-8") as f:
            f.write("后续拖入的文件")
        drop([txt2])
        check("已有页签时再拖入 1 个文件 → 新页签", docs.tab_widget.count() == 4)
        cur = docs.current_tab()
        check("拖入后当前页签为该文件",
              cur is not None and os.path.abspath(cur.file_path) == os.path.abspath(txt2))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ---- 3. 重复拖入已打开的文件 → 切换到已有页签，不新增 ----
    drop([pdf])
    check("重复拖入已打开文件不新增页签", docs.tab_widget.count() == 4)

    # ---- 4. 所有动态标签内部控件均不拦截拖放 ----
    for i in range(docs.tab_widget.count()):
        t = docs.tab_widget.widget(i)
        check(f"标签 {i} 编辑器 viewport 不拦截拖放",
              not t.editor.viewport().acceptDrops())
        check(f"标签 {i} PDF 滚动区 viewport 不拦截拖放",
              not t.pdf_scroll.viewport().acceptDrops())


if __name__ == "__main__":
    main()
    print()
    print("==== 拖放场景测试 ====")
    test_drag_drop()
