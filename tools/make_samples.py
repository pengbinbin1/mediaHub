# 生成各模块测试样例：图片 / TXT / DOCX / PDF / MP4
import os

import numpy as np
from PIL import Image, ImageDraw
from docx import Document
import pymupdf as fitz

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(BASE, "samples")


def make_images():
    os.makedirs(OUT, exist_ok=True)
    # 渐变
    w, h = 800, 600
    grad = np.zeros((h, w, 3), np.uint8)
    for x in range(w):
        grad[:, x] = (int(255 * x / w), int(255 * x / w * 0.6), 220 - int(180 * x / w))
    Image.fromarray(grad).save(os.path.join(OUT, "渐变.png"))
    # 几何
    img = Image.new("RGB", (640, 480), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.ellipse([80, 80, 300, 300], fill=(31, 35, 41))
    d.rectangle([340, 120, 560, 340], outline=(31, 35, 41), width=8)
    d.line([60, 420, 580, 420], fill=(180, 184, 190), width=4)
    img.save(os.path.join(OUT, "几何.jpg"))
    # 小 bmp
    Image.new("RGB", (320, 240), (240, 242, 245)).save(os.path.join(OUT, "纯色.bmp"))


def make_txt():
    text = (
        "极简媒体中心 · TXT 测试\n"
        "====================\n"
        "1. 这是一段中文测试文本\n"
        "2. 用于验证编码与编辑保存\n"
        "\n"
        "Try editing me, then press Ctrl+S.\n"
    )
    with open(os.path.join(OUT, "笔记.txt"), "w", encoding="utf-8") as f:
        f.write(text)


def make_docx():
    doc = Document()
    doc.add_heading("极简媒体中心 使用说明", 1)
    p = doc.add_paragraph()
    p.add_run("这一段包含 ").bold = True
    r = p.add_run("粗体、")
    r.bold = True
    r2 = p.add_run("斜体 ")
    r2.italic = True
    p.add_run("和下划线内容。").underline = True
    doc.add_heading("基本功能", 2)
    doc.add_paragraph("视频播放：播放 / 暂停 / 快进 / 快退")
    doc.add_paragraph("图片查看：上一张 / 下一张 / 旋转 / 缩放", style="List Bullet")
    doc.add_paragraph("文件浏览：全盘符树形浏览", style="List Bullet")
    doc.add_paragraph("文档编辑：TXT / Word", style="List Bullet")
    doc.add_paragraph("打开应用")
    doc.add_paragraph("双击桌面「极简媒体中心」快捷方式", style="List Number")
    doc.add_paragraph("拖入任意文件即可自动识别打开", style="List Number")
    doc.save(os.path.join(OUT, "示例文档.docx"))


def make_pdf():
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page()  # A4 595x842
        page.insert_text((72, 96), f"极简媒体中心 · PDF 测试 第 {i + 1} 页", fontname="china-s", fontsize=20)
        page.insert_text((72, 140), "这是一页用于验证 PDF 查看 / 翻页 / 缩放的测试内容。", fontname="china-s", fontsize=13)
        for j in range(20):
            page.insert_text((72, 180 + j * 22), f"行 {j + 1}: " + "极简干净的设计让人专注内容本身。", fontname="china-s", fontsize=11)
        page.draw_rect(fitz.Rect(60, 60, 535, 780), color=(0.7, 0.7, 0.7), width=0.8)
    doc.save(os.path.join(OUT, "示例文档.pdf"))


def make_mp4():
    import imageio.v2 as imageio
    path = os.path.join(OUT, "演示.mp4")
    w, h, fps, secs = 640, 360, 12, 8
    writer = imageio.get_writer(path, fps=fps, codec="libx264", pixelformat="yuv420p", macro_block_size=None)
    for i in range(fps * secs):
        frame = np.zeros((h, w, 3), np.uint8)
        x = (np.arange(w) + i * 10) % w
        frame[:, :, 0] = (x * 255 // w).astype(np.uint8)
        frame[:, :, 1] = 120
        frame[:, :, 2] = (255 - x * 255 // w).astype(np.uint8)
        pos = (i * 12) % (w - 80)
        frame[150:230, pos:pos + 80] = 255  # 移动白色方块
        t = i / fps
        writer.append_data(frame)
    writer.close()
    print("mp4 ->", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    make_images()
    make_txt()
    make_docx()
    make_pdf()
    make_mp4()
    print("samples ready ->", OUT)


if __name__ == "__main__":
    main()
