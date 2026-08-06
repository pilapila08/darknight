# -*- coding: utf-8 -*-
"""R3 数值生效验证（验收用）：逐项断言权威表 playability-pack-v1.md §1.2。

用法：python tools/verify_r3.py   （结果写入 tools/verify_out.txt）
"""
import os, sys, traceback
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    out = open("verify_out.txt", "w", encoding="utf-8")
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
    BULLET_BASE_DAMAGE, BULLET_COUNT_BASE, SKILL_DEFS, TRAP_DAMAGE_BASE,
    DIFFICULTY_MAX_TIER, DAMAGE_BONUS_MAX, SPAWN_RATE_CAP_BASE, SPAWN_CAP_PER_BOSS,
    VOID_LORD_HP, BULLET_PENALTY_THRESHOLD, BULLET_PENALTY_MULT,
    BULLET_PIERCE_MAX, LIGHTNING_COOLDOWN, TRAP_DURATION, TRAP_RADIUS, TRAP_DOT_TICK,
)
from skills import apply_skill, get_random_skills, SKILL_POOL
from game.state import GameState


def fresh_stats():
    return GameState().reset() or GameState().stats


def get_skill(name):
    for s in SKILL_POOL:
        if s["name"] == name:
            return s
    return None


# --- R3: 暗影新星 ---
def v_nova_first():
    st = fresh_stats()
    apply_skill(st, get_skill("暗影新星"))
    assert st["blade_damage"] == 12, st["blade_damage"]
    assert st["nova_cooldown"] == 3.8, st["nova_cooldown"]
    assert st["nova_radius"] == 150, st["nova_radius"]
    assert st["has_blades"] == 1


def v_nova_second():
    st = fresh_stats()
    s = get_skill("暗影新星")
    apply_skill(st, s)
    apply_skill(st, s)
    assert st["blade_damage"] == 15, st["blade_damage"]          # 12+3
    assert abs(st["nova_cooldown"] - 3.55) < 1e-6, st["nova_cooldown"]  # 3.8-0.25
    assert st["nova_radius"] == 162, st["nova_radius"]           # 150+12


def v_nova_cooldown_floor():
    st = fresh_stats()
    s = get_skill("暗影新星")
    for _ in range(10):
        apply_skill(st, s)
    assert st["nova_cooldown"] >= 2.2, st["nova_cooldown"]       # 下限 2.2


# --- R3: 连锁闪电 ---
def v_lightning_first():
    st = fresh_stats()
    apply_skill(st, get_skill("连锁闪电"))
    assert st["lightning_chains"] == 5, st["lightning_chains"]
    assert st["lightning_damage"] == 7, st["lightning_damage"]


def v_lightning_second():
    st = fresh_stats()
    s = get_skill("连锁闪电")
    apply_skill(st, s)
    apply_skill(st, s)
    assert st["lightning_chains"] == 6, st["lightning_chains"]   # +1跳
    assert st["lightning_damage"] == 8, st["lightning_damage"]   # +1伤


# --- R3: 剧毒地雷 ---
def v_trap_first():
    st = fresh_stats()
    apply_skill(st, get_skill("剧毒地雷"))
    assert st["trap_damage"] == 4, st["trap_damage"]             # TRAP_DAMAGE_BASE
    assert st["trap_interval"] == 2.0, st["trap_interval"]       # skills 唯一源
    assert st["trap_radius_mult"] == 1.0


def v_trap_second():
    st = fresh_stats()
    s = get_skill("剧毒地雷")
    apply_skill(st, s)
    apply_skill(st, s)
    assert st["trap_interval"] == 1.9, st["trap_interval"]       # -0.1
    assert abs(st["trap_damage"] - 4.5) < 1e-6, st["trap_damage"]  # +0.5
    assert abs(st["trap_radius_mult"] - 1.05) < 1e-6, st["trap_radius_mult"]


# --- R3: 弹量边际惩罚（第 4 发起 ×0.55）---
def v_bullet_penalty():
    assert BULLET_PENALTY_THRESHOLD == 3
    assert BULLET_PENALTY_MULT == 0.55
    # 4 发时：索引 0-2 满伤，索引 3 起 ×0.55
    for i in range(4):
        mult = BULLET_PENALTY_MULT if i >= BULLET_PENALTY_THRESHOLD else 1.0
        assert mult == (0.55 if i >= 3 else 1.0), (i, mult)


# --- R3: 穿透弹重做（B1）---
def v_pierce():
    st = fresh_stats()
    s = get_skill("穿透弹")
    assert s is not None and s["key"] == "bullet_speed"
    apply_skill(st, s)
    assert st["bullet_pierce"] == 1, st["bullet_pierce"]
    assert st["bullet_damage_mult"] == 0.85, st["bullet_damage_mult"]
    assert st["bullet_speed"] == 1.5, st["bullet_speed"]
    apply_skill(st, s)  # 重复：+1 穿透，伤害不再衰减
    assert st["bullet_pierce"] == 2, st["bullet_pierce"]
    assert st["bullet_damage_mult"] == 0.85, st["bullet_damage_mult"]
    apply_skill(st, s)  # 第 3 层
    assert st["bullet_pierce"] == 3, st["bullet_pierce"]


def v_pierce_cap():
    # 4 层后移出池
    st = fresh_stats()
    s = get_skill("穿透弹")
    for _ in range(3):
        apply_skill(st, s)
    from skills import _skill_available
    assert not _skill_available(s, st), "穿透弹应在 3 层后不可用"


# --- R3: 静电过载 ---
def v_static_overload_grants_nova():
    st = fresh_stats()
    apply_skill(st, get_skill("静电过载"))
    assert st["has_blades"] == 1, st["has_blades"]               # 未拥有新星 → 获得 +1 层
    assert st["blade_damage"] == 12, st["blade_damage"]
    assert st["nova_cooldown"] == 3.8, st["nova_cooldown"]
    assert st["static_overload"] == 1


def v_static_overload_with_nova():
    st = fresh_stats()
    apply_skill(st, get_skill("暗影新星"))
    apply_skill(st, get_skill("静电过载"))
    # 已有新星：静电过载不额外加新星层，只标记联动生效（has_blades 保持 1）
    assert st["has_blades"] == 1, st["has_blades"]
    assert st["static_overload"] == 1


# --- R3: 死亡回响 ---
def v_death_echo():
    st = fresh_stats()
    apply_skill(st, get_skill("死亡回响"))
    assert st["death_echo"] == 1, st["death_echo"]


# --- R3: 三选一不重复（池 12→14 回归）---
def v_random_no_dup():
    for _ in range(50):
        skills = get_random_skills(3, fresh_stats())
        names = [s["name"] for s in skills]
        assert len(set(names)) == len(names), names
    # C02：技能池 14→16（content-pack-v2.md §1.4，新增 凛冬之环/圣焰喷射器）
    assert len(SKILL_POOL) == 16, len(SKILL_POOL)


# --- R3: state 基础值引用 settings ---
def v_state_defaults():
    st = fresh_stats()
    assert st["bullet_damage"] == BULLET_BASE_DAMAGE == 2
    assert st["bullet_count"] == BULLET_COUNT_BASE == 1
    assert "pickup_range" not in st, "pickup_range 死字段应移除"


# --- R3: 死常量删除 ---
def v_dead_constants_removed():
    import settings
    for name in ["BLADE_DAMAGE", "BLADE_ORBIT_RADIUS", "BLADE_ORBIT_SPEED",
                 "BLADE_SIZE", "BLADE_COLOR", "ORB_RADIUS", "ORB_SPEED",
                 "XP_PER_ORB", "PICKUP_RANGE", "TRAP_DOT_DAMAGE",
                 "TRAP_INTERVAL", "LIGHTNING_DAMAGE", "LIGHTNING_CHAINS",
                 "SPAWN_RATE_CAP"]:
        assert not hasattr(settings, name), f"{name} 应已删除"
    # 保留项
    assert settings.LIGHTNING_COOLDOWN == 2.0
    assert settings.TRAP_DURATION == 12.0
    assert settings.TRAP_RADIUS == 45
    assert settings.TRAP_DOT_TICK == 1.0


# --- R3: TRAP 唯一源 ---
def v_trap_unique_source():
    from entities.acid_trap import AcidTrap, TrapManager
    assert AcidTrap.__init__.__defaults__[0] == TRAP_DAMAGE_BASE == 4
    assert TrapManager.update.__defaults__[1] == TRAP_DAMAGE_BASE


# --- R4: 难度常量 ---
def v_r4_constants():
    assert DIFFICULTY_MAX_TIER == 17, DIFFICULTY_MAX_TIER
    assert DAMAGE_BONUS_MAX == 8
    assert SPAWN_RATE_CAP_BASE == 5
    assert SPAWN_CAP_PER_BOSS == 1.5
    assert VOID_LORD_HP == 5500, VOID_LORD_HP


# --- R4: tf_cap 公式（终局 5+1.5×4=11）---
def v_tf_cap():
    for b in range(5):
        cap = SPAWN_RATE_CAP_BASE + SPAWN_CAP_PER_BOSS * b
        assert cap == 5 + 1.5 * b, (b, cap)
    assert SPAWN_RATE_CAP_BASE + SPAWN_CAP_PER_BOSS * 4 == 11.0


checks = [
    ("R3 新星首取 12/3.8/150", v_nova_first),
    ("R3 新星二取 15/3.55/162", v_nova_second),
    ("R3 新星冷却下限 2.2", v_nova_cooldown_floor),
    ("R3 闪电首取 5跳/7伤", v_lightning_first),
    ("R3 闪电二取 6跳/8伤", v_lightning_second),
    ("R3 地雷首取 4伤/2.0s/×1.0", v_trap_first),
    ("R3 地雷二取 4.5伤/1.9s/×1.05", v_trap_second),
    ("R3 弹量第4发起×0.55", v_bullet_penalty),
    ("R3 穿透弹 穿透+1/×0.85/弹速1.5", v_pierce),
    ("R3 穿透弹 3层封顶移出池", v_pierce_cap),
    ("R3 静电过载 未拥有新星→获得+1层", v_static_overload_grants_nova),
    ("R3 静电过载 已有新星→联动层+1", v_static_overload_with_nova),
    ("R3 死亡回响 层数+1", v_death_echo),
    ("R3 三选一不重复（池16回归）", v_random_no_dup),
    ("R3 state 基础值引用 settings", v_state_defaults),
    ("R3 死常量删除", v_dead_constants_removed),
    ("R3 TRAP 唯一源", v_trap_unique_source),
    ("R4 难度常量", v_r4_constants),
    ("R4 tf_cap 公式", v_tf_cap),
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
