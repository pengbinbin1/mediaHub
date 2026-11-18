# documents.py — 文档页：多标签文档（TXT/DOCX 编辑 + PDF 查看）
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QFont, QPixmap, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QStackedLayout, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

import pymupdf as fitz  # PyMuPDF

from app import docx_io

TXT_EXTS = {".txt", ".md", ".log", ".text", ".ini", ".csv"}


class DocumentTab(QWidget):
    """单个文档标签：编辑器（TXT/DOCX）或 PDF 渲染区。

    每个标签独立持有文件路径、文档类型、编辑/渲染状态，
    多个标签可同时存在且互不干扰。
    """

    def __init__(self, path: str, page=None, parent=None):
        super().__init__(parent)
        self.file_path = path
        self.page = page      # 宿主 DocumentsPage，用于刷新工具栏状态
        self.doc_kind = None  # 'txt' | 'docx' | 'pdf'

        # 编辑器（TXT / DOCX）
        self.editor = QTextEdit()
        # 光标/格式变化时同步工具栏 B/I/U 按钮状态
        self.editor.cursorPositionChanged.connect(self._notify_format_changed)
        self.editor.currentCharFormatChanged.connect(lambda _f: self._notify_format_changed())

        # PDF 渲染区
        self.pdf_label = QLabel(objectName="PdfCanvas")
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.pdf_scroll = QScrollArea(widgetResizable=True)
        self.pdf_scroll.setWidget(self.pdf_label)
        self.pdf_doc = None
        self.pdf_page_no = 0
        self.pdf_zoom = 1.0

        self.stack = QStackedLayout(self)
        self.stack.addWidget(self.editor)
        self.stack.addWidget(self.pdf_scroll)
        self._load_file(path)
        # 动态创建的标签不在 MainWindow 初始禁用范围内，
        # 这里禁用其内部控件的拖放接收，让 drop 冒泡到主窗口统一路由
        self._disable_child_drops()

    # ---------- 加载 ----------
    def _load_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            self._load_pdf(path)
        elif ext == ".docx":
            self._load_docx(path)
        else:
            self._load_txt(path)

    def _notify_format_changed(self):
        """当前标签的编辑器格式变化时，刷新 B/I/U 按钮状态。"""
        if self.page and self.page.current_tab() is self:
            self.page._sync_format_buttons()

    def _disable_child_drops(self):
        """禁用本标签内所有控件的拖拽接收。

        QTextEdit / QScrollArea 的 viewport 默认接受 drop，会拦截
        拖入的后续文件；关闭后 drop 冒泡到 MainWindow 统一路由。
        """
        self.setAcceptDrops(False)
        for child in self.findChildren(QWidget):
            child.setAcceptDrops(False)
            # QTextEdit / QAbstractScrollArea 的事件实际由 viewport 处理
            vp_method = getattr(child, "viewport", None)
            if callable(vp_method):
                vp = vp_method()
                if vp is not None:
                    vp.setAcceptDrops(False)

    def _load_txt(self, path: str):
        text = None
        for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
            try:
                with open(path, "r", encoding=enc) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            text = ""
        self.editor.setPlainText(text)
        self.doc_kind = "txt"
        self.stack.setCurrentWidget(self.editor)

    def _load_docx(self, path: str):
        try:
            html = docx_io.load_docx_to_html(path)
        except Exception as e:
            self.editor.setPlainText(f"无法读取 Word 文档：{e}\n\n提示：仅支持 .docx（新版 Word 格式）")
            self.doc_kind = "txt"
            self.stack.setCurrentWidget(self.editor)
            return
        self.editor.setHtml(html)
        self.doc_kind = "docx"
        self.stack.setCurrentWidget(self.editor)

    def _load_pdf(self, path: str):
        try:
            self.pdf_doc = fitz.open(path)
        except Exception as e:
            self.pdf_label.setText(f"无法打开 PDF：{e}")
            self.pdf_doc = None
            return
        self.pdf_page_no = 0
        self.doc_kind = "pdf"
        self.stack.setCurrentWidget(self.pdf_scroll)
        self._pdf_fit_width()

    # ---------- 修改状态 ----------
    def is_modified(self) -> bool:
        return self.doc_kind in ("txt", "docx") and self.editor.document().isModified()

    # ---------- PDF ----------
    def _pdf_fit_width(self):
        if not self.pdf_doc:
            return
        page = self.pdf_doc.load_page(self.pdf_page_no)
        vw = self.pdf_scroll.viewport().width()
        self.pdf_zoom = max(0.2, min((vw - 48) / page.rect.width, 6.0))
        self._pdf_render()

    def _pdf_render(self):
        if not self.pdf_doc:
            return
        page = self.pdf_doc.load_page(self.pdf_page_no)
        mat = fitz.Matrix(self.pdf_zoom, self.pdf_zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.pdf_label.setPixmap(QPixmap.fromImage(img))
        self._update_pdf_status()

    def _update_pdf_status(self):
        """刷新文档页工具栏上的 PDF 页码/缩放显示。"""
        if self.pdf_doc and self.page:
            self.page.page_label.setText(f"  {self.pdf_page_no + 1} / {self.pdf_doc.page_count}  ")
            self.page.zoom_label.setText(f"{self.pdf_zoom * 100:.0f}%")

    def showEvent(self, event):
        super().showEvent(event)
        # 标签首次显示时 viewport 才有真实宽度，此时适应一次
        if self.doc_kind == "pdf" and not getattr(self, "_pdf_shown", False):
            self._pdf_shown = True
            self._pdf_fit_width()

    def pdf_turn(self, delta: int):
        if not self.pdf_doc:
            return
        n = self.pdf_page_no + delta
        if 0 <= n < self.pdf_doc.page_count:
            self.pdf_page_no = n
            self._pdf_render()

    def pdf_zoom_by(self, factor: float):
        if not self.pdf_doc:
            return
        self.pdf_zoom = max(0.2, min(self.pdf_zoom * factor, 6.0))
        self._pdf_render()

    def close_pdf(self):
        """释放 PDF 资源。"""
        if self.pdf_doc:
            self.pdf_doc.close()
            self.pdf_doc = None


class DocumentsPage(QWidget):
    """文档页：多标签容器，工具栏作用于当前激活标签。"""

    def __init__(self, router, parent=None):
        super().__init__(parent)
        self.router = router

        # ---------- 工具栏 ----------
        self.btn_open = QPushButton("打开")
        self.btn_open.clicked.connect(self._open_file)
        self.btn_save = QPushButton("保存", objectName="Primary")
        self.btn_save.clicked.connect(self.save)
        self.btn_save_as = QPushButton("另存为")
        self.btn_save_as.clicked.connect(self._save_as)
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self._close_current)
        self.btn_bold = QPushButton("B", objectName="FormatBtn")
        self.btn_bold.setCheckable(True)
        self.btn_bold.clicked.connect(lambda: self._toggle_char_format("bold"))
        self.btn_italic = QPushButton("I", objectName="FormatBtn")
        self.btn_italic.setCheckable(True)
        self.btn_italic.clicked.connect(lambda: self._toggle_char_format("italic"))
        self.btn_underline = QPushButton("U", objectName="FormatBtn")
        self.btn_underline.setCheckable(True)
        self.btn_underline.clicked.connect(lambda: self._toggle_char_format("underline"))

        # PDF 导航组
        self.btn_prev_page = QPushButton("← 上一页")
        self.btn_prev_page.clicked.connect(lambda: self._pdf_turn(-1))
        self.btn_next_page = QPushButton("下一页 →")
        self.btn_next_page.clicked.connect(lambda: self._pdf_turn(1))
        self.page_label = QLabel("", objectName="Muted")
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.clicked.connect(lambda: self._pdf_zoom_by(0.8))
        self.btn_zoom_in = QPushButton("＋")
        self.btn_zoom_in.clicked.connect(lambda: self._pdf_zoom_by(1.25))
        self.btn_fit_w = QPushButton("适应宽度")
        self.btn_fit_w.clicked.connect(self._pdf_fit_width)
        self.zoom_label = QLabel("", objectName="Muted")

        self.modified_dot = QLabel("", objectName="Muted")

        for b in (self.btn_open, self.btn_save, self.btn_save_as, self.btn_close,
                  self.btn_bold, self.btn_italic, self.btn_underline, self.btn_prev_page,
                  self.btn_next_page, self.btn_zoom_in, self.btn_zoom_out, self.btn_fit_w):
            b.setFocusPolicy(Qt.NoFocus)

        bar = QHBoxLayout()
        bar.setSpacing(8)
        bar.addWidget(self.btn_open)
        bar.addWidget(self.btn_save)
        bar.addWidget(self.btn_save_as)
        bar.addWidget(self.btn_close)
        bar.addSpacing(12)
        bar.addWidget(self.btn_bold)
        bar.addWidget(self.btn_italic)
        bar.addWidget(self.btn_underline)
        bar.addWidget(self.modified_dot)
        bar.addStretch(1)
        bar.addWidget(self.btn_prev_page)
        bar.addWidget(self.page_label)
        bar.addWidget(self.btn_next_page)
        bar.addSpacing(12)
        bar.addWidget(self.btn_zoom_out)
        bar.addWidget(self.btn_zoom_in)
        bar.addWidget(self.btn_fit_w)
        bar.addWidget(self.zoom_label)

        # ---------- 多标签容器 ----------
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)

        # ---------- 空状态提示 ----------
        self.empty_hint = QLabel("打开 TXT / Word / PDF 文档\n可同时打开多个文件", objectName="Hint")
        self.empty_hint.setAlignment(Qt.AlignCenter)

        self.holder = QStackedLayout()
        self.holder.addWidget(self.tab_widget)   # index 0
        self.holder.addWidget(self.empty_hint)   # index 1
        self.holder.setCurrentIndex(1)           # 初始显示空状态

        self.path_label = QLabel("未打开文件", objectName="Muted")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 20)
        root.setSpacing(12)
        root.addLayout(bar)
        root.addLayout(self.holder, 1)
        root.addWidget(self.path_label)

        self._sync_toolbar_state()

    # ---------- 对外接口 ----------
    def load(self, path: str):
        """打开文档到新标签；已在其他标签打开时切换过去。"""
        if not os.path.exists(path):
            self.path_label.setText(f"文件不存在：{path}")
            return
        abspath = os.path.abspath(path)
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab and os.path.abspath(tab.file_path) == abspath:
                self.tab_widget.setCurrentIndex(i)
                return
        tab = DocumentTab(path, page=self)
        tab.editor.document().modificationChanged.connect(
            lambda _: self._update_modified_indicator()
        )
        self.tab_widget.addTab(tab, os.path.basename(path))
        if self.holder.currentIndex() == 1:
            self.holder.setCurrentIndex(0)
        self.tab_widget.setCurrentWidget(tab)

    def current_tab(self) -> DocumentTab:
        return self.tab_widget.currentWidget()

    # ---------- 保存 ----------
    def save(self):
        """保存当前标签。"""
        self._save_tab(self.current_tab())

    def _save_tab(self, tab) -> bool:
        """保存指定标签；返回是否保存成功。"""
        if not tab or tab.doc_kind not in ("txt", "docx") or not tab.file_path:
            return False
        try:
            if tab.doc_kind == "docx":
                docx_io.save_docx_from_qdocument(tab.editor.document(), tab.file_path)
            else:
                with open(tab.file_path, "w", encoding="utf-8", newline="") as f:
                    f.write(tab.editor.toPlainText())
            tab.editor.document().setModified(False)
            return True
        except Exception as e:  # 权限/占用等
            self.path_label.setText(f"保存失败：{e}")
            return False

    def _save_as(self):
        from app.dialogs import pick_save_file

        tab = self.current_tab()
        if not tab or tab.doc_kind not in ("txt", "docx"):
            return
        default = tab.file_path or "未命名"
        if tab.doc_kind == "docx":
            path = pick_save_file(self, "另存为", default, "Word 文档 (*.docx)")
        else:
            path = pick_save_file(self, "另存为", default, "文本文件 (*.txt)")
        if path:
            tab.file_path = path
            self.save()
            idx = self.tab_widget.currentIndex()
            self.tab_widget.setTabText(idx, os.path.basename(path))
            self._update_modified_indicator()

    # ---------- 关闭标签 ----------
    def _close_current(self):
        self._close_tab(self.tab_widget.currentIndex())

    def _close_tab(self, index: int):
        """关闭指定标签；有未保存修改时提示。"""
        if index < 0 or index >= self.tab_widget.count():
            return
        tab = self.tab_widget.widget(index)
        if tab.is_modified():
            box = QMessageBox(self)
            box.setWindowTitle("未保存的修改")
            box.setText(f"「{os.path.basename(tab.file_path or '')}」有未保存的修改。\n保存后关闭？")
            btn_save = box.addButton("保存", QMessageBox.ButtonRole.YesRole)
            box.addButton("不保存", QMessageBox.ButtonRole.DestructiveRole)
            btn_cancel = box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is btn_cancel:
                return
            if box.clickedButton() is btn_save:
                if not self._save_tab(tab):
                    return  # 保存失败，保持文档打开
        tab.close_pdf()
        self.tab_widget.removeTab(index)
        tab.deleteLater()
        if self.tab_widget.count() == 0:
            self.holder.setCurrentIndex(1)
            self.path_label.setText("未打开文件")
            self._sync_toolbar_state()

    # ---------- 标签切换 ----------
    def _on_tab_changed(self, index):
        tab = self.tab_widget.widget(index) if index >= 0 else None
        self.path_label.setText(tab.file_path if tab and tab.file_path else "未打开文件")
        if tab and tab.file_path and hasattr(self.window(), "set_current_file"):
            self.window().set_current_file(tab.file_path)
        self._sync_toolbar_state()
        self._update_modified_indicator()
        if tab and tab.doc_kind == "pdf":
            tab._update_pdf_status()
        self._sync_format_buttons()

    def _sync_toolbar_state(self):
        """根据当前标签类型显示/隐藏工具栏按钮组。"""
        tab = self.current_tab()
        kind = tab.doc_kind if tab else None
        editing = kind in ("txt", "docx")
        is_pdf = kind == "pdf"
        # 保存/另存为/格式组只在编辑模式显示
        for b in (self.btn_save, self.btn_save_as, self.btn_bold,
                  self.btn_italic, self.btn_underline):
            b.setVisible(editing)
        # PDF 导航只在 PDF 模式显示
        for w in (self.btn_prev_page, self.btn_next_page, self.page_label,
                  self.btn_zoom_in, self.btn_zoom_out, self.btn_fit_w, self.zoom_label):
            w.setVisible(is_pdf)

    def _update_modified_indicator(self):
        """当前标签有未保存修改时显示 ●。"""
        tab = self.current_tab()
        idx = self.tab_widget.currentIndex()
        modified = tab.is_modified() if tab else False
        if idx >= 0 and tab:
            name = os.path.basename(tab.file_path or "未命名")
            self.tab_widget.setTabText(idx, f"{name} ●" if modified else name)
        self.modified_dot.setText("已修改 ●" if modified else "")

    # ---------- 富文本格式 ----------
    def _toggle_char_format(self, prop: str):
        tab = self.current_tab()
        if not tab or tab.doc_kind not in ("txt", "docx"):
            return
        editor = tab.editor
        cursor = editor.textCursor()
        fmt = QTextCharFormat()
        if prop == "bold":
            current = cursor.charFormat().fontWeight() >= 600
            fmt.setFontWeight(QFont.Weight.Normal if current else QFont.Weight.Bold)
        elif prop == "italic":
            current = cursor.charFormat().fontItalic()
            fmt.setFontItalic(not current)
        else:
            current = cursor.charFormat().fontUnderline()
            fmt.setFontUnderline(not current)
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)
        editor.setFocus()

    def _sync_format_buttons(self):
        tab = self.current_tab()
        if not tab or tab.doc_kind not in ("txt", "docx"):
            return
        cf = tab.editor.textCursor().charFormat()
        self.btn_bold.setChecked(cf.fontWeight() >= 600)
        self.btn_italic.setChecked(cf.fontItalic())
        self.btn_underline.setChecked(cf.fontUnderline())

    # ---------- PDF 导航（转发到当前标签） ----------
    def _pdf_turn(self, delta: int):
        tab = self.current_tab()
        if tab and tab.doc_kind == "pdf":
            tab.pdf_turn(delta)

    def _pdf_zoom_by(self, factor: float):
        tab = self.current_tab()
        if tab and tab.doc_kind == "pdf":
            tab.pdf_zoom_by(factor)

    def _pdf_fit_width(self):
        tab = self.current_tab()
        if tab and tab.doc_kind == "pdf":
            tab._pdf_fit_width()

    # ---------- 打开 ----------
    def _open_file(self):
        from app.dialogs import pick_open_files

        paths = pick_open_files(
            self, "打开文档（可多选）",
            "文档 (*.txt *.md *.docx *.pdf *.log *.ini *.csv);;所有文件 (*)"
        )
        for path in paths:
            self.load(path)
