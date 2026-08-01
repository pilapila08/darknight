# -*- coding: utf-8 -*-
"""MAP-01 验证：AI 地图纹理接入（加载/平铺/回退/绘制/过渡）。

用法：python tools/verify_map.py   （结果写入 tools/verify_out_map.txt）
"""
import os
import sys
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    # 从项目根运行，保证 _resource_path("assets/maps") 解析正确
    os.chdir(_PROJECT_ROOT)
    out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "verify_out_map.txt"), "w", encoding="utf-8")
    sys.stdout = out
    sys.stderr = out

FAILED = []


def check(name, fn):
    try:
        fn()
        print(f"[OK]   {name}")
    except BaseException:
        print(f"[FAIL] {name}")
        traceback.print_exc()
        FAILED.append(name)


import pygame
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from systems.map_manager import MapManager, GROUND_TEXTURE_FILES
from systems.camera import Camera


def _camera(ox=0, oy=0):
    cam = Camera()
    cam.offset.x = ox
    cam.offset.y = oy
    return cam


def v_textures_loaded():
    print("--- 纹理预加载 ---")
    mgr = MapManager()
    for idx, fname in enumerate(GROUND_TEXTURE_FILES):
        tex = mgr._ground_textures[idx]
        assert tex is not None, f"纹理未加载: {fname}"
        w, h = tex.get_size()
        print(f"  {idx} {fname}: {w}x{h}")
        assert (w, h) == (256, 256), (fname, w, h)


def v_texture_seamless():
    """make_seamless 断言：瓦片右边缘 vs 左边缘、下边缘 vs 上边缘像素差应极小。"""
    print("--- 纹理无缝断言（边缘像素差应 ≈ 0） ---")
    mgr = MapManager()
    for idx, fname in enumerate(GROUND_TEXTURE_FILES):
        tex = mgr._ground_textures[idx]
        assert tex is not None, fname
        w, h = tex.get_size()
        hdiff = sum(abs(tex.get_at((w - 1, y))[i] - tex.get_at((0, y))[i])
                    for y in range(h) for i in range(3)) / (h * 3)
        vdiff = sum(abs(tex.get_at((x, h - 1))[i] - tex.get_at((x, 0))[i])
                    for x in range(w) for i in range(3)) / (w * 3)
        print(f"  idx{idx} {fname}: 水平 {hdiff:.2f} 垂直 {vdiff:.2f}")
        assert hdiff < 6.0, (fname, hdiff)
        assert vdiff < 6.0, (fname, vdiff)


def v_chunk_texture_tiled():
    print("--- 整图预渲染（纹理交错平铺，逐像素与源纹理比对） ---")
    mgr = MapManager()
    for idx in range(len(GROUND_TEXTURE_FILES)):
        mgr.switch_to_map(idx)
        mgr._ground_chunk = None
        mgr._ground_map_index = -1
        chunk = mgr._build_ground_chunk()
        w, h = chunk.get_size()
        assert (w, h) == (MAP_WIDTH, MAP_HEIGHT), (w, h)
        tex = mgr._ground_textures[idx]
        tw, th = tex.get_size()
        half = tw // 2
        # 采样多个世界坐标：奇数行偏移半瓦片（用取模处理边界）
        mismatches = 0
        for (wx, wy) in [(0, 0), (255, 255), (256, 0), (1280, 720),
                         (1500, 1125), (2999, 2249), (100, 2200), (10, 300)]:
            offset = half if (wy // th) % 2 == 1 else 0
            expected = tex.get_at(((wx + offset) % tw, wy % th))
            actual = chunk.get_at((wx, wy))
            if actual != expected:
                mismatches += 1
                print(f"    idx{idx} ({wx},{wy}) offset={offset} actual={actual} expected={expected}")
        assert mismatches == 0, f"idx{idx} 纹理交错平铺像素不匹配 x{mismatches}"
        # 断言交错确实发生：奇数行 x=0 处应等于源纹理 (half, 0)，而非 (0, 0)
        odd_px = chunk.get_at((0, th))          # 第 1 行（奇数行）
        assert odd_px == tex.get_at((half, 0)), f"idx{idx} 奇数行未偏移"
        even_px = chunk.get_at((0, 0))          # 第 0 行（偶数行）
        assert even_px == tex.get_at((0, 0)), f"idx{idx} 偶数行不应偏移"
        print(f"  idx{idx} 整图 {w}x{h} 交错平铺校验通过（奇数行偏移 {half}px 生效）")


def v_chunk_fallback():
    print("--- 回退路径（纹理缺失 → 程序化棋盘格整图平铺） ---")
    mgr = MapManager()
    for idx in range(len(GROUND_TEXTURE_FILES)):
        mgr.switch_to_map(idx)
        mgr._ground_textures[idx] = None   # 模拟文件缺失/损坏
        mgr._ground_chunk = None
        mgr._ground_map_index = -1
        chunk = mgr._build_ground_chunk()
        w, h = chunk.get_size()
        assert (w, h) == (MAP_WIDTH, MAP_HEIGHT), (w, h)
        # 棋盘格应非全黑/空白：采样 64 点统计不同色
        colors = set()
        for i in range(64):
            colors.add(tuple(chunk.get_at((i * 47 % MAP_WIDTH, i * 31 % MAP_HEIGHT))))
        assert len(colors) >= 2, f"idx{idx} 回退地面为空白"
        print(f"  idx{idx} 回退整图 {w}x{h} 通过（{len(colors)} 种采样色）")


def v_draw_all_maps():
    print("--- 逐图 draw_background（含相机偏移 + 场景/暗角/机制叠加） ---")
    mgr = MapManager()
    for idx in range(len(GROUND_TEXTURE_FILES)):
        mgr.switch_to_map(idx)
        # 强制重建
        mgr._ground_chunk = None
        mgr._ground_map_index = -1
        for (ox, oy) in [(0, 0), (500, 300), (1500, 1125), (2500, 2000)]:
            mgr.draw_background(screen, _camera(ox, oy))
        # 屏幕非空白
        px = screen.get_at((10, 10))
        assert px != (0, 0, 0, 255), f"idx{idx} 屏幕左上全黑"
        print(f"  idx{idx} 绘制通过（4 相机位，左上像素={px}）")


def v_transition_compat():
    mgr = MapManager()
    mgr.switch_to_map(2)
    assert mgr.transition_active is True
    assert mgr.transition_timer > 0
    assert mgr.current_map_index == 2
    mgr.update(1.0, pygame.Rect(100, 100, 20, 20), [])
    assert mgr.transition_active is True
    mgr.update(2.0, pygame.Rect(100, 100, 20, 20), [])
    assert mgr.transition_active is False


checks = [
    ("纹理预加载 5/5", v_textures_loaded),
    ("纹理无缝断言（边缘像素差≈0）", v_texture_seamless),
    ("整图预渲染·纹理交错平铺逐像素校验", v_chunk_texture_tiled),
    ("回退路径·程序化棋盘格整图", v_chunk_fallback),
    ("逐图 draw_background 绘制", v_draw_all_maps),
    ("地图切换过渡兼容", v_transition_compat),
]


def _main():
    for name, fn in checks:
        check(name, fn)
    print()
    if FAILED:
        print("VERIFY_FAIL:", ", ".join(FAILED))
        rc = 1
    else:
        print("VERIFY_ALL_PASS")
        rc = 0
    out.close()
    return rc


if __name__ == "__main__":
    sys.exit(_main())
out.close()
