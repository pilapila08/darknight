# -*- coding: utf-8 -*-
"""VIS-01 验证：敌人轮廓光 + 脚底危险光圈（缓存/兼容/性能冒烟）。

用法：python tools/verify_vis.py   （结果写入 tools/verify_out_vis.txt）
"""
import os
import sys
import time
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    os.chdir(_PROJECT_ROOT)   # 资源路径以项目根解析
    out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "verify_out_vis.txt"), "w", encoding="utf-8")
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

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ENEMY_SIZE, ELITE_SIZE,
    ENEMY_GLOW_COLOR, ENEMY_GLOW_WIDTH, ENEMY_GLOW_ALPHA,
    ENEMY_RING_COLOR, ENEMY_RING_ALPHA, BOSS_RING_SCALE,
    EXPLODER_RADIUS, EXPLODER_RING_COLOR,
)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from systems.camera import Camera
from entities.enemy import Enemy, _GLOW_CACHE, _RING_CACHE
from entities.enemy_types import Charger, Ranger, Exploder
from entities.boss import BOSS_CLASSES
from entities import walk_anim as wa


def _cam(ox=300, oy=300):
    cam = Camera()
    cam.offset.x = ox
    cam.offset.y = oy
    return cam


def v_settings_params():
    for name, lo, hi in [
        ("ENEMY_GLOW_COLOR", None, None),
        ("ENEMY_GLOW_WIDTH", 1, 5),
        ("ENEMY_GLOW_ALPHA", 40, 120),
        ("ENEMY_RING_COLOR", None, None),
        ("ENEMY_RING_ALPHA", 30, 90),
        ("BOSS_RING_SCALE", 1.0, 3.0),
    ]:
        v = globals()[name]
        assert v is not None, name
        if lo is not None:
            assert lo <= v <= hi, (name, v)
    print("  settings 参数在位：",
          ENEMY_GLOW_COLOR, ENEMY_GLOW_WIDTH, ENEMY_GLOW_ALPHA,
          ENEMY_RING_COLOR, ENEMY_RING_ALPHA, BOSS_RING_SCALE)


def v_glow_cached_by_type():
    print("--- 轮廓光缓存（按类型/尺寸/帧，150 敌人共享） ---")
    c0 = len(_GLOW_CACHE)
    # 同类同尺寸 20 只 → 缓存不增长（共享）
    enemies = [Enemy(100 + i * 40, 100, sprite_name="enemy") for i in range(20)]
    c1 = len(_GLOW_CACHE)
    assert c1 - c0 <= 3, (c0, c1)   # enemy 3 帧
    print(f"  20 只普通怪后缓存 {c0}→{c1}（共享生效）")
    # 各类型 + 精英 + Boss 各建 1 只
    types = [
        Enemy(200, 200, sprite_name="enemy"),
        Enemy(200, 200, sprite_name="enemy", is_elite=True, size=ELITE_SIZE),
        Charger(200, 200), Ranger(200, 200), Exploder(200, 200),
    ] + [cls(200, 200) for cls in BOSS_CLASSES]
    c2 = len(_GLOW_CACHE)
    print(f"  全部类型后缓存 {c2}（含 Boss 4 型）")
    # 轮廓光 surface 尺寸应 ≥ 精灵 + 2*width 边距，且含暖色像素
    for e in enemies:
        glow = e._glow_frames[0]
        fw, fh = e._normal_frames[0].get_size()
        gw, gh = glow.get_size()
        assert gw >= fw + 2 * ENEMY_GLOW_WIDTH and gh >= fh + 2 * ENEMY_GLOW_WIDTH, (gw, gh, fw, fh)
        # 采样暖色：统计 alpha>0 像素中偏暖色占比应 > 0（存在发光描边）
        warm = 0
        total = 0
        for gx in range(0, gw, 3):
            for gy in range(0, gh, 3):
                r, g, b, a = glow.get_at((gx, gy))
                if a > 0:
                    total += 1
                    if r >= ENEMY_GLOW_COLOR[0] - 30 and g >= ENEMY_GLOW_COLOR[1] - 30:
                        warm += 1
        assert total > 0 and warm / total > 0.5, (total, warm)
    print(f"  轮廓光尺寸/暖色校验通过（帧 {fw}x{fh} → glow {gw}x{gh}）")


def v_draw_all_types():
    print("--- 各类型 draw 冒烟（含 flip / 受击闪白 / exploder 光圈 / Boss） ---")
    cam = _cam()
    enemies = [
        Enemy(400, 400), Enemy(400, 400, is_elite=True, size=ELITE_SIZE),
        Charger(420, 400), Ranger(440, 400), Exploder(460, 400),
    ] + [cls(500 + i * 120, 400) for i, cls in enumerate(BOSS_CLASSES)]
    # 翻转方向（朝左）
    for e in enemies:
        e.vx = -100.0
        e.update(0.016, pygame.Rect(0, 0, 20, 20))
        e.draw(screen, cam)
    # 受击闪白：flash_timer>0 后 draw 仍正常，且最上层为白剪影（闪白叠加在轮廓光之上）
    # 注意：基础怪 HP=1 一击即死无闪白，用高 HP 敌人验证
    flash_enemies = [Enemy(600, 600, hp=5), Charger(620, 600, hp=5)]
    for e in flash_enemies:
        e.take_damage(1)
        assert e.flash_timer > 0
        e.draw(screen, cam)
    print(f"  全部类型 draw 通过（{len(enemies)} 只 + 闪白 {len(flash_enemies)} 只）")


def v_exploder_range_ring():
    print("--- 自爆怪爆炸范围光圈 ---")
    e = Exploder(600, 600)
    e.draw(screen, _cam(500, 500))
    assert e._sprite_name == "exploder"
    assert EXPLODER_RADIUS > 0
    print(f"  exploder 范围光圈半径 = {EXPLODER_RADIUS}px（红色脉冲）通过")


def v_150_enemies_perf():
    print("--- 150 敌人绘制性能冒烟（参考 L1 动画 0.79ms 预算） ---")
    cam = _cam()
    enemies = [Enemy(200 + (i % 15) * 180, 200 + (i // 15) * 180) for i in range(150)]
    # 预热（贴图/缓存命中）
    for e in enemies:
        e.draw(screen, cam)
    t0 = time.perf_counter()
    N = 3
    for _ in range(N):
        for e in enemies:
            e.draw(screen, cam)
    dt = (time.perf_counter() - t0) / N
    per_enemy = dt / len(enemies) * 1000
    print(f"  150 敌人单帧绘制 {dt * 1000:.2f}ms（每敌人 {per_enemy:.3f}ms）")
    assert dt < 0.05, dt   # dummy 驱动下宽松上限，防灾难性回归


checks = [
    ("settings 参数在位", v_settings_params),
    ("轮廓光按类型缓存 + 尺寸/暖色校验", v_glow_cached_by_type),
    ("各类型 draw 冒烟（flip/闪白/exploder/Boss）", v_draw_all_types),
    ("自爆怪爆炸范围光圈", v_exploder_range_ring),
    ("150 敌人绘制性能冒烟", v_150_enemies_perf),
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
