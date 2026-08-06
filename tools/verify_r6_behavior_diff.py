# -*- coding: utf-8 -*-
"""R6 行为等价验证：原始(HEAD) vs 重构后 NormalGame/TestGame 逐帧状态对比。

用法：venv/Scripts/python.exe tools/verify_r6_behavior_diff.py
原理：把 git HEAD 的原始类与重构后的类分别实例化，喂入相同随机种子/相同事件序列，
每帧对比全部可观察游戏状态（GameState 字段 / 玩家 / 敌人 / 子弹 / 掉落 / Boss /
区域效果 / 陷阱 / 飘字 / 武器冷却等），断言完全一致 → 证明行为零变化。
"""
import os
import sys
import math
import random
import tempfile
import importlib.util

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pygame

FAILED = []


def load_orig(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


ORIG_DIR = os.environ.get("R6_ORIG_DIR", tempfile.gettempdir())
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def snapshot(g):
    """提取可观察状态快照（排除渲染/音频副作用）。"""
    gs = g.game_state
    st = dict(gs.stats)
    return {
        "character": gs.character,
        "stats": st,
        "acquired_skills": list(gs.acquired_skills),
        "spawn_timer": gs.spawn_timer,
        "fire_timer": gs.fire_timer,
        "score": gs.score,
        "experience": gs.experience,
        "level": gs.level,
        "paused": gs.paused,
        "chosen_skills": [s["name"] for s in gs.chosen_skills] if gs.chosen_skills else None,
        "elapsed_time": gs.elapsed_time,
        "difficulty_level": gs.difficulty_level,
        "player_hp": gs.player_hp,
        "player_shield": gs.player_shield,
        "player_max_shield": gs.player_max_shield,
        "invincible_timer": gs.invincible_timer,
        "boss_active": gs.boss_active,
        "boss_defeated_count": gs.boss_defeated_count,
        "boss_warning_active": gs.boss_warning_active,
        "boss_warning_timer": gs.boss_warning_timer,
        "player_rect": (g.player.rect.x, g.player.rect.y),
        "player_speed": g.player.speed,
        "player_max_hp": g.player.max_hp,
        "enemies": sorted((e.rect.x, e.rect.y, e.hp, e.is_elite, e.contact_damage)
                          for e in g.enemies),
        "bullets": sorted((b.rect.x, b.rect.y, b.pierce, getattr(b, "damage_mult", 1.0))
                          for b in g.bullets),
        "enemy_bullets": sorted((b.rect.x, b.rect.y, b.damage) for b in g.enemy_bullets),
        "boss_projectiles": sorted((b.rect.x, b.rect.y, b.damage) for b in g.boss_projectiles),
        "bosses": sorted((b.rect.x, b.rect.y, b.hp, b.max_hp) for b in g.bosses),
        "drops": sorted((d.kind, d.amount, d.rect.x, d.rect.y) for d in g.drops),
        "particles": len(g.particles),
        "area_effects": sorted((a.x, a.y, a.damage, a.elapsed, type(a).__name__)
                               for a in g.area_effects),
        "explosions": len(g.explosions),
        "damage_numbers": len(g.damage_numbers),
        "blade_cd": g.blade_mgr.cooldown_timer,
        "trap_count": len(g.trap_mgr.group),
        "run_kills": g.run_kills,
        "run_boss_kills": g.run_boss_kills,
        "warning_flash_alpha": g.warning_flash_alpha,
        "map_name": g.map_manager.map_data["name"],
        "transition_active": g.map_manager.transition_active,
        "transition_timer": g.map_manager.transition_timer,
    }


def compare(name, a, b):
    if a != b:
        FAILED.append(name)
        print(f"[DIFF] {name}")
        keys = set(a) | set(b)
        for k in sorted(keys):
            if a.get(k) != b.get(k):
                av, bv = a.get(k), b.get(k)
                if isinstance(av, list) and isinstance(bv, list) and len(av) != len(bv):
                    print(f"  {k}: len {len(av)} vs {len(bv)}")
                else:
                    print(f"  {k}: {str(av)[:120]} vs {str(bv)[:120]}")
    else:
        print(f"[OK]   {name}")


def run_scenario(mode, frames=140, dt=1 / 60.0):
    from skills import SKILL_POOL as _SKILL_POOL

    def get_skill(name):
        for s in _SKILL_POOL:
            if s["name"] == name:
                return s
        return None

    if mode == "normal":
        orig_mod = load_orig(os.path.join(ORIG_DIR, "r6_orig_normal.py"), "r6_orig_normal")
        from game.normal_game import NormalGame as NewNormal
        old = orig_mod.NormalGame()
        new = NewNormal()
    else:
        orig_mod = load_orig(os.path.join(ORIG_DIR, "r6_orig_test.py"), "r6_orig_test")
        from game.test_game import TestGame as NewTest
        old = orig_mod.TestGame()
        new = NewTest()

    old._init_game()
    new._init_game()
    compare(f"{mode}:init", snapshot(old), snapshot(new))

    # 施加固定技能序列（覆盖 新星/闪电/地雷/穿透/火力/复苏 等路径）
    skill_seq = ["暗影新星", "连锁闪电", "剧毒地雷", "穿透弹", "火力增强", "复苏之风"]
    for i, name in enumerate(skill_seq):
        s = get_skill(name)
        if s is None:
            continue
        random.seed(1000 + i)
        old._apply_skill(s)
        random.seed(1000 + i)
        new._apply_skill(s)
        compare(f"{mode}:apply[{name}]", snapshot(old), snapshot(new))

    # 事件序列：技能选择确认(1/2/3) + ESC + F11 全屏切换
    ev_seq = [
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}),
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1}),
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}),
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11}),
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11}),
    ]
    for i, ev in enumerate(ev_seq):
        pygame.event.post(ev)
        old._handle_events()
        pygame.event.clear()
        pygame.event.post(ev)
        new._handle_events()
        pygame.event.clear()
        compare(f"{mode}:event[{i}]", snapshot(old), snapshot(new))

    # 主循环逐帧对比（每帧同一随机种子）
    for f in range(frames):
        seed = 4242 + f
        random.seed(seed)
        old._update(dt)
        random.seed(seed)
        new._update(dt)
        compare(f"{mode}:frame[{f}]", snapshot(old), snapshot(new))
        old._render()
        new._render()

    # 终局：手动触发 Boss 战（预警 + 生成 + 击杀路径）
    old.game_state.elapsed_time = 200.0
    new.game_state.elapsed_time = 200.0
    old.game_state.boss_defeated_count = 0
    new.game_state.boss_defeated_count = 0
    for f in range(120):
        seed = 9000 + f
        random.seed(seed)
        old._update(dt)
        random.seed(seed)
        new._update(dt)
        compare(f"{mode}:boss[{f}]", snapshot(old), snapshot(new))
        if not old.game_state.boss_active and not old.game_state.boss_warning_active and old.game_state.boss_defeated_count > 0:
            break
        old._render()
        new._render()

    old.audio.stop_music()
    new.audio.stop_music()


run_scenario("normal")
run_scenario("test")

print()
if FAILED:
    print("BEHAVIOR_DIFF_FAIL:", len(FAILED), "frames differed")
    sys.exit(1)
print("BEHAVIOR_ALL_MATCH")
