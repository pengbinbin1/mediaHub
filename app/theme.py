# 极简媒体中心 — 浅色极简 QSS 主题
# 白底、细边框、圆角、克制的黑色强调

GLOBAL_QSS = """
* {
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
    outline: none;
}
QMainWindow { background: #fafafa; }
QWidget { font-size: 13px; color: #1f2329; }

/* ---------- 侧边栏 ---------- */
QFrame#Sidebar { background: #ffffff; border-right: 1px solid #e9e9e9; }
QLabel#AppTitle { font-size: 15px; font-weight: 600; color: #111827; }
QLabel#AppVersion { color: #b0b5bc; font-size: 11px; }
QPushButton#NavButton {
    text-align: left; padding: 9px 16px; border: none; border-radius: 8px;
    background: transparent; color: #6b7280; font-size: 13px;
}
QPushButton#NavButton:hover { background: #f4f5f6; color: #1f2329; }
QPushButton#NavButton:checked { background: #eceef1; color: #111827; font-weight: 600; }

/* ---------- 页面标题 ---------- */
QLabel#PageTitle { font-size: 20px; font-weight: 600; color: #111827; }
QLabel#Hint { color: #9aa0a8; font-size: 12px; }
QLabel#Muted { color: #9aa0a8; font-size: 12px; }

/* ---------- 通用按钮 ---------- */
QPushButton {
    background: #ffffff; border: 1px solid #e2e4e8; border-radius: 8px;
    padding: 6px 14px; color: #1f2329;
}
QPushButton:hover { background: #f6f7f8; border-color: #c9cdd3; }
QPushButton:pressed { background: #eceef1; }
QPushButton:disabled { color: #b6bac0; background: #f6f7f8; }
QPushButton#Primary { background: #1f2329; border: 1px solid #1f2329; color: #ffffff; }
QPushButton#Primary:hover { background: #34383e; }
QPushButton#Primary:disabled { background: #9aa0a8; border-color: #9aa0a8; }
QPushButton#Flat {
    background: transparent; border: 1px solid transparent; border-radius: 6px;
    padding: 6px 12px; color: #4b5158;
}
QPushButton#Flat:hover { background: #f1f2f4; border-color: transparent; }
QPushButton#FormatBtn {
    padding: 5px 10px; font-weight: 600; min-width: 30px;
}
QPushButton#FormatBtn:checked { background: #1f2329; color: #ffffff; border-color: #1f2329; }

/* ---------- 首页卡片 ---------- */
QFrame#Card {
    background: #ffffff; border: 1px solid #e9e9e9; border-radius: 12px;
}
QFrame#Card:hover { border-color: #c2c6cb; background: #fdfdfd; }
QLabel#CardTitle { font-size: 15px; font-weight: 600; color: #111827; }
QLabel#CardDesc { color: #9aa0a8; font-size: 12px; }
QPushButton#RecentItem {
    text-align: left; background: transparent; border: none; border-radius: 6px;
    padding: 6px 10px; color: #4b5158;
}
QPushButton#RecentItem:hover { background: #f1f2f4; }

/* ---------- 视频 ---------- */
QFrame#VideoStage { background: #0a0a0a; border-radius: 12px; }
QLabel#VideoEmptyHint { color: #6b7280; font-size: 14px; }
QLabel#TimeLabel { color: #6b7280; font-size: 12px; }

/* ---------- 滑块 ---------- */
QSlider::groove:horizontal { height: 4px; background: #e5e7ea; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #1f2329; border-radius: 2px; }
QSlider::handle:horizontal {
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
    background: #ffffff; border: 1px solid #c9cdd3;
}
QSlider::handle:horizontal:hover { border-color: #1f2329; }
QSlider:disabled::sub-page:horizontal { background: #d5d8dc; }

/* ---------- 图片 ---------- */
QGraphicsView#ImageCanvas {
    background: #ffffff; border: 1px solid #e9e9e9; border-radius: 12px;
}

/* ---------- 文件树 ---------- */
QTreeView {
    background: #ffffff; border: 1px solid #e9e9e9; border-radius: 10px; padding: 4px;
}
QTreeView::item { height: 26px; border-radius: 6px; margin: 1px 0; }
QTreeView::item:hover { background: #f4f5f6; }
QTreeView::item:selected { background: #e8eaee; color: #111827; }
QTreeView::branch { background: transparent; }
QLineEdit#PathBox {
    background: #ffffff; border: 1px solid #e9e9e9; border-radius: 8px;
    padding: 6px 10px; color: #6b7280;
}

/* ---------- 文档 ---------- */
QTextEdit {
    background: #ffffff; border: 1px solid #e9e9e9; border-radius: 10px;
    padding: 12px 14px; selection-background-color: #dfe3e8;
}
QFrame#PdfStage { background: #f0f1f3; border-radius: 12px; }
QLabel#PdfCanvas { background: #ffffff; }

/* ---------- 多标签 ---------- */
QTabWidget::pane {
    border: 1px solid #e9e9e9; border-radius: 10px; top: -1px;
}
QTabBar::tab {
    background: transparent; color: #6b7280;
    padding: 7px 14px; margin-right: 2px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:hover { color: #1f2329; }
QTabBar::tab:selected {
    color: #111827; font-weight: 600;
    border-bottom: 2px solid #1f2329;
}

/* ---------- 滚动条 ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #d9dce0; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #c2c6cb; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #d9dce0; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #c2c6cb; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QToolTip {
    background: #ffffff; border: 1px solid #d5d8dc; border-radius: 6px;
    padding: 4px 8px; color: #1f2329;
}
QMenu {
    background: #ffffff; border: 1px solid #e5e7ea; border-radius: 8px; padding: 4px;
}
QMenu::item { padding: 6px 24px; border-radius: 6px; }
QMenu::item:selected { background: #f1f2f4; }
"""
