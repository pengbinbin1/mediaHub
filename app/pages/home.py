# home.py — 首页：功能入口卡片 + 最近打开
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from app.theme import (
    ACCENT_DOCS, ACCENT_FILES, ACCENT_IMAGE, ACCENT_VIDEO, PRIMARY, qss_rgba,
)


class CardButton(QFrame):
    """可点击的彩色卡片：圆底 emoji 图标 + 标题 + 描述。"""

    def __init__(self, title: str, desc: str, on_click, icon: str = "📁",
                 accent: str = PRIMARY, parent=None):
        super().__init__(parent, objectName="Card")
        self.on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(4)

        # 彩色圆底 emoji 图标
        badge = QLabel(icon)
        badge.setFixedSize(42, 42)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            background: {qss_rgba(accent, 26)};
            border: 1px solid {qss_rgba(accent, 60)};
            border-radius: 21px;
            font-size: 18px;
        """)
        lay.addWidget(badge)
        lay.addWidget(QLabel(title, objectName="CardTitle"))
        lay.addWidget(QLabel(desc, objectName="CardDesc"))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.underMouse():
            self.on_click()
        super().mouseReleaseEvent(event)


class HomePage(QWidget):
    def __init__(self, router, parent=None):
        super().__init__(parent)
        self.router = router

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(18)

        title = QLabel("极简媒体中心", objectName="PageTitle")
        subtitle = QLabel("视频 · 图片 · 文件 · 文档，一个干净的应用搞定", objectName="Hint")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(6)

        # ---- 功能卡片 ----
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        cards = [
            ("📁", PRIMARY, "打开文件…", "自动识别类型并打开", self._open_any),
            ("🎬", ACCENT_VIDEO, "视频播放", "播放 / 暂停 / 快进快退", lambda: router.switch_page("video")),
            ("🖼️", ACCENT_IMAGE, "图片查看", "切换 / 旋转 / 缩放", lambda: router.switch_page("image")),
            ("📂", ACCENT_FILES, "文件浏览", "浏览所有磁盘文件", lambda: router.switch_page("explorer")),
            ("📄", ACCENT_DOCS, "文档", "TXT · Word 编辑，PDF 查看", lambda: router.switch_page("docs")),
        ]
        for icon, accent, t, d, fn in cards:
            cards_row.addWidget(CardButton(t, d, fn, icon=icon, accent=accent))
        root.addLayout(cards_row)
        root.addSpacing(10)

        # ---- 最近打开 ----
        recent_title = QLabel("最近打开", objectName="CardTitle")
        root.addWidget(recent_title)
        self.recent_area = QScrollArea()
        self.recent_area.setWidgetResizable(True)
        self.recent_area.setFrameShape(QFrame.NoFrame)
        self.recent_host = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_host)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_layout.setSpacing(2)
        self.recent_layout.addStretch(1)
        self.recent_area.setWidget(self.recent_host)
        root.addWidget(self.recent_area, 1)

        tip = QLabel("提示：可直接把文件拖进窗口 · Word 保留基础排版 · PDF 为只读查看", objectName="Hint")
        root.addWidget(tip)

    def refresh_recent(self):
        # 清空旧条目（保留末尾 stretch）
        while self.recent_layout.count() > 1:
            item = self.recent_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for path in self.router.recent_files():
            if not os.path.exists(path):
                continue
            display = path if len(path) <= 76 else "…" + path[-75:]
            btn = QPushButton(display, objectName="RecentItem")
            btn.setToolTip(path)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, p=path: self.router.open_file(p))
            self.recent_layout.insertWidget(self.recent_layout.count() - 1, btn)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_recent()

    def _open_any(self):
        from app.dialogs import pick_open_file

        path = pick_open_file(self, "打开文件", "所有文件 (*)")
        if path:
            self.router.open_file(path)
