# video.py — 极简视频播放页：播放/暂停、±10s 快进快退、进度条、音量
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
    QSizePolicy, QFileDialog,
)


def _fmt_ms(ms: int) -> str:
    s = int(ms // 1000)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class VideoPage(QWidget):
    def __init__(self, router, parent=None):
        super().__init__(parent)
        self.router = router
        self._seeking = False

        # ---- 播放器内核 ----
        self.player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.audio_out.setVolume(0.7)
        self.player.setAudioOutput(self.audio_out)
        self.player.errorOccurred.connect(self._on_error)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.mediaStatusChanged.connect(self._on_media_status)

        # ---- 画面区 ----
        self.stage = QFrame(objectName="VideoStage")
        stage_lay = QVBoxLayout(self.stage)
        stage_lay.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stage_lay.addWidget(self.video_widget)
        self.empty_hint = QLabel("打开一个视频文件开始播放", objectName="VideoEmptyHint")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        stage_lay.addWidget(self.empty_hint)
        self.video_widget.hide()

        # ---- 控制条 ----
        bar = QFrame()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.btn_open = QPushButton("打开")
        self.btn_open.clicked.connect(self._open_file)

        self.btn_back = QPushButton("快退 10s")
        self.btn_back.clicked.connect(lambda: self._seek_relative(-10000))
        self.btn_play = QPushButton("播放", objectName="Primary")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setEnabled(False)
        self.btn_fwd = QPushButton("快进 10s")
        self.btn_fwd.clicked.connect(lambda: self._seek_relative(10000))

        self.cur_time = QLabel("00:00", objectName="TimeLabel")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderPressed.connect(lambda: self._seeking(True))
        self.slider.sliderReleased.connect(self._release_seek)
        self.slider.sliderMoved.connect(self._seek_to_slider)
        self.total_time = QLabel("00:00", objectName="TimeLabel")

        vol_label = QLabel("音量", objectName="TimeLabel")
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(70)
        self.vol_slider.setFixedWidth(90)
        self.vol_slider.valueChanged.connect(
            lambda v: self.audio_out.setVolume(v / 100.0)
        )

        for w in (self.btn_open, self.btn_back, self.btn_play, self.btn_fwd,
                  self.slider, self.vol_slider):
            w.setFocusPolicy(Qt.NoFocus)

        lay.addWidget(self.btn_open)
        lay.addSpacing(12)
        lay.addWidget(self.btn_back)
        lay.addWidget(self.btn_play)
        lay.addWidget(self.btn_fwd)
        lay.addSpacing(12)
        lay.addWidget(self.cur_time)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.total_time)
        lay.addSpacing(12)
        lay.addWidget(vol_label)
        lay.addWidget(self.vol_slider)

        # ---- 页面布局 ----
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 20)
        root.setSpacing(12)
        root.addWidget(self.stage, 1)
        root.addWidget(bar)

        # 键盘：空格 播放/暂停，←/→ 快退/快进（仅本页获得焦点时生效）
        for seq, fn in (
            (Qt.Key_Space, self.toggle_play),
            (Qt.Key_Left, lambda: self._seek_relative(-10000)),
            (Qt.Key_Right, lambda: self._seek_relative(10000)),
        ):
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(fn)

    # ---------- 对外接口 ----------
    def load(self, path: str):
        self.empty_hint.hide()
        self.video_widget.show()
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.btn_play.setEnabled(True)
        self.btn_play.setText("暂停")
        self.player.play()
        self.setWindowTitle_safe(path)

    def setWindowTitle_safe(self, path: str):
        win = self.window()
        if hasattr(win, "set_current_file"):
            win.set_current_file(path)

    # ---------- 内部 ----------
    def _open_file(self):
        from app.dialogs import pick_open_file

        path = pick_open_file(
            self, "打开视频",
            "视频文件 (*.mp4 *.mkv *.mov *.webm *.avi *.flv *.wmv *.ts);;所有文件 (*)"
        )
        if path:
            self.load(path)

    def toggle_play(self):
        if self.player.source().isEmpty():
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _seek_relative(self, delta_ms: int):
        pos = self.player.position() + delta_ms
        pos = max(0, min(pos, self.player.duration()))
        self.player.setPosition(pos)

    def _seeking(self, on: bool):
        self._seeking = on

    def _release_seek(self):
        self.player.setPosition(self.slider.value())
        self._seeking = False

    def _seek_to_slider(self, value: int):
        self.player.setPosition(value)
        self.cur_time.setText(_fmt_ms(value))

    def _on_position(self, ms: int):
        if not self._seeking:
            self.slider.blockSignals(True)
            self.slider.setValue(int(ms))
            self.slider.blockSignals(False)
        self.cur_time.setText(_fmt_ms(ms))

    def _on_duration(self, ms: int):
        self.slider.setRange(0, int(ms))
        self.total_time.setText(_fmt_ms(ms))

    def _on_state(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.btn_play.setText("暂停" if playing else "播放")

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.btn_play.setText("播放")

    def _on_error(self, _err, msg: str):
        self.empty_hint.setText(f"无法播放：{msg}" if msg else "无法播放该文件")
        self.empty_hint.show()
        self.btn_play.setEnabled(False)
