# theme.py — 彩色主题：品牌靛蓝 + 各页专属强调色
# 浅色底、圆角卡片、彩色点缀，告别纯黑白

# ---------- 配色 ----------
PRIMARY      = "#4F6BFF"   # 品牌靛蓝（主按钮 / 选中态）
PRIMARY_DARK = "#3B53D9"
PRIMARY_SOFT = "#EEF1FF"   # 品牌色浅背景（选中行 / 菜单悬停）

ACCENT_VIDEO = "#8B5CF6"   # 紫 —— 视频
ACCENT_IMAGE = "#10B981"   # 绿 —— 图片
ACCENT_FILES = "#F59E0B"   # 橙 —— 文件
ACCENT_DOCS  = "#06B6D4"   # 青 —— 文档

BG_WINDOW = "#F7F8FC"      # 主窗口底（极浅蓝紫，比纯白有质感）
BG_PANEL  = "#FFFFFF"      # 卡片 / 侧边栏
BORDER    = "#E7E9F0"
TEXT_MAIN = "#1F2329"
TEXT_MUTE = "#8A90A0"


def qss_rgba(hex_color: str, alpha: int) -> str:
    """hex 颜色 → QSS 的 rgba() 字符串（alpha 0-255）。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def nav_button_qss() -> str:
    """为侧边栏每个导航按钮生成彩色选中态（按 navKey 属性匹配）。"""
    colors = {
        "home":     PRIMARY,
        "video":    ACCENT_VIDEO,
        "image":    ACCENT_IMAGE,
        "explorer": ACCENT_FILES,
        "docs":     ACCENT_DOCS,
    }
    parts = []
    for key, accent in colors.items():
        parts.append(f'''
QPushButton#NavButton[navKey="{key}"]:hover {{
    color: {accent};
}}
QPushButton#NavButton[navKey="{key}"]:checked {{
    background: {qss_rgba(accent, 26)};
    color: {accent};
    font-weight: 600;
    border-left: 3px solid {accent};
}}''')
    return "".join(parts)


GLOBAL_QSS = f'''
* {{
    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
    outline: none;
}}
QMainWindow {{ background: {BG_WINDOW}; }}
QWidget {{ font-size: 13px; color: {TEXT_MAIN}; }}

/* ---------- 侧边栏 ---------- */
QFrame#Sidebar {{ background: {BG_PANEL}; border-right: 1px solid {BORDER}; }}
QLabel#AppTitle {{ font-size: 15px; font-weight: 700; color: #111827; }}
QLabel#AppVersion {{ color: #b0b5bc; font-size: 11px; }}
QPushButton#NavButton {{
    text-align: left; padding: 9px 14px; border: none; border-radius: 8px;
    border-left: 3px solid transparent;
    background: transparent; color: #6b7280; font-size: 13px;
}}
QPushButton#NavButton:hover {{ background: #f4f5f6; color: #1f2329; }}

/* ---------- 通用按钮 ---------- */
QPushButton {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 6px 14px; color: {TEXT_MAIN};
}}
QPushButton:hover {{ background: #fdfdfe; border-color: {qss_rgba(PRIMARY, 120)}; }}
QPushButton:pressed {{ background: {PRIMARY_SOFT}; }}
QPushButton:disabled {{ color: #b6bac0; background: #f6f7f8; }}

QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {PRIMARY}, stop:1 #6A5CFF);
    border: none; color: #ffffff; font-weight: 600;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {PRIMARY_DARK}, stop:1 #5949E8);
}}
QPushButton#Primary:pressed {{ background: {PRIMARY_DARK}; }}
QPushButton#Primary:disabled {{ background: #aeb6e8; }}

QPushButton#Flat {{
    background: transparent; border: 1px solid transparent; border-radius: 6px;
    padding: 6px 12px; color: #4b5158;
}}
QPushButton#Flat:hover {{ background: #f1f2f4; border-color: transparent; }}
QPushButton#FormatBtn {{
    padding: 5px 10px; font-weight: 600; min-width: 30px;
}}
QPushButton#FormatBtn:hover {{ border-color: {qss_rgba(PRIMARY, 120)}; }}
QPushButton#FormatBtn:checked {{
    background: {PRIMARY}; color: #ffffff; border-color: {PRIMARY};
}}

/* ---------- 首页卡片 ---------- */
QFrame#Card {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
}}
QFrame#Card:hover {{ border-color: {qss_rgba(PRIMARY, 160)}; }}
QLabel#CardTitle {{ font-size: 15px; font-weight: 600; color: #111827; }}
QLabel#CardDesc {{ color: {TEXT_MUTE}; font-size: 12px; }}
QPushButton#RecentItem {{
    text-align: left; background: transparent; border: none; border-radius: 6px;
    padding: 6px 10px; color: #4b5158;
}}
QPushButton#RecentItem:hover {{ background: {PRIMARY_SOFT}; }}

/* ---------- 页面标题 ---------- */
QLabel#PageTitle {{ font-size: 20px; font-weight: 600; color: #111827; }}
QLabel#Hint {{ color: {TEXT_MUTE}; font-size: 12px; }}
QLabel#Muted {{ color: {TEXT_MUTE}; font-size: 12px; }}

/* ---------- 输入框 ---------- */
QLineEdit {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 6px 10px; color: {TEXT_MAIN};
}}
QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}

/* ---------- 视频 ---------- */
QFrame#VideoStage {{ background: #0a0a0a; border-radius: 12px; }}
QLabel#VideoEmptyHint {{ color: #6b7280; font-size: 14px; }}
QLabel#TimeLabel {{ color: {TEXT_MUTE}; font-size: 12px; }}

/* ---------- 滑块（品牌色进度） ---------- */
QSlider::groove:horizontal {{ height: 4px; background: #e5e7ea; border-radius: 2px; }}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {PRIMARY}, stop:1 #6A5CFF);
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
    background: #ffffff; border: 1px solid {qss_rgba(PRIMARY, 160)};
}}
QSlider::handle:horizontal:hover {{ border: 1px solid {PRIMARY}; }}
QSlider:disabled::sub-page:horizontal {{ background: #d5d8dc; }}

/* ---------- 图片 ---------- */
QGraphicsView#ImageCanvas {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
}}

/* ---------- 文件树 ---------- */
QTreeView {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 4px;
}}
QTreeView::item {{ height: 26px; border-radius: 6px; margin: 1px 0; }}
QTreeView::item:hover {{ background: #f4f5f6; }}
QTreeView::item:selected {{ background: {PRIMARY_SOFT}; color: {PRIMARY_DARK}; }}
QTreeView::branch {{ background: transparent; }}
QLineEdit#PathBox {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 6px 10px; color: {TEXT_MUTE};
}}

/* ---------- 文档 ---------- */
QTextEdit {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 12px 14px;
    selection-background-color: #C7D2FE; selection-color: {TEXT_MAIN};
}}
QFrame#PdfStage {{ background: #f0f1f3; border-radius: 12px; }}
QLabel#PdfCanvas {{ background: {BG_PANEL}; }}

/* ---------- 多标签（品牌色选中态） ---------- */
QTabWidget::pane {{
    border: 1px solid {BORDER}; border-radius: 10px; top: -1px;
}}
QTabBar::tab {{
    background: transparent; color: #6b7280;
    padding: 7px 14px; margin-right: 2px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}}
QTabBar::tab:hover {{ color: {PRIMARY}; }}
QTabBar::tab:selected {{
    color: {PRIMARY_DARK}; font-weight: 600;
    border-bottom: 2px solid {PRIMARY};
}}

/* ---------- 滚动条（悬停变品牌色） ---------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #d9dce0; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {PRIMARY}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #d9dce0; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {PRIMARY}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------- 菜单 / 提示 ---------- */
QMenu {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px;
}}
QMenu::item {{ padding: 6px 24px; border-radius: 6px; }}
QMenu::item:selected {{ background: {PRIMARY_SOFT}; color: {PRIMARY_DARK}; }}
QToolTip {{
    background: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 4px 8px; color: {TEXT_MAIN};
}}
'''
