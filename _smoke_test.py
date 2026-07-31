# -*- coding: utf-8 -*-
"""无窗口冒烟测试：验证新系统可初始化、主要接口可调用、无运行时异常。"""
import os
import sys
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

FAILED = []


def check(name, fn):
    try:
        fn()
        print(f"[OK]   {name}")
    except Exception:
        print(f"[FAIL] {name}")
        traceback.print_exc()
        FAILED.append(name)


pygame.init()
try:
    pygame.mixer.init()
except Exception as e:
    print("mixer init failed (dummy audio):", e)

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


# --- 打击感 ---
def t_juice():
    from effects.juice import EffectManager
    from systems.camera import Camera
    em = EffectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    cam = Camera()
    img = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(img, (255, 0, 0), (16, 16), 14)
    em.add_death_ghost(img, (100, 100))
    em.add_sparks(120, 120, 1, 0, count=6)
    em.add_muzzle_flash(130, 130, 0.5)
    em.screen_flash((255, 0, 0), 90)
    em.trigger_hitstop(0.05)
    assert em.consume_hitstop(0.016) is True
    for _ in range(30):
        em.update(0.016)
    em.draw_world(screen, cam)
    em.draw_screen(screen, hp_ratio=0.2)


# --- 光照 ---
def t_lighting():
    from systems.lighting import LightingSystem
    from systems.camera import Camera
    ls = LightingSystem()
    cam = Camera()
    for i in range(5):
        ls.set_map(i)
    ls.add_light(400, 300, 330, (255, 238, 198), 1.0)
    ls.add_light(500, 300, 55, (120, 180, 255), 0.6)
    ls.render(screen, cam)


# --- 相机震动 ---
def t_camera():
    from systems.camera import Camera
    cam = Camera()
    cam.shake(0.3, 8)
    rect = pygame.Rect(0, 0, 40, 40)
    for _ in range(40):
        cam.update(rect, 0.016)


# --- 字体 ---
def t_font():
    from ui.drawables import get_font
    f1 = get_font(24)
    f2 = get_font(24)
    assert f1 is f2, "字体缓存未生效"
    fb = get_font(58, bold=True)
    fb.render("强大的敌人逼近", True, (255, 255, 255))


# --- 音频 ---
def t_audio():
    from systems.audio_manager import AudioManager
    am = AudioManager()
    am.play_shoot(); am.play_hit(); am.play_enemy_death()
    am.play_explosion(); am.play_pickup(); am.play_hurt()
    am.play_boss_warning(); am.play_boss_death()
    am.play_level_up(); am.play_ui_click()
    am.duck(0.6, 0.5)
    for _ in range(10):
        am.update(0.016)
    am.start_music(); am.stop_music()
    am.set_music_volume(0.5); am.set_sfx_volume(0.5)
    am.get_music_volume(); am.get_sfx_volume()


# --- HUD / UI 绘制 ---
def t_hud():
    from ui.hud import draw_hud
    from ui.drawables import get_font
    font = get_font(24)
    for _ in range(3):
        draw_hud(screen, font, level=2, experience=30, xp_to_next=100,
                 player_hp=25, player_max_hp=100, elapsed_time=63.2,
                 player_shield=20, player_max_shield=50)


def t_skill_select():
    from ui.skill_select import draw_skill_selection
    from skills import get_random_skills
    from ui.drawables import get_font
    skills = get_random_skills(3)
    for _ in range(3):
        draw_skill_selection(screen, get_font(48), get_font(18),
                             skills, (400, 300))


def t_boss_hud():
    from ui.boss_hud import draw_boss_hp_bar
    from ui.drawables import get_font

    class B:
        hp = 600; max_hp = 1000
        config = {"name": "尸潮之王", "color": (200, 60, 60)}
    b = B()
    for _ in range(5):
        draw_boss_hp_bar(screen, get_font(20), b)


def t_game_over():
    from ui.game_over import draw_game_over_screen
    from ui.drawables import get_font
    for _ in range(3):
        draw_game_over_screen(screen, get_font(48), get_font(24),
                              elapsed_time=125.6, score=4321, level=8,
                              high_score=5000, is_new_record=True)


def t_start_screen():
    from ui.start_screen import draw_start_screen
    from ui.drawables import get_font
    for _ in range(3):
        draw_start_screen(screen, get_font(64), get_font(28), get_font(18))


# --- 主游戏多帧模拟 ---
def t_normal_game():
    from game.normal_game import NormalGame
    g = NormalGame()
    g._init_game()
    for _ in range(10):
        g._update(0.016)
        g._render()
    # 顿帧路径
    g.effects.trigger_hitstop(0.05)
    g._update(0.016)
    # 光源提交
    g._submit_lights()
    g.lighting.render(g.screen, g.camera)
    g.audio.stop_music()


check("effects/juice", t_juice)
check("systems/lighting", t_lighting)
check("systems/camera", t_camera)
check("ui/drawables get_font", t_font)
check("systems/audio_manager", t_audio)
check("ui/hud", t_hud)
check("ui/skill_select", t_skill_select)
check("ui/boss_hud", t_boss_hud)
check("ui/game_over", t_game_over)
check("ui/start_screen", t_start_screen)
check("game/normal_game 10帧模拟", t_normal_game)

print()
if FAILED:
    print("SMOKE_FAIL:", ", ".join(FAILED))
    sys.exit(1)
print("SMOKE_ALL_PASS")
