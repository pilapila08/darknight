# -*- coding: utf-8 -*-
"""测试模式重构验收（DN-ENG-TEST-R1）+ 沙盒化验收（DN-ENG-TEST-R2）。

无窗口（dummy 视频驱动）。验证：
R1：7 敌种快速生成 / 自定义敌人 7 类型 / 4 Boss+清屏 / 自动生成单一源 /
    16 技能 / TEXTINPUT / 渲染 / 结构回归 / 玩家控制保留
R2（沙盒化）：升级开关默认关（击杀不升级不冻结）、开启后升级恢复、
    重置按钮 → _restart 状态归零、布局无重叠

用法：venv/Scripts/python.exe tools/verify_test_mode.py
输出：tools/verify_out_test_r1.txt
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
    out = open(os.path.join(_PROJECT_ROOT, "tools", "verify_out_test_r1.txt"), "w", encoding="utf-8")
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

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_MAX_HP
pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from game.test_game import TestGame
from game.test_mode import TestInputField, ENEMY_TYPE_DEFS
from entities import Enemy
from entities.enemy_types import Wraith, Warlock
from entities.boss import Boss, BOSS_CLASSES, BOSS_CONFIGS
from skills import SKILL_POOL
from ui.test_panel import build_test_layout


def reset():
    """复用单实例并完全重置（_init_game 重建全部实体 + handler）。"""
    g._init_game()
    g.game_state.test_auto_spawn = False
    return g


def click(g, pos):
    g._handle_mode_click_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos}))


g = TestGame()


# ---------------------------------------------------------------- 结构回归

def v_structure_no_scatter():
    """结构回归：test_game 无方法内延迟 import；无 _enemy_types 散落敌种表。"""
    import inspect
    import game.test_game as tg
    src = inspect.getsource(tg)
    assert "from ui.test_panel import get_test_boss_rects" not in src, "方法内延迟 import 仍在"
    assert "get_test_boss_toggle_rect" not in src, "Boss 按钮 y hack 仍在"
    assert "_enemy_types" not in src, "散落敌种表仍在"
    # 敌种统一表：7 种（含 C02 新增 wraith/warlock）
    assert [d["key"] for d in ENEMY_TYPE_DEFS] == [
        "basic", "charger", "ranger", "exploder", "elite", "wraith", "warlock"]


def v_layout_structure():
    """布局单一入口：结构化 dict，7 敌种 / 4 Boss+清屏 / 16 技能 / R2 沙盒按钮。"""
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT, True, True)
    assert len(layout["enemy"]) == 7
    assert len(layout["boss"]) == len(BOSS_CONFIGS) + 1 == 5
    assert len(layout["skill"]) == len(SKILL_POOL) == 16
    for k in ("type_0", "type_6", "hp_input", "damage_input", "speed_input", "spawn"):
        assert k in layout["custom_enemy"], f"custom_enemy 缺 {k}"
    # R2：沙盒控制按钮存在
    for k in ("upgrade_toggle", "reset"):
        assert k in layout["player"], f"player 缺 {k}"
    # 收起状态：enemy / boss 为空
    collapsed = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    assert collapsed["enemy"] == [] and collapsed["boss"] == []
    # Boss 按钮与技能区（y<=236）不重叠
    for r in layout["boss"]:
        assert r.top > 236, f"Boss 按钮 {r} 与技能区重叠"
    # R2：玩家面板内按钮互不重叠；调试按钮不与玩家面板重叠
    player_rects = list(layout["player"].values())
    for i in range(len(player_rects)):
        for j in range(i + 1, len(player_rects)):
            assert not player_rects[i].colliderect(player_rects[j]), \
                f"player rect 重叠: {i} {player_rects[i]} vs {j} {player_rects[j]}"
    for r in player_rects:
        assert not layout["debug_stats"].colliderect(r), f"debug 与玩家按钮重叠 {r}"


# ---------------------------------------------------------------- 敌种快速生成

def v_quick_spawn_7_types():
    """① 7 敌种快速生成可 spawn（含 wraith/warlock）。"""
    g = reset()
    for d in ENEMY_TYPE_DEFS:
        before = len(g.enemies)
        g.test_handler.spawn_enemy_near_player(d["key"], g.enemies, g.player, game=g)
        assert len(g.enemies) == before + 1, f"quick spawn {d['key']} 失败"
    spawned = g.enemies.sprites()
    assert any(isinstance(e, Wraith) for e in spawned), "未生成 Wraith"
    assert any(isinstance(e, Warlock) for e in spawned), "未生成 Warlock"
    wraith = next(e for e in spawned if isinstance(e, Wraith))
    assert wraith._sprite_name == "wraith", "Wraith 未走 C02 _spawn_enemy 构造路径"


def v_quick_spawn_click():
    """①b 通过面板点击快速生成（展开敌种面板，7 按钮逐个点）。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    click(g, layout["enemy_toggle"].center)  # 展开敌种面板
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT, True, False)
    assert len(layout["enemy"]) == 7
    for i, d in enumerate(ENEMY_TYPE_DEFS):
        before = len(g.enemies)
        click(g, layout["enemy"][i].center)
        assert len(g.enemies) == before + 1, f"点击快速生成 {d['key']} 失败"
    spawned = g.enemies.sprites()
    assert any(isinstance(e, Wraith) for e in spawned)
    assert any(isinstance(e, Warlock) for e in spawned)


# ---------------------------------------------------------------- 自定义敌人

def v_custom_spawn_7_types():
    """② 自定义敌人 7 类型可生成，HP/速度/伤害 生效。"""
    g = reset()
    for d in ENEMY_TYPE_DEFS:
        before = len(g.enemies)
        g.test_handler.spawn_custom_enemy_with_type(
            g.enemies, g.player, d["key"], hp=77, speed=120, damage=3, game=g)
        assert len(g.enemies) == before + 1, f"custom spawn {d['key']} 失败"
        new_enemy = g.enemies.sprites()[-1]
        assert new_enemy.hp == 77, f"{d['key']} hp={new_enemy.hp} != 77"
        assert new_enemy.speed == 120, f"{d['key']} speed={new_enemy.speed} != 120"
        if d["key"] != "exploder":
            assert new_enemy.contact_damage == 3, f"{d['key']} contact_damage={new_enemy.contact_damage}"
    # exploder 保持旧行为：无接触伤害、爆炸伤害=3×2
    g = reset()
    g.test_handler.spawn_custom_enemy_with_type(
        g.enemies, g.player, "exploder", hp=77, speed=120, damage=3, game=g)
    ex = g.enemies.sprites()[-1]
    assert ex.contact_damage == 0 and ex.explosion_damage == 6


def v_custom_spawn_click():
    """②b 自定义敌种选择 + 生成按钮（点击路径）。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    # 选第 7 种（warlock）
    click(g, layout["custom_enemy"]["type_6"].center)
    assert g.test_handler.state.custom_enemy_type == 6
    # 设置数值后点生成
    g.test_handler.state.custom_hp = 99
    g.test_handler.state.custom_speed = 150
    g.test_handler.state.custom_damage = 4
    before = len(g.enemies)
    click(g, layout["custom_enemy"]["spawn"].center)
    assert len(g.enemies) == before + 1, "自定义生成按钮未生效"
    new_enemy = g.enemies.sprites()[-1]
    assert isinstance(new_enemy, Warlock), "自定义敌种未按所选类型生成"
    assert new_enemy.hp == 99 and new_enemy.speed == 150 and new_enemy.contact_damage == 4


# ---------------------------------------------------------------- Boss

def v_boss_spawn_clear():
    """③ 4 Boss + 独立清屏按钮：Boss 进 enemies+bosses 双组；清屏保留 Boss。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    click(g, layout["boss_toggle"].center)  # 展开 Boss 面板
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT, False, True)
    assert len(layout["boss"]) == len(BOSS_CONFIGS) + 1

    for i in range(len(BOSS_CONFIGS)):
        before_boss = len(g.bosses)
        click(g, layout["boss"][i].center)
        assert len(g.bosses) == before_boss + 1, f"Boss {i} 未生成"
        assert g.game_state.boss_active, "Boss 生成后 boss_active 未置位"
        # Boss 双组：enemies 中也存在
        assert any(isinstance(e, Boss) for e in g.enemies), "Boss 未加入 enemies 组"

    # 清屏：加入普通敌人后点清屏按钮
    g.enemies.add(Enemy(400, 400))
    non_boss_before = sum(1 for e in g.enemies if not isinstance(e, Boss))
    assert non_boss_before >= 1
    click(g, layout["boss"][len(BOSS_CONFIGS)].center)  # 独立清屏按钮
    non_boss_after = sum(1 for e in g.enemies if not isinstance(e, Boss))
    assert non_boss_after == 0, "清屏后仍有非 Boss 敌人"
    assert len(g.bosses) == len(BOSS_CONFIGS), "清屏误删 Boss"


# ---------------------------------------------------------------- 自动生成开关

def v_auto_spawn_single_source():
    """④ 自动生成开关状态单一源同步（handler.state ↔ game_state 镜像 ↔ _should_spawn_auto）。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    assert g.test_handler.state.auto_spawn is False
    assert g.game_state.test_auto_spawn is False
    assert g._should_spawn_auto() is False
    click(g, layout["auto_spawn"].center)
    assert g.test_handler.state.auto_spawn is True
    assert g.game_state.test_auto_spawn is True, "镜像未同步"
    assert g._should_spawn_auto() is True
    click(g, layout["auto_spawn"].center)
    assert g.test_handler.state.auto_spawn is False
    assert g.game_state.test_auto_spawn is False
    assert g._should_spawn_auto() is False


# ---------------------------------------------------------------- 技能面板

def v_skill_click_16():
    """⑤ 技能面板点击 16 技能不崩（含 frost/flame）。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    for i, skill in enumerate(SKILL_POOL):
        before = list(g.game_state.acquired_skills)
        click(g, layout["skill"][i].center)
        assert skill["name"] in g.game_state.acquired_skills, f"技能 {i} {skill['name']} 未获得"
    assert g.game_state.stats.get("has_frost", 0) >= 1, "凛冬之环未激活"
    assert g.game_state.stats.get("has_flame", 0) >= 1, "圣焰喷射器未激活"


# ---------------------------------------------------------------- TEXTINPUT

def v_textinput_collect():
    """⑥ 输入框 TEXTINPUT 收集 + Backspace/ESC/点击外部取消。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    # 激活 HP 输入框
    click(g, layout["custom_enemy"]["hp_input"].center)
    assert g.test_handler.state.active_input_field == TestInputField.HP
    # TEXTINPUT 数字追加（初值 20 → 205 → 2057）
    g._handle_pre_event(pygame.event.Event(pygame.TEXTINPUT, {"text": "5"}))
    assert g.test_handler.state.custom_hp == 205, f"custom_hp={g.test_handler.state.custom_hp}"
    g._handle_pre_event(pygame.event.Event(pygame.TEXTINPUT, {"text": "7"}))
    assert g.test_handler.state.custom_hp == 2057
    # 非数字忽略
    g._handle_pre_event(pygame.event.Event(pygame.TEXTINPUT, {"text": "a"}))
    assert g.test_handler.state.custom_hp == 2057
    # Backspace
    g._handle_pre_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE}))
    assert g.test_handler.state.custom_hp == 205
    # ESC 取消
    g._handle_pre_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert g.test_handler.state.active_input_field is None
    # damage 输入框：激活后点外部取消
    click(g, layout["custom_enemy"]["damage_input"].center)
    assert g.test_handler.state.active_input_field == TestInputField.DAMAGE
    g._handle_pre_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (500, 500)}))
    assert g.test_handler.state.active_input_field is None


# ---------------------------------------------------------------- 渲染

def v_render_panel():
    """⑦ 测试面板渲染多状态不崩（_render_mode_overlays）。"""
    g = reset()
    for enemy_exp in (False, True):
        for boss_exp in (False, True):
            g.test_handler.state.enemy_panel_expanded = enemy_exp
            g.test_handler.state.boss_panel_expanded = boss_exp
            g.test_handler.state.debug_stats_enabled = True
            g._render_mode_overlays((10, 10))
            g._render_mode_overlays((640, 360))
    # 暂停/结束/escaped 时不渲染（不崩）
    g.game_state.paused = True
    g._render_mode_overlays((10, 10))
    g.game_state.paused = False
    g.game_state.game_over = True
    g._render_mode_overlays((10, 10))
    g.game_state.game_over = False
    g.game_state.escaped = True
    g._render_mode_overlays((10, 10))
    g.game_state.escaped = False


def v_render_full_frame():
    """⑦b 全帧渲染不崩（含武器管理器渲染路径）。"""
    g = reset()
    g.test_handler.state.enemy_panel_expanded = True
    g.test_handler.state.boss_panel_expanded = True
    g.test_handler.state.debug_stats_enabled = True
    g.game_state.stats["has_blades"] = 1
    g.game_state.stats["blade_count"] = 3
    g.game_state.stats["has_lightning"] = 1
    g.game_state.stats["has_frost"] = 1
    g.game_state.stats["has_flame"] = 1
    for _ in range(3):
        g._update(0.016)
        g._render()
    # 渲染 Boss 预警
    g.game_state.boss_warning_active = True
    g._pending_boss_config = BOSS_CONFIGS[0]
    g.warning_flash_alpha = 40
    g._render()
    g.game_state.boss_warning_active = False


# ---------------------------------------------------------------- 回归：玩家控制保留

def v_player_controls():
    """保留功能：HP/HP上限/经验倍率 的 -/+ /应用、满血、+100/+500 经验。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    p = layout["player"]

    # xp 应用语义修正：+/- 改值后点"应用"保留当前值（不再清零）
    g.test_handler.state.xp_multiplier = 1.0
    click(g, p["xp_plus"].center)
    assert g.test_handler.state.xp_multiplier == 1.5
    assert g.game_state.test_xp_multiplier == 1.5
    click(g, p["xp_apply"].center)
    assert g.test_handler.state.xp_multiplier == 1.5, "xp_apply 不应清零（应用当前值语义）"
    assert g.game_state.test_xp_multiplier == 1.5

    # HP 设置 → 应用（clamp 到上限设置，故先抬高上限）
    g.test_handler.state.custom_hp = 30
    g.test_handler.state.custom_max_hp = 50
    g.game_state.player_hp = 20
    click(g, p["hp_apply"].center)
    assert g.game_state.player_hp == 30

    # MaxHP 应用
    g.test_handler.state.custom_max_hp = 50
    click(g, p["max_hp_apply"].center)
    assert g.game_state.stats["max_hp"] == 50

    # 满血
    g.game_state.player_hp = 10
    click(g, p["full_hp"].center)
    assert g.game_state.player_hp == g.game_state.stats["max_hp"]

    # 加经验
    g.game_state.experience = 0
    click(g, p["add_xp_100"].center)
    assert g.game_state.experience == 100
    click(g, p["add_xp_500"].center)
    assert g.game_state.experience == 600


# ---------------------------------------------------------------- R2 沙盒化

def v_level_up_disabled_default():
    """SMK-新1：默认 allow_level_up=False 时击杀不触发升级弹窗（经验涨但 level/paused 不变）。"""
    g = reset()
    assert g.test_handler.state.allow_level_up is False
    g.game_state.experience = 10000  # 远超阈值
    g._check_level_up()
    assert g.game_state.level == 1, "默认关闭时不应升级"
    assert g.game_state.paused is False, "默认关闭时不应暂停（弹窗冻结根因）"
    assert g.game_state.chosen_skills is None, "默认关闭时不应弹技能选择"
    assert g.game_state.experience == 10000, "经验应保留显示不扣减"


def v_level_up_enabled():
    """SMK-新2：开启 allow_level_up 后升级路径恢复（经验达阈值触发 chosen_skills/paused）。"""
    g = reset()
    g.test_handler.state.allow_level_up = True
    g.game_state.experience = 10000
    g._check_level_up()
    assert g.game_state.level > 1, "开启后应升级"
    assert g.game_state.paused is True, "升级应暂停（恢复 BaseGame 原逻辑）"
    assert g.game_state.chosen_skills is not None and len(g.game_state.chosen_skills) == 3
    assert g.game_state.stats["max_hp"] >= 21, "升级应 +1 max_hp"


def v_level_up_toggle_click():
    """升级开关按钮：点击切换 allow_level_up。"""
    g = reset()
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    assert g.test_handler.state.allow_level_up is False
    click(g, layout["player"]["upgrade_toggle"].center)
    assert g.test_handler.state.allow_level_up is True
    click(g, layout["player"]["upgrade_toggle"].center)
    assert g.test_handler.state.allow_level_up is False


def v_reset_button():
    """SMK-新3：重置按钮 → _restart → 状态归零（敌人清空/HP 满/level 1/技能空/test_handler 默认）。"""
    g = reset()
    # 制造非初始状态
    g.test_handler.state.custom_hp = 77
    g.test_handler.state.custom_max_hp = 66
    g.test_handler.state.allow_level_up = True
    g.test_handler.state.auto_spawn = True
    g.test_handler.state.enemy_panel_expanded = True
    g.game_state.test_auto_spawn = True
    g.game_state.experience = 500
    g.game_state.level = 5
    g.game_state.player_hp = 3
    g.game_state.stats["max_hp"] = 50
    g.game_state.acquired_skills.append("火力增强")
    g.enemies.add(Enemy(400, 400))
    boss = BOSS_CLASSES[0](400, 400)
    g.enemies.add(boss)
    g.bosses.add(boss)
    g.game_state.boss_active = True
    # 点击重置（敌种面板展开状态，reset 按钮位置固定不受影响）
    layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT, True, False)
    click(g, layout["player"]["reset"].center)
    # 断言：全部归零 / 回默认
    assert g.test_handler.state.custom_hp == PLAYER_MAX_HP
    assert g.test_handler.state.custom_max_hp == PLAYER_MAX_HP
    assert g.test_handler.state.allow_level_up is False
    assert g.test_handler.state.auto_spawn is False
    assert g.test_handler.state.enemy_panel_expanded is False
    assert g.game_state.test_auto_spawn is False
    assert g.game_state.experience == 0
    assert g.game_state.level == 1
    assert g.game_state.player_hp == g.game_state.stats["max_hp"]
    assert g.game_state.acquired_skills == []
    assert g.game_state.boss_active is False
    assert len(g.enemies) == 0 and len(g.bosses) == 0


def v_reset_after_restart_still_runs():
    """重置后游戏可继续：_update/_render 不崩（_restart 复用 run 循环）。"""
    g = reset()
    click(g, build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT)["player"]["reset"].center)
    for _ in range(3):
        g._update(0.016)
        g._render()


checks = [
    ("结构回归：无延迟 import / 无散落敌种表 / 7 敌种表", v_structure_no_scatter),
    ("布局单一入口：7 敌种 / 4 Boss+清屏 / 16 技能 / R2 沙盒按钮无重叠", v_layout_structure),
    ("① 敌种快速生成 7 种可 spawn（含 wraith/warlock）", v_quick_spawn_7_types),
    ("①b 面板点击快速生成 7 种", v_quick_spawn_click),
    ("② 自定义敌人 7 类型可生成，数值生效", v_custom_spawn_7_types),
    ("②b 自定义敌种选择 + 生成按钮（点击路径）", v_custom_spawn_click),
    ("③ 4 Boss + 独立清屏按钮（双组/保留 Boss）", v_boss_spawn_clear),
    ("④ 自动生成开关状态单一源同步", v_auto_spawn_single_source),
    ("⑤ 技能面板点击 16 技能不崩（含 frost/flame）", v_skill_click_16),
    ("⑥ 输入框 TEXTINPUT 收集 + Backspace/ESC/外部取消", v_textinput_collect),
    ("⑦ 测试面板渲染多状态不崩", v_render_panel),
    ("⑦b 全帧渲染不崩（含武器/Boss 预警）", v_render_full_frame),
    ("保留功能：玩家控制 -/+/应用/满血/加经验", v_player_controls),
    ("SMK-新1 升级开关默认关：击杀不触发升级弹窗", v_level_up_disabled_default),
    ("SMK-新2 开启升级开关后升级路径恢复", v_level_up_enabled),
    ("SMK-新2b 升级开关按钮点击切换", v_level_up_toggle_click),
    ("SMK-新3 重置按钮 → _restart 状态归零", v_reset_button),
    ("SMK-新3b 重置后游戏可继续（update/render 不崩）", v_reset_after_restart_still_runs),
]


def _main():
    print("DN-ENG-TEST-R1/R2 测试模式重构 + 沙盒化验收")
    print("=" * 46)
    for name, fn in checks:
        check(name, fn)
    print()
    if FAILED:
        print("TEST_MODE_REFACTOR_FAIL:", ", ".join(FAILED))
        rc = 1
    else:
        print("TEST_MODE_REFACTOR_ALL_PASS")
        rc = 0
    out.close()
    return rc


if __name__ == "__main__":
    sys.exit(_main())
out.close()
