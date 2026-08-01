# -*- coding: utf-8 -*-
"""QOL 验证：视野调亮参数 + 音效合成升级（时长抽查）。

用法：python tools/verify_qol.py   （结果写入 tools/verify_out_qol.txt）
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
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    out = open("verify_out_qol.txt", "w", encoding="utf-8")
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

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from systems.lighting import (
    AMBIENT_BY_MAP, LIGHT_AMBIENT_BRIGHTNESS, LightingSystem,
    PLAYER_LIGHT_RADIUS, PLAYER_LIGHT_COLOR,
)


def v_ambient_brightened():
    print("--- 各图环境光新值（QOL 调亮） ---")
    names = ["荒芜墓地", "腐化沼泽", "暗影庭院", "钢铁废墟", "虚空裂缝"]
    for i, (name, c) in enumerate(zip(names, AMBIENT_BY_MAP)):
        print(f"  {i} {name}: {c}  avg={sum(c)//3}")
        assert all(140 <= v <= 190 for v in c), (name, c)
    # 保留色调差异：墓地主蓝、沼泽主绿、庭院主紫、废墟主暖、虚空主紫暗
    r0, g0, b0 = AMBIENT_BY_MAP[0]
    assert b0 > r0, "墓地应偏冷蓝"
    r1, g1, b1 = AMBIENT_BY_MAP[1]
    assert g1 > r1 and g1 > b1, "沼泽应偏绿"
    r4, g4, b4 = AMBIENT_BY_MAP[4]
    assert b4 > r4 and sum(AMBIENT_BY_MAP[4]) <= sum(AMBIENT_BY_MAP[0]), "虚空应最暗"
    assert LIGHT_AMBIENT_BRIGHTNESS >= 1.0
    assert PLAYER_LIGHT_RADIUS >= 360, PLAYER_LIGHT_RADIUS  # 330→400


def v_lighting_render():
    ls = LightingSystem()
    cam = _make_cam()
    ls.set_map(0)
    ls.add_light(400, 300, 200, (255, 255, 255), 1.0)
    ls.render(screen, cam)
    ls.set_map(4)
    ls.render(screen, cam)


def _make_cam():
    from systems.camera import Camera
    cam = Camera()
    cam.offset.x = 0
    cam.offset.y = 0
    return cam


def v_audio_synthesis_durations():
    from systems.audio_manager import AudioManager, SAMPLE_RATE
    am = AudioManager()
    expected = {
        "_shoot": (0.055, 0.085),        # 0.07
        "_hit_variants": (0.05, 0.075),  # 0.06
        "_explosion": (0.45, 0.55),      # 0.5
        "_pickup": (0.09, 0.13),         # 0.11（两音）
        "_ui_click": (0.055, 0.085),     # 0.07
    }
    print("--- 音效时长抽查（采样率对齐后应≈设计时长） ---")
    for attr, (lo, hi) in expected.items():
        obj = getattr(am, attr)
        sounds = obj if isinstance(obj, list) else [obj]
        for s in sounds:
            length = s.get_length()
            print(f"  {attr}: {length:.3f}s")
            assert lo <= length <= hi, (attr, length)
    print(f"  SAMPLE_RATE = {SAMPLE_RATE}")


def v_audio_playable():
    am = _build_am()
    am.play_shoot(); am.play_hit(); am.play_enemy_death()
    am.play_explosion(); am.play_pickup(); am.play_hurt()
    am.play_boss_warning(); am.play_boss_death()
    am.play_level_up(); am.play_ui_click()
    for _ in range(10):
        am.update(0.016)


def _build_am():
    from systems.audio_manager import AudioManager
    return AudioManager()


checks = [
    ("QOL 环境光调亮 + 色调差异保留", v_ambient_brightened),
    ("QOL 光照渲染冒烟", v_lighting_render),
    ("QOL 音效合成时长抽查", v_audio_synthesis_durations),
    ("QOL 音效可播放", v_audio_playable),
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
