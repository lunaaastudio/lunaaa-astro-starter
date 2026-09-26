#!/usr/bin/env python3
"""
make_book_cover.py — 统一生成 Library 书封封面

目的：保证后续每本新增书籍的封面背景与其他封面**完全一致**，
不再手工调参。背景参数从 Flow 原版采样并固化于此，是唯一权威来源。

用法：
    python scripts/make_book_cover.py <源图路径> <书名slug> [--height 405]

示例：
    # 生成封面到 public/library-<slug>.jpg
    python scripts/make_book_cover.py "C:/path/to/cover.jpg" thinking-in-systems

    # 指定书封高度（默认 405，与其他书封一致）
    python scripts/make_book_cover.py "C:/path/cover.jpg" my-book --height 380

依赖：
    pip install Pillow

输出：
    public/library-<slug>.jpg  (860x500, 约 35-60KB)

背景参数（与 library-flow.jpg 实测一致，勿改）：
    - 底色   RGB(146, 225, 240)
    - 环线   RGB(136, 215, 230)，间距 34px，宽 1px（2x 超采样后缩放）
    - 环线半径带 ±2px 随机抖动，模拟手绘有机感
    - 书封高度 405px，垂直居中，带高斯模糊投影
"""

from PIL import Image, ImageDraw, ImageFilter
import argparse
import os
import random
import sys

# ---------------------------------------------------------------------------
# 权威背景参数（从 library-flow.jpg 实测提取，保持一致）
# ---------------------------------------------------------------------------
CANVAS_W = 860
CANVAS_H = 500
BG_COLOR = (146, 225, 240)      # 底色
RING_COLOR = (136, 215, 230)    # 环线颜色
RING_SPACING = 34               # 环线间距（px）
RING_START = 14                 # 起始半径
RING_END = 700                  # 结束半径
RING_WIDTH = 1                  # 线宽（px，在 2x 画布上为 2px）
RING_JITTER = 2.0               # 半径抖动幅度（px）
SUPERSAMPLE = 2                 # 超采样倍数
BLUR_SIGMA = 0.6                # 线条模糊（2x 画布上的 sigma）
BOOK_HEIGHT = 405               # 书封目标高度（px）
SHADOW_BLUR = 14                # 投影模糊半径
SHADOW_COLOR = (20, 60, 80)     # 投影颜色
SHADOW_ALPHA = 90               # 投影透明度
JPEG_QUALITY = 86               # 输出质量


def make_background() -> Image.Image:
    """生成与其他封面一致的圆环背景。"""
    cx, cy = CANVAS_W // 2, CANVAS_H // 2
    S = SUPERSAMPLE
    big = Image.new('RGB', (CANVAS_W * S, CANVAS_H * S), BG_COLOR)
    d = ImageDraw.Draw(big)
    for base in range(RING_START, RING_END, RING_SPACING):
        rr = base + random.uniform(-RING_JITTER, RING_JITTER)
        d.ellipse(
            [(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S],
            outline=RING_COLOR,
            width=RING_WIDTH * S,
        )
    big = big.filter(ImageFilter.GaussianBlur(BLUR_SIGMA * S))
    return big.convert('RGB').resize((CANVAS_W, CANVAS_H), Image.LANCZOS)


def crop_screenshot_border(img: Image.Image) -> Image.Image:
    """裁掉截图自带的灰色边框（如果存在）。

    检测边缘连续的灰像素（r≈g≈b 且 150~230），逐个方向内缩。
    """
    w, h = img.size

    def is_gray(p):
        r, g, b = p[:3]
        return abs(r - g) < 12 and abs(g - b) < 12 and 150 < r < 230

    left = 0
    while left < 80 and is_gray(img.getpixel((left, h // 2))):
        left += 1
    right = 0
    while right < 80 and is_gray(img.getpixel((w - 1 - right, h // 2))):
        right += 1
    top = 0
    while top < 80 and is_gray(img.getpixel((w // 2, top))):
        top += 1
    bottom = 0
    while bottom < 80 and is_gray(img.getpixel((w // 2, h - 1 - bottom))):
        bottom += 1

    return img.crop((left, top, w - right, h - bottom))


def compose(source_path: str, slug: str, book_height: int = BOOK_HEIGHT) -> str:
    """把源书封合成为统一背景的封面，保存到 public/。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(root, 'public')
    os.makedirs(public_dir, exist_ok=True)

    # 1) 背景
    bg = make_background()

    # 2) 书封源图（自动裁截图边框）
    src = Image.open(source_path).convert('RGB')
    book = crop_screenshot_border(src)
    bw, bh = book.size
    tw = round(bw * book_height / bh)
    book_scaled = book.resize((tw, book_height), Image.LANCZOS)
    bx, by = (CANVAS_W - tw) // 2, (CANVAS_H - book_height) // 2

    # 3) 柔和投影
    shadow = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle(
        [bx - 3, by + 3, bx + tw + 3, by + book_height + 12],
        fill=SHADOW_COLOR + (SHADOW_ALPHA,),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))

    # 4) 合成
    out = Image.alpha_composite(bg.convert('RGBA'), shadow)
    out.paste(book_scaled, (bx, by))
    out = out.convert('RGB')

    out_path = os.path.join(public_dir, f'library-{slug}.jpg')
    out.save(out_path, 'JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out_path


def main():
    parser = argparse.ArgumentParser(description='生成统一背景的 Library 书封封面')
    parser.add_argument('source', help='书封源图路径（可含截图边框，会自动裁掉）')
    parser.add_argument('slug', help='书名 slug（输出为 library-<slug>.jpg）')
    parser.add_argument('--height', type=int, default=BOOK_HEIGHT,
                        help=f'书封目标高度（默认 {BOOK_HEIGHT}px）')
    parser.add_argument('--seed', type=int, default=None,
                        help='随机种子（复现相同背景纹理）')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    else:
        random.seed(hash(args.slug) % (2 ** 32))  # 同 slug 稳定复现

    if not os.path.exists(args.source):
        print(f'错误：源图不存在：{args.source}', file=sys.stderr)
        sys.exit(1)

    out_path = compose(args.source, args.slug, args.height)
    print(f'已生成：{out_path}  ({os.path.getsize(out_path) // 1024} KB)')


if __name__ == '__main__':
    main()
