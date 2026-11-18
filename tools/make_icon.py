# 生成极简应用图标：深灰圆角方块 + 白色播放三角
import os

from PIL import Image, ImageDraw

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(BASE, "app", "resources", "icon.ico")


def draw_glyph(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 圆角底
    radius = max(2, size // 5)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(31, 35, 41, 255))
    # 白色播放三角（略偏右，视觉居中）
    m = size * 0.30
    cx, cy = size * 0.53, size * 0.5
    w, h = size * 0.30, size * 0.34
    d.polygon(
        [(cx - w * 0.45, cy - h / 2), (cx - w * 0.45, cy + h / 2), (cx + w * 0.62, cy)],
        fill=(255, 255, 255, 255),
    )
    return img


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [draw_glyph(s) for s in sizes]
    imgs[-1].save(OUT, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
    print("icon ->", OUT)


if __name__ == "__main__":
    main()
