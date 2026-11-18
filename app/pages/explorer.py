# explorer.py — 文件浏览器：全盘符树 + 右键文件操作 + 全盘关键字搜索
import ctypes
import os
import subprocess
import threading
from ctypes import wintypes

from PySide6.QtCore import (
    QMimeData, QThread, QTimer, QUrl, QDir, QModelIndex, Qt, Signal,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QFileSystemModel, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMenu, QPushButton, QStackedWidget, QTreeWidget,
    QTreeWidgetItem, QTreeView, QVBoxLayout, QWidget,
)

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".flv", ".wmv", ".ts", ".m4v"}
DOC_EXTS = {".txt", ".md", ".docx", ".pdf"}


# ================= Windows API =================

def _get_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drives.append(chr(ord("A") + i) + ":\\")
    return drives


def send_to_recycle_bin(path: str) -> bool:
    """把文件/目录移入回收站（可在回收站恢复）"""

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", ctypes.c_uint),
            ("pFrom", ctypes.c_wchar_p),
            ("pTo", ctypes.c_wchar_p),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", ctypes.c_wchar_p),
        ]

    # pFrom 需 double-null 结尾
    src = path + "\0"
    op = SHFILEOPSTRUCTW()
    op.hwnd = None
    op.wFunc = 3  # FO_DELETE
    op.pFrom = src
    op.pTo = None
    op.fFlags = 0x40 | 0x10 | 0x4  # ALLOWUNDO | NOCONFIRMATION | SILENT
    ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    return ret == 0


# ================= 搜索线程 =================

class SearchWorker(QThread):
    """后台全盘搜索：每个盘符一个线程并行扫描，跳过无权限目录。
    结果存 self.results，由主线程 QTimer 轮询读取。"""

    def __init__(self, keyword, parent=None):
        super().__init__(parent)
        self.keyword = keyword.lower().strip()
        self._stop = False
        self.results = []
        self._lock = threading.Lock()

    def stop(self):
        self._stop = True

    def run(self):
        if not self.keyword:
            return
        threads = []
        for drive in _get_drives():
            t = threading.Thread(target=self._scan, args=(drive,), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def _scan(self, path):
        if self._stop:
            return
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self._stop:
                        return
                    try:
                        name = entry.name
                        if self.keyword in name.lower():
                            with self._lock:
                                self.results.append(entry.path)
                        if entry.is_dir(follow_symlinks=False):
                            self._scan(entry.path)
                    except OSError:
                        continue
        except OSError:
            pass  # 无权限目录跳过


# ================= 页面 =================

class ExplorerPage(QWidget):
    def __init__(self, router, parent=None):
        super().__init__(parent)
        self.router = router  # MainWindow，提供 open_file(path)

        # ---- 文件系统模型 ----
        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.model.setReadOnly(False)
        self.model.setRootPath("")  # 监控整个文件系统

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        # 根设为模型不可见根：顶层直接列出所有盘符（此电脑）
        self.tree.setRootIndex(QModelIndex())
        self.tree.setColumnWidth(0, 420)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setStretchLastSection(True)
        self.tree.setAnimated(True)
        self.tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

        # ---- 搜索结果表 ----
        self.search_view = QTreeWidget()
        self.search_view.setColumnCount(4)
        self.search_view.setHeaderLabels(["名称", "路径", "大小", "类型"])
        self.search_view.setColumnWidth(0, 220)
        self.search_view.setColumnWidth(1, 420)
        self.search_view.header().setStretchLastSection(True)
        self.search_view.setRootIsDecorated(False)
        self.search_view.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.search_view.doubleClicked.connect(self._on_search_result_activated)
        self.search_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.search_view.customContextMenuRequested.connect(self._on_search_context_menu)

        # ---- 顶部：路径栏 + 搜索栏 ----
        top = QHBoxLayout()
        self.btn_up = QPushButton("↑ 上一级")
        self.btn_up.clicked.connect(self._go_up)
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self._refresh)
        self.path_box = QLineEdit(objectName="PathBox")
        self.path_box.setReadOnly(True)
        self.path_box.setText("此电脑")
        for b in (self.btn_up, self.btn_refresh):
            b.setFocusPolicy(Qt.NoFocus)
        top.addWidget(self.btn_up)
        top.addWidget(self.btn_refresh)
        top.addWidget(self.path_box, 1)

        search_bar = QHBoxLayout()
        self.search_box = QLineEdit(objectName="PathBox")
        self.search_box.setPlaceholderText("搜索全盘文件（输入关键字，实时搜索）…")
        self.search_box.setClearButtonEnabled(True)
        self.btn_search_stop = QPushButton("停止")
        self.btn_search_stop.clicked.connect(self._stop_search)
        for b in (self.btn_search_stop,):
            b.setFocusPolicy(Qt.NoFocus)
        search_bar.addWidget(self.search_box, 1)
        search_bar.addWidget(self.btn_search_stop)

        self.search_status = QLabel("", objectName="Hint")
        self.search_status.hide()

        # ---- 视图切换：文件树 / 搜索结果 ----
        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.tree)
        self.view_stack.addWidget(self.search_view)

        self.hint = QLabel("双击视频/图片/文档直接在本应用打开；其他文件调用系统程序", objectName="Hint")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 20)
        root.setSpacing(10)
        root.addLayout(top)
        root.addLayout(search_bar)
        root.addWidget(self.search_status)
        root.addWidget(self.view_stack, 1)
        root.addWidget(self.hint)

        # ---- 搜索状态 ----
        self._worker = None
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(400)
        self._debounce.timeout.connect(self._start_search)
        self.search_box.textChanged.connect(lambda _: self._debounce.start())

    # ================= 文件树导航 =================

    def _on_double_click(self, index: QModelIndex):
        if not index.isValid():
            return
        path = self.model.filePath(index)
        self.path_box.setText(path)
        if self.model.isDir(index):
            return  # 目录交给树默认展开行为
        self.router.open_file(path)

    def _go_up(self):
        idx = self.tree.currentIndex()
        if not idx.isValid():
            return
        parent = idx.parent()
        if parent.isValid():
            self.tree.setCurrentIndex(parent)
            self.tree.scrollTo(parent)
            self.path_box.setText(self.model.filePath(parent))
        else:
            self.tree.setCurrentIndex(QModelIndex())
            self.path_box.setText("此电脑")

    def _refresh(self):
        # 重新展开到当前位置
        idx = self.tree.currentIndex()
        self.model.setRootPath("")
        if idx.isValid():
            refreshed = self.model.index(self.model.filePath(idx))
            self.tree.setCurrentIndex(refreshed)

    # ================= 右键菜单 =================

    def _on_context_menu(self, pos):
        idx = self.tree.indexAt(pos)
        if not idx.isValid():
            return
        self.tree.setCurrentIndex(idx)
        path = self.model.filePath(idx)
        menu = QMenu(self)

        act_open = menu.addAction("打开")
        act_show = menu.addAction("在资源管理器中显示")
        menu.addSeparator()
        act_copy = menu.addAction("复制")
        act_cut = menu.addAction("剪切")
        menu.addSeparator()
        act_delete = menu.addAction("删除（移到回收站）")
        act_rename = menu.addAction("重命名")
        menu.addSeparator()
        act_copy_name = menu.addAction("复制文件名")
        act_copy_path = menu.addAction("复制完整路径")

        chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if chosen == act_open:
            self._open_path(path)
        elif chosen == act_show:
            self._show_in_explorer(path)
        elif chosen == act_copy:
            self._copy_to_clipboard([path], cut=False)
        elif chosen == act_cut:
            self._copy_to_clipboard([path], cut=True)
        elif chosen == act_delete:
            self._delete_to_recycle_bin(path)
        elif chosen == act_rename:
            self.tree.edit(idx)
        elif chosen == act_copy_name:
            QApplication.clipboard().setText(os.path.basename(path))
        elif chosen == act_copy_path:
            QApplication.clipboard().setText(path)

    # ================= 搜索结果右键菜单 =================

    def _on_search_context_menu(self, pos):
        item = self.search_view.itemAt(pos)
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        act_open = menu.addAction("打开")
        act_show = menu.addAction("在资源管理器中显示")
        menu.addSeparator()
        act_copy_path = menu.addAction("复制完整路径")
        chosen = menu.exec(self.search_view.viewport().mapToGlobal(pos))
        if chosen == act_open:
            self._open_path(path)
        elif chosen == act_show:
            self._show_in_explorer(path)
        elif chosen == act_copy_path:
            QApplication.clipboard().setText(path)

    def _on_search_result_activated(self, _):
        item = self.search_view.currentItem()
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        if os.path.isdir(path):
            self._open_path(path)
        else:
            self.router.open_file(path)

    # ================= 文件操作 =================

    def _open_path(self, path: str):
        if os.path.isdir(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            self.router.open_file(path)

    def _show_in_explorer(self, path: str):
        """打开资源管理器并定位/选中该文件（修复：路径需转换为反斜杠）"""
        path_win = os.path.abspath(path).replace("/", "\\")
        # explorer /select,"D:\path\file.txt" 会打开父目录并选中该文件
        subprocess.Popen(["explorer", f"/select,{path_win}"])

    def _copy_to_clipboard(self, paths, cut=False):
        """复制/剪切文件到剪贴板（支持在资源管理器中 Ctrl+V 粘贴）"""
        import struct

        data = QMimeData()
        data.setUrls([QUrl.fromLocalFile(p) for p in paths])
        data.setText("\n".join(paths))
        if cut:
            # Windows 剪贴板的"剪切"标记：Preferred DropEffect = DROPEFFECT_MOVE(2)
            data.setData("Preferred DropEffect", struct.pack("<I", 2))
        QApplication.clipboard().setMimeData(data)

    def _delete_to_recycle_bin(self, path: str):
        """删除文件/目录到回收站"""
        try:
            ok = send_to_recycle_bin(path)
            if not ok:
                self.hint.setText(f"删除失败：{path}")
            else:
                self.hint.setText(f"已移到回收站：{os.path.basename(path)}")
        except Exception as e:
            self.hint.setText(f"删除失败：{e}")

    # ================= 搜索 =================

    def _start_search(self):
        keyword = self.search_box.text().strip()
        if not keyword:
            self._stop_search()
            self.view_stack.setCurrentWidget(self.tree)
            self.search_status.hide()
            return
        # 停止之前的搜索
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(2000)
        # 清空结果
        self.search_view.clear()
        self.view_stack.setCurrentWidget(self.search_view)
        self.search_status.show()
        self.search_status.setText(f"正在搜索「{keyword}」…")

        self._worker = SearchWorker(keyword, self)
        self._worker.start()

        # 主线程轮询结果（绕开跨线程信号问题）
        self._polled = 0
        if hasattr(self, "_poll") and self._poll.isActive():
            self._poll.stop()
        self._poll = QTimer(self)
        self._poll.setInterval(200)
        self._poll.timeout.connect(self._poll_results)
        self._poll.start()

    def _poll_results(self):
        if self._worker is None:
            self._poll.stop()
            return
        results = self._worker.results
        n = len(results)
        if n > self._polled:
            new_paths = results[self._polled:n]
            self._polled = n
            self._on_search_batch(new_paths)
        if not self._worker.isRunning():
            self._poll.stop()
            self.search_status.setText(f"搜索完成，共找到 {n} 个结果")

    def _stop_search(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(2000)
            self.search_status.setText("搜索已停止")

    def _on_search_batch(self, paths):
        """批量添加搜索结果到列表"""
        for path in paths:
            name = os.path.basename(path)
            try:
                if os.path.isdir(path):
                    size_str = ""
                    type_str = "文件夹"
                else:
                    st = os.stat(path)
                    size_str = self._format_size(st.st_size)
                    ext = os.path.splitext(name)[1].lower()
                    type_str = f"{ext[1:].upper()} 文件" if ext else "文件"
            except OSError:
                size_str, type_str = "", ""

            item = QTreeWidgetItem([name, os.path.dirname(path), size_str, type_str])
            item.setData(0, Qt.UserRole, path)
            item.setToolTip(1, path)
            self.search_view.addTopLevelItem(item)

    @staticmethod
    def _format_size(size):
        if size < 1024:
            return f"{size} B"
        if size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        if size < 1024 ** 3:
            return f"{size / 1024 ** 2:.1f} MB"
        return f"{size / 1024 ** 3:.2f} GB"
