# main.py — 极简媒体中心：主窗口、侧边栏导航、文件路由、最近打开
import os
import sys

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from app.pages.documents import TXT_EXTS
from app.pages.explorer import DOC_EXTS, VIDEO_EXTS
from app.pages.image_viewer import IMAGE_EXTS
from app.pages.documents import DocumentsPage
from app.pages.explorer import ExplorerPage
from app.pages.home import HomePage
from app.pages.image_viewer import ImagePage
from app.pages.video import VideoPage
from app.theme import GLOBAL_QSS, nav_button_qss

NAV_ITEMS = [
    ("home", "首页", "🏠", "#4F6BFF"),     # 靛蓝
    ("video", "视频", "🎬", "#8B5CF6"),    # 紫
    ("image", "图片", "🖼️", "#10B981"),   # 绿
    ("explorer", "文件", "📂", "#F59E0B"), # 橙
    ("docs", "文档", "📄", "#06B6D4"),     # 青
]


def resource_path(rel: str) -> str:
    """兼容源码运行与 PyInstaller 打包后的资源路径。"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("极简媒体中心")
        self.setWindowIcon(QIcon(resource_path(os.path.join("resources", "icon.ico"))))
        self.resize(1180, 780)
        self.setMinimumSize(960, 620)
        self.setAcceptDrops(True)

        self.settings = QSettings("MiniHub", "MiniHub")

        # ---- 页面 ----
        self.pages = {}
        self.stack = QStackedWidget()
        for key, make in (
            ("home", lambda: HomePage(self)),
            ("video", lambda: VideoPage(self)),
            ("image", lambda: ImagePage(self)),
            ("explorer", lambda: ExplorerPage(self)),
            ("docs", lambda: DocumentsPage(self)),
        ):
            page = make()
            self.pages[key] = page
            self.stack.addWidget(page)

        # ---- 侧边栏 ----
        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(148)
        side_lay = QVBoxLayout(sidebar)
        side_lay.setContentsMargins(10, 18, 10, 14)
        side_lay.setSpacing(2)

        # 品牌区：渐变圆形 logo + 标题
        logo = QLabel("M")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4F6BFF, stop:1 #8B5CF6);
            color: #ffffff; font-size: 18px; font-weight: 800;
            border-radius: 18px;
        """)
        brand = QLabel("MiniHub", objectName="AppTitle")
        version = QLabel("极简媒体中心 · v1.0", objectName="AppVersion")

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.setSpacing(10)
        brand_row.addWidget(logo)
        brand_col = QVBoxLayout()
        brand_col.setContentsMargins(0, 0, 0, 0)
        brand_col.setSpacing(0)
        brand_col.addWidget(brand)
        brand_col.addWidget(version)
        brand_row.addLayout(brand_col)
        side_lay.addLayout(brand_row)
        side_lay.addSpacing(14)

        self.nav_buttons = {}
        for key, label, icon, _accent in NAV_ITEMS:
            btn = QPushButton(f"{icon}  {label}", objectName="NavButton")
            btn.setProperty("navKey", key)
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, k=key: self.switch_page(k))
            self.nav_buttons[key] = btn
            side_lay.addWidget(btn)
        side_lay.addStretch(1)

        # ---- 布局 ----
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(sidebar)
        body.addWidget(self.stack, 1)
        central = QWidget()
        central.setLayout(body)
        self.setCentralWidget(central)

        self.switch_page("home")
        # 子控件不再拦截拖拽，统一由主窗口路由
        self._disable_child_drops()

    # ---------- 页面切换 ----------
    def switch_page(self, key: str):
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        page.setFocus(Qt.FocusReason.OtherFocusReason)

    # ---------- 文件路由 ----------
    def open_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXTS:
            self.pages["video"].load(path)
            self.switch_page("video")
        elif ext in IMAGE_EXTS:
            self.pages["image"].load(path)
            self.switch_page("image")
        elif ext in DOC_EXTS or ext in TXT_EXTS:
            self.pages["docs"].load(path)
            self.switch_page("docs")
        else:
            # 其他类型交给系统默认程序
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        self.add_recent(path)

    def set_current_file(self, path: str):
        name = os.path.basename(path)
        self.setWindowTitle(f"{name} — 极简媒体中心")

    # ---------- 最近打开 ----------
    def recent_files(self):
        vals = self.settings.value("recent/files", [])
        if isinstance(vals, str):
            vals = [vals]
        return [str(v) for v in vals]

    def add_recent(self, path: str):
        paths = [p for p in self.recent_files() if p != path]
        paths.insert(0, path)
        self.settings.setValue("recent/files", paths[:8])

    # ---------- 拖放 ----------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local:
                self.open_file(local)
        event.acceptProposedAction()

    def _disable_child_drops(self):
        """禁用所有子控件的拖拽接收，让 drop 事件冒泡到主窗口统一路由。"""
        for child in self.findChildren(QWidget):
            child.setAcceptDrops(False)
            # QTextEdit / QAbstractScrollArea 的事件实际由 viewport 处理
            vp_method = getattr(child, "viewport", None)
            if callable(vp_method):
                vp = vp_method()
                if vp is not None:
                    vp.setAcceptDrops(False)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS + nav_button_qss())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
