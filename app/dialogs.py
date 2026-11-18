# dialogs.py — 文件对话框：默认打开用户主目录，并记住上次使用的目录
import os

from PySide6.QtWidgets import QFileDialog

_state = {"last_dir": os.path.expanduser("~")}


def pick_open_file(parent, title: str, filters: str) -> str:
    """打开文件选择框；返回所选路径（取消则返回空串）。"""
    path, _ = QFileDialog.getOpenFileName(parent, title, _state["last_dir"], filters)
    if path:
        _remember(path)
    return path


def pick_open_files(parent, title: str, filters: str) -> list:
    """打开可多选的文件选择框；返回所选路径列表（取消则返回空列表）。"""
    paths, _ = QFileDialog.getOpenFileNames(parent, title, _state["last_dir"], filters)
    if paths:
        _remember(paths[0])
    return paths


def pick_save_file(parent, title: str, default_name: str, filters: str) -> str:
    """打开保存对话框；返回所选路径（取消则返回空串）。"""
    start = os.path.join(_state["last_dir"], default_name)
    path, _ = QFileDialog.getSaveFileName(parent, title, start, filters)
    if path:
        _remember(path)
    return path


def _remember(path: str):
    d = os.path.dirname(path)
    if os.path.isdir(d):
        _state["last_dir"] = d
