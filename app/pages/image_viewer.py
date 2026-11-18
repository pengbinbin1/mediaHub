# image_viewer.py — 极简图片查看页：上一张/下一张、旋转、缩放
import os

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFileDialog, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".jfif", ".tif", ".tiff", ".ico"}


class ImageCanvas(QGraphicsView):
    """滚轮缩放的画布。"""

    def __init__(self, page):
        super().__init__(objectName="ImageCanvas")
        self.page = page
        self.setScene(QGraphicsScene(self))
        self.item = QGraphicsPixmapItem()
        self.item.setTransformationMode(Qt.SmoothTransformation)
        self.scene().addItem(self.item)
        self.setAlignment(Qt.AlignCenter)
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        if self.item.pixmap().isNull():
            return
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.page.zoom_by(factor)


class ImagePage(QWidget):
    def __init__(self, router, parent=None):
        super().__init__(parent)
        self.router = router
        self.dir_images = []   # 同目录图片列表
        self.index = -1
        self._fit_pending = False

        self.canvas = ImageCanvas(self)
        self.empty_hint = QLabel("打开一张图片开始查看", objectName="Hint")
        self.empty_hint.setAlignment(Qt.AlignCenter)

        self.stack_layout = QVBoxLayout()
        self.stack_layout.addWidget(self.canvas)
        self.stack_layout.addWidget(self.empty_hint)
        self.canvas.hide()

        # ---- 控制条 ----
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.btn_open = QPushButton("打开")
        self.btn_open.clicked.connect(self._open_file)
        self.btn_prev = QPushButton("← 上一张")
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next = QPushButton("下一张 →")
        self.btn_next.clicked.connect(self.next_image)
        self.btn_rot_l = QPushButton("↺ 左旋")
        self.btn_rot_l.clicked.connect(lambda: self.rotate_by(-90))
        self.btn_rot_r = QPushButton("↻ 右旋")
        self.btn_rot_r.clicked.connect(lambda: self.rotate_by(90))
        self.btn_fit = QPushButton("适应窗口")
        self.btn_fit.clicked.connect(self.fit_window)
        self.btn_actual = QPushButton("1:1")
        self.btn_actual.clicked.connect(self.actual_size)
        self.zoom_label = QLabel("", objectName="Muted")
        self.pos_label = QLabel("未打开图片", objectName="Muted")

        for b in (self.btn_open, self.btn_prev, self.btn_next,
                  self.btn_rot_l, self.btn_rot_r, self.btn_fit, self.btn_actual):
            b.setFocusPolicy(Qt.NoFocus)

        bar.addWidget(self.btn_open)
        bar.addSpacing(10)
        bar.addWidget(self.btn_prev)
        bar.addWidget(self.btn_next)
        bar.addSpacing(10)
        bar.addWidget(self.btn_rot_l)
        bar.addWidget(self.btn_rot_r)
        bar.addSpacing(10)
        bar.addWidget(self.btn_fit)
        bar.addWidget(self.btn_actual)
        bar.addStretch(1)
        bar.addWidget(self.zoom_label)
        bar.addSpacing(14)
        bar.addWidget(self.pos_label)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 20)
        root.setSpacing(12)
        root.addLayout(self.stack_layout, 1)
        root.addLayout(bar)

        # 键盘：←/→ 切换，+/- 缩放，R 右旋
        for seq, fn in (
            (Qt.Key_Left, self.prev_image),
            (Qt.Key_Right, self.next_image),
            (Qt.Key_Plus, lambda: self.zoom_by(1.25)),
            (Qt.Key_Minus, lambda: self.zoom_by(0.8)),
            (Qt.Key_R, lambda: self.rotate_by(90)),
        ):
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(fn)

    # ---------- 对外接口 ----------
    def load(self, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            return
        self.canvas.show()
        self.empty_hint.hide()
        self.item = self.canvas.item
        self.item.setPixmap(pix)
        self.item.setRotation(0)
        self.item.setTransformOriginPoint(pix.width() / 2, pix.height() / 2)
        self._sync_dir(os.path.dirname(path), path)
        self.fit_window()
        if hasattr(self.window(), "set_current_file"):
            self.window().set_current_file(path)

    # ---------- 切换 ----------
    def prev_image(self):
        self._step(-1)

    def next_image(self):
        self._step(1)

    def _step(self, delta: int):
        if not self.dir_images:
            return
        self.index = (self.index + delta) % len(self.dir_images)
        self.load(self.dir_images[self.index])

    def _sync_dir(self, dirpath: str, current: str):
        try:
            names = [f for f in os.listdir(dirpath)
                     if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
            names.sort(key=str.lower)
            self.dir_images = [os.path.join(dirpath, n) for n in names]
            self.index = self.dir_images.index(current) if current in self.dir_images else -1
        except OSError:
            self.dir_images, self.index = [], -1
        self._update_pos()

    def _update_pos(self):
        total = len(self.dir_images)
        self.pos_label.setText(f"{self.index + 1} / {total} 张" if 0 <= self.index < total else "未打开图片")

    # ---------- 旋转 / 缩放 ----------
    def rotate_by(self, deg: int):
        if self.item.pixmap().isNull():
            return
        self.item.setRotation((self.item.rotation() + deg) % 360)
        self.canvas.scene().setSceneRect(self.item.sceneBoundingRect())
        self.fit_window()

    def _apply_zoom(self, z: float):
        z = max(0.02, min(z, 24.0))
        self.canvas.resetTransform()
        self.canvas.scale(z, z)
        self.zoom_label.setText(f"{z * 100:.0f}%")

    def zoom_by(self, factor: float):
        if self.item.pixmap().isNull():
            return
        self._apply_zoom(self.canvas.transform().m11() * factor)

    def fit_window(self):
        if self.item.pixmap().isNull():
            return
        self.canvas.scene().setSceneRect(self.item.sceneBoundingRect())
        self.canvas.fitInView(self.item, Qt.KeepAspectRatio)
        self.zoom_label.setText(f"{self.canvas.transform().m11() * 100:.0f}%")

    def actual_size(self):
        if self.item.pixmap().isNull():
            return
        self._apply_zoom(1.0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口尺寸变化时保持“适应窗口”体验（未加载图片时安全跳过）
        if hasattr(self, "item") and not self.item.pixmap().isNull():
            self.fit_window()

    # ---------- 打开 ----------
    def _open_file(self):
        from app.dialogs import pick_open_file

        path = pick_open_file(
            self, "打开图片",
            "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.jfif *.tif *.tiff);;所有文件 (*)"
        )
        if path:
            self.load(path)
