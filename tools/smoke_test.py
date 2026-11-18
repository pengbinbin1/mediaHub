# 回归冒烟测试：文件树 + 搜索 + 文件操作 + 文档多标签
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from app.main import MainWindow
from app.theme import GLOBAL_QSS

S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples")

result = {"ok": [], "fail": []}

app = QApplication(sys.argv)
app.setStyleSheet(GLOBAL_QSS)
win = MainWindow()
win.show()

exp = win.pages["explorer"]
docs = win.pages["docs"]


def check_drives():
    """树的顶层行必须是所有盘符（C:/ D:/ E:/...）"""
    m = exp.model
    n = m.rowCount(exp.tree.rootIndex())
    assert n >= 2, f"盘符数量异常: {n}"


def test_search():
    """搜索功能：搜索 samples 目录下存在的文件名"""
    import time

    exp.search_box.setText("演示")
    # 等待防抖 + 搜索线程 + 轮询（全盘并行扫描，最多 30 秒）
    deadline = time.time() + 30
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.1)
        if exp.search_view.topLevelItemCount() > 0:
            break
    count = exp.search_view.topLevelItemCount()
    assert count > 0, "搜索无结果"
    # 验证结果包含路径
    item = exp.search_view.topLevelItem(0)
    path = item.data(0, 0x0100)  # Qt.UserRole
    assert path, "结果无路径数据"
    print(f"  搜索「演示」找到 {count} 个结果")


def test_search_clear():
    """清空搜索框回到文件浏览"""
    exp.search_box.setText("")
    for _ in range(20):
        app.processEvents()
        import time
        time.sleep(0.05)
    # 验证视图切换回文件树
    assert exp.view_stack.currentWidget() == exp.tree, "未切回文件树视图"


def test_recycle_bin_delete():
    """测试删除到回收站（创建临时文件后删除）"""
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "minihub_test_delete.txt")
    with open(tmp, "w") as f:
        f.write("test")
    from app.pages.explorer import send_to_recycle_bin
    ok = send_to_recycle_bin(tmp)
    assert ok, "删除到回收站失败"
    # 文件应该被移走（进入回收站）
    assert not os.path.exists(tmp), "文件未被删除"


def test_show_in_explorer():
    """测试在资源管理器中显示（仅验证不抛异常）"""
    exp._show_in_explorer(os.path.join(S, "笔记.txt"))


def test_docs_multitab():
    """文档页多标签：打开 3 个不同类型文件 → 3 个标签"""
    # 切换到文档页（让页面可见，否则 isVisible 全为 False）
    win.switch_page("docs")
    docs.load(os.path.join(S, "笔记.txt"))
    docs.load(os.path.join(S, "示例文档.docx"))
    docs.load(os.path.join(S, "示例文档.pdf"))
    for _ in range(10):
        app.processEvents()
    n = docs.tab_widget.count()
    assert n == 3, f"标签数量错误: {n} (期望 3)"
    # 当前标签应为 pdf（最后打开）
    tab = docs.current_tab()
    assert tab.doc_kind == "pdf", f"当前标签类型错误: {tab.doc_kind}"
    # 每个标签独立持有状态
    kinds = [docs.tab_widget.widget(i).doc_kind for i in range(3)]
    assert kinds == ["txt", "docx", "pdf"], f"标签类型错误: {kinds}"
    print("  3 种类型文件 (txt/docx/pdf) 已同时打开为 3 个标签")


def test_docs_tab_switch():
    """切换标签：窗口标题、工具栏状态跟随"""
    # 切到 txt 标签（索引 0）
    docs.tab_widget.setCurrentIndex(0)
    for _ in range(10):
        app.processEvents()
    assert docs.current_tab().doc_kind == "txt"
    assert docs.btn_save.isVisible(), "保存按钮在编辑模式未显示"
    assert not docs.btn_prev_page.isVisible(), "PDF 导航组在编辑模式不应显示"
    assert "笔记" in win.windowTitle(), f"窗口标题未同步: {win.windowTitle()}"
    # 切到 docx 标签（索引 1）
    docs.tab_widget.setCurrentIndex(1)
    for _ in range(10):
        app.processEvents()
    assert docs.current_tab().doc_kind == "docx"
    assert "示例文档" in win.windowTitle(), f"窗口标题未同步: {win.windowTitle()}"
    print("  标签切换正常：标题/工具栏状态同步")


def test_docs_modified_indicator():
    """修改编辑器内容 → 标签标题出现 ●"""
    docs.tab_widget.setCurrentIndex(0)  # txt 标签
    for _ in range(10):
        app.processEvents()
    tab = docs.current_tab()
    original = tab.editor.toPlainText()
    # 用 append 触发真实修改（setPlainText 会重置 modified 状态）
    tab.editor.append("测试修改行")
    for _ in range(10):
        app.processEvents()
    title = docs.tab_widget.tabText(0)
    assert "●" in title, f"标签标题未显示修改标记: {title}"
    # 保存后 ● 消失
    docs.save()
    for _ in range(10):
        app.processEvents()
    title = docs.tab_widget.tabText(0)
    assert "●" not in title, f"保存后标签标题仍有修改标记: {title}"
    # 恢复原始内容
    tab.editor.setPlainText(original)
    docs.save()
    for _ in range(10):
        app.processEvents()
    print("  修改标记（●）在编辑/保存后正确显示/消失")


def test_docs_reopen_same_file():
    """重新打开已打开的文件：不新增标签，切换过去"""
    docs.load(os.path.join(S, "笔记.txt"))
    for _ in range(10):
        app.processEvents()
    n = docs.tab_widget.count()
    assert n == 3, f"重复打开同一文件不应新增标签: {n}"
    assert docs.current_tab().doc_kind == "txt", "应切换到已有标签"
    print("  重复打开同一文件正确切换到已有标签（不新增）")


def test_docs_close_tabs():
    """关闭标签：逐个关闭 → 数量递减；关闭最后一个 → 空状态"""
    # 当前是 txt 标签（索引 0），无未保存修改
    docs._close_tab(0)
    for _ in range(10):
        app.processEvents()
    assert docs.tab_widget.count() == 2, "关闭标签后数量错误"
    # 切到 docx 并关闭
    docs.tab_widget.setCurrentIndex(0)  # docx 现在是索引 0
    for _ in range(10):
        app.processEvents()
    docs._close_tab(0)
    for _ in range(10):
        app.processEvents()
    assert docs.tab_widget.count() == 1, "关闭标签后数量错误"
    # 关闭最后一个（pdf）
    docs._close_tab(0)
    for _ in range(10):
        app.processEvents()
    assert docs.tab_widget.count() == 0, "关闭最后一个标签后数量错误"
    # 关闭最后一个标签后应显示空状态
    assert docs.holder.currentIndex() == 1, "关闭所有标签后未显示空状态"
    assert not docs.btn_save.isVisible(), "空状态下不应显示保存按钮"
    assert not docs.btn_prev_page.isVisible(), "空状态下不应显示 PDF 导航"
    assert docs.path_label.text() == "未打开文件", f"路径标签未重置: {docs.path_label.text()}"
    print("  标签关闭流程正常：逐个关闭 → 空状态")


steps = [
    ("explorer-drives", check_drives),
    ("search-test", test_search),
    ("search-clear", test_search_clear),
    ("recycle-bin-delete", test_recycle_bin_delete),
    ("show-in-explorer", test_show_in_explorer),
    ("docs-multitab", test_docs_multitab),
    ("docs-tab-switch", test_docs_tab_switch),
    ("docs-modified-indicator", test_docs_modified_indicator),
    ("docs-reopen-same-file", test_docs_reopen_same_file),
    ("docs-close-tabs", test_docs_close_tabs),
]

queue = list(steps)


def run_next():
    if not queue:
        print("SMOKE-RESULT:", "ALL-OK" if not result["fail"] else f"FAIL={result['fail']}")
        app.quit()
        return
    name, fn = queue.pop(0)
    try:
        fn()
        result["ok"].append(name)
        print(f"[OK] {name}")
    except Exception:
        result["fail"].append(name)
        print(f"[FAIL] {name}")
        traceback.print_exc()
    QTimer.singleShot(300, run_next)


QTimer.singleShot(600, run_next)
QTimer.singleShot(60000, app.quit)  # 兜底退出
app.exec()
sys.exit(0 if not result["fail"] else 1)
