# -*- coding: utf-8 -*-
"""地图纹理无缝化预处理（DN-ENG-VIS-01 任务 A）。

对 assets/maps/ 5 张 256×256 瓦片做边缘 wrap 混合：
把左/右、上/下边缘各 band 像素带宽做渐隐加权融合，使平铺时边缘像素连续
（右边缘 ≈ 左边缘、下边缘 ≈ 上边缘），消除棋盘式平铺的直线接缝。

- 原始文件先备份到 assets/maps/_backup_orig/（仅首次，幂等）。
- 处理后直接覆盖 assets/maps/ 同名文件（map_manager 读取路径不变）。
- 输出每张图处理前后的边缘像素差（右-左、下-上），供 verify 断言。

用法：python tools/make_seamless.py
"""
import os
import sys

import pygame

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(_PROJECT_ROOT, "assets", "maps")
BACKUP_DIR = os.path.join(MAPS_DIR, "_backup_orig")

FILES = [
    "bleak_graveyard_256.png",
    "corrupted_swamp_256.png",
    "shadow_court_256.png",
    "iron_ruins_256.png",
    "void_rift_256.png",
]

BAND = 14  # 边缘融合带宽（px），建议 12-16


def _edge_diff(surf):
    """右边缘 vs 左边缘、下边缘 vs 上边缘的平均绝对像素差。"""
    w, h = surf.get_size()
    hdiff = sum(
        abs(surf.get_at((w - 1, y))[i] - surf.get_at((0, y))[i])
        for y in range(h) for i in range(3)
    ) / (h * 3)
    vdiff = sum(
        abs(surf.get_at((x, h - 1))[i] - surf.get_at((x, 0))[i])
        for x in range(w) for i in range(3)
    ) / (w * 3)
    return hdiff, vdiff


def _blend_edge(surf, band):
    """水平 + 垂直边缘渐隐加权融合（原地修改）。"""
    w, h = surf.get_size()

    # 水平：右边缘 ← 左边缘（含带内渐变），左边缘向带内右侧采样渐变
    for y in range(h):
        for x in range(band):
            t = x / band  # 0 在最边缘 → 1 在带内边界
            left = surf.get_at((x, y))
            right = surf.get_at((w - band + x, y))
            # 左带：向带内右侧内容渐变；右带镜像，保证右边缘 == 左边缘
            mix = tuple(int(left[i] * (1 - t) + right[i] * t) for i in range(3))
            surf.set_at((x, y), mix + (255,))
            surf.set_at((w - 1 - x, y), mix + (255,))

    # 垂直：下边缘 ← 上边缘（同理）
    for x in range(w):
        for y in range(band):
            t = y / band
            top = surf.get_at((x, y))
            bot = surf.get_at((x, h - band + y))
            mix = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
            surf.set_at((x, y), mix + (255,))
            surf.set_at((x, h - 1 - y), mix + (255,))


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((64, 64))

    if not os.path.isdir(MAPS_DIR):
        print(f"[ERROR] 找不到 {MAPS_DIR}")
        return 1
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for fname in FILES:
        path = os.path.join(MAPS_DIR, fname)
        if not os.path.isfile(path):
            print(f"[SKIP] 缺失 {fname}")
            continue
        # 备份（仅首次）
        bak = os.path.join(BACKUP_DIR, fname)
        if not os.path.isfile(bak):
            with open(path, "rb") as src, open(bak, "wb") as dst:
                dst.write(src.read())
            print(f"[BAK ] {fname} -> {os.path.relpath(bak, MAPS_DIR)}")

        surf = pygame.image.load(path).convert()
        before_h, before_v = _edge_diff(surf)
        _blend_edge(surf, BAND)
        after_h, after_v = _edge_diff(surf)
        pygame.image.save(surf, path)
        print(f"[OK  ] {fname}: 边差 水平 {before_h:.2f}→{after_h:.2f} | "
              f"垂直 {before_v:.2f}→{after_v:.2f}")

    print("MAKE_SEAMLESS_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
