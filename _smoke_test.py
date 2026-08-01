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


# --- R5 角色系统 ---
def t_character_select():
    from ui.character_select import (
        draw_character_select, build_character_select_layout,
        handle_character_select_input,
    )
    from ui.drawables import get_font
    from characters import CHARACTERS
    from game.state import GameState
    # 四角色数值覆盖可实例化
    assert set(CHARACTERS.keys()) == {"default", "gunslinger", "vanguard", "wayfarer"}
    GameState("gunslinger"); GameState("vanguard"); GameState("wayfarer")
    meta = {"total_kills": 100, "victories": 2, "high_score": 500, "total_runs": 3,
            "best_run_kills": 60}
    unlocks = {"gunslinger": True, "vanguard": False, "wayfarer": False}
    card_rects, start_btn, back_btn = build_character_select_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    for _ in range(3):
        draw_character_select(screen, get_font(48), get_font(24), get_font(14),
                              "gunslinger", meta, unlocks, card_rects, start_btn, back_btn)
    ev = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
    # 解锁顺序仅 [default, gunslinger]（vanguard/wayfarer 锁定）→ 右移选中 gunslinger
    assert handle_character_select_input(ev, card_rects, start_btn, back_btn,
                                         "default", unlocks) == "select:gunslinger"
    # 从 gunslinger 右移回绕到 default
    assert handle_character_select_input(ev, card_rects, start_btn, back_btn,
                                         "gunslinger", unlocks) == "select:default"
    # 数字键 1-4：锁定角色不可选中
    ev2 = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_3})
    assert handle_character_select_input(ev2, card_rects, start_btn, back_btn,
                                         "default", unlocks) is None


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


# --- L1 程序动画 ---
def t_walk_anim():
    from entities.walk_anim import (
        bob_offset, squash, flip_for_direction, apply_walk_anim,
        compute_walk_frame, resolve_params, bob_phase,
    )
    from entities.enemy import Enemy
    from entities.boss import CorpseKing
    from entities import Player
    from systems.camera import Camera
    from ui.drawables import get_font
    cam = Camera()

    # 纯函数：bob 半波（phase=0 触地 dy=0；phase=π 最高点 dy=-amp，负=向上）
    assert bob_offset(0.0, 0.0, 4.0, 1.0) == 0
    assert bob_offset(0.5, 0.0, 4.0, 1.0) == -4

    # squash：触地（cos=1）水平加宽/垂直压缩；最高点（cos=-1）反向
    base = pygame.Surface((28, 28), pygame.SRCALPHA)
    sq_ground = squash(base, 0.0, 0.0, 0.10, freq=1.0)
    assert sq_ground.get_width() >= 28 and sq_ground.get_height() <= 28
    sq_peak = squash(base, 0.5, 0.0, 0.10, freq=1.0)
    assert sq_peak.get_width() <= 28 and sq_peak.get_height() >= 28

    # flip：vx<-5 镜像，vx>=0 零拷贝
    assert flip_for_direction(base, -100.0) is not base
    assert flip_for_direction(base, 10.0) is base

    # 相位错开：不同 id 相位不同
    assert bob_phase(1) != bob_phase(2)

    # 组合入口 + 绘制帧
    p = resolve_params("player")
    assert isinstance(apply_walk_anim(base, 0.25, 1, 100.0, p), pygame.Surface)
    frame = compute_walk_frame(base, 0.25, 1, 100.0, p)
    assert 0.0 <= frame.shadow_scale <= 2.0

    # 实体接入：玩家 / 敌人 / Boss 均可用 L1 draw
    Player().draw(screen, cam)
    Enemy(100, 100).draw(screen, cam)
    CorpseKing(200, 200).draw(screen, cam)
    CorpseKing(200, 200).draw_hp_bar_bg(screen, get_font(16), cam)


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
check("r5/character_select", t_character_select)
check("game/normal_game 10帧模拟", t_normal_game)
check("entities/walk_anim L1程序动画", t_walk_anim)

print()
if FAILED:
    print("SMOKE_FAIL:", ", ".join(FAILED))
    sys.exit(1)
print("SMOKE_ALL_PASS")
