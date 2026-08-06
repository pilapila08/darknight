# -*- coding: utf-8 -*-
"""C02 内容扩充验收（content-pack-v2.md §1.5 / §2.6 / §4.4 + fx-spec-v1.md）。

用法：venv/Scripts/python.exe tools/verify_content.py   （结果写入 tools/verify_content_out.txt）

覆盖（22 条生效验收中的关键可断言项）：
- 新武器：凛冬之环 / 圣焰喷射器 数值权威表、减速生效、锥形命中、燃烧、暴击
- 新敌人：怨灵 闪现行为 / 唤魔师 召唤+追踪弹 / 主从绑定无奖励消散 / Boss 战不刷唤魔师
- R7：Boss 降临入场 / 尸王狂暴（召唤 3→5 混合）/ 暗影巫师传送提示 / 弹幕尾迹
- FX：4 类贴图资源可加载，draw 路径不报错
"""
import os
import sys
import math
import random
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    out = open(os.path.join(_PROJECT_ROOT, "tools", "verify_content_out.txt"), "w", encoding="utf-8")
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

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, SKILL_DEFS, WARLOCK_ORB_SPEED
pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from skills import apply_skill, get_random_skills, SKILL_POOL, get_skill_by_name, get_skill_effect_desc
from game.state import GameState
from entities import Enemy
from entities.enemy_types import Wraith, Warlock, HomingOrb
from entities.frost_aura import FrostAuraManager
from entities.flame_spitter import FlameSpitterManager
from entities.boss import CorpseKing, ShadowMage, BOSS_CLASSES
from settings import (WRATH_HP, WARLOCK_HP, WARLOCK_SUMMON_INTERVAL, WARLOCK_ORB_INTERVAL,
                      SHADOW_MAGE_TELEPORT_INTERVAL, SHADOW_MAGE_TELEPORT_TELEGRAPH,
                      CORPSE_KING_MINION_COUNT, CORPSE_KING_ENRAGE_MINION_COUNT)
from effects.fx_textures import (get_explosion_fire, get_explosion_purple, get_nova_ring,
                                 get_lightning_bolt, get_muzzle_flash)


def get_skill(name):
    return get_skill_by_name(name)


def fresh_stats(character="default"):
    return GameState(character).stats


# ---------- §1.5 新武器 ----------

def v_pool_size():
    assert len(SKILL_POOL) == 16, len(SKILL_POOL)
    for _ in range(60):
        sk = get_random_skills(3, GameState().stats)
        assert len({s["name"] for s in sk}) == 3


def v_frost_values():
    st = fresh_stats()
    s = get_skill("凛冬之环")
    assert s is not None
    apply_skill(st, s)
    assert st["frost_radius"] == 100 and st["frost_damage"] == 2 and abs(st["frost_slow"] - 0.20) < 1e-6
    apply_skill(st, s)
    apply_skill(st, s)
    assert st["frost_radius"] == 124, st["frost_radius"]
    assert st["frost_damage"] == 4, st["frost_damage"]
    assert abs(st["frost_slow"] - 0.50) < 1e-6, st["frost_slow"]
    # 减速上限 0.65
    for _ in range(5):
        apply_skill(st, s)
    assert st["frost_slow"] <= 0.65 + 1e-9


def v_flame_values():
    st = fresh_stats()
    s = get_skill("圣焰喷射器")
    assert s is not None
    apply_skill(st, s)
    assert abs(st["flame_interval"] - 0.28) < 1e-6 and st["flame_damage"] == 2
    for _ in range(4):
        apply_skill(st, s)
    assert abs(st["flame_damage"] - 4.4) < 1e-6, st["flame_damage"]   # 2 + 4×0.6
    assert abs(st["flame_interval"] - 0.20) < 1e-6, st["flame_interval"]  # 0.28 - 4×0.02
    apply_skill(st, s)  # 第 6 次触底
    assert abs(st["flame_interval"] - 0.18) < 1e-6
    for _ in range(4):
        apply_skill(st, s)
    assert abs(st["flame_interval"] - 0.18) < 1e-6  # 封底不再降


def v_frost_slow_effect():
    mgr = FrostAuraManager()
    player = pygame.Rect(200, 200, 32, 32)
    e = Enemy(210, 200)
    base_speed = e.speed
    stats = {"has_frost": 1, "frost_radius": 100, "frost_damage": 2, "frost_slow": 0.20}
    mgr.update(0.01, player, [e], stats)
    assert e.speed < base_speed, (e.speed, base_speed)           # 减速生效
    e.rect.center = (500, 500)
    mgr.update(0.01, player, [e], stats)
    assert e.speed == base_speed                                  # 离开恢复
    # tick 伤害
    e2 = Enemy(210, 200)
    e2_hp = e2.hp
    mgr.tick_timer = 0.5
    hits = mgr.update(0.5, player, [e2], stats)
    assert e2.hp < e2_hp                                          # 伤害生效
    assert any(h[1] == 2 for h in hits)


def v_flame_cone_and_burn():
    mgr = FlameSpitterManager()
    player = pygame.Rect(200, 200, 32, 32)
    e1 = Enemy(300, 200)   # 锥内（距离100，角度0）
    e2 = Enemy(500, 400)   # 锥外（距离>170）
    stats = {"has_flame": 1, "flame_interval": 0.28, "flame_damage": 2, "flame_burn": 1,
             "crit_chance": 0.0, "crit_multiplier": 2.0}
    mgr.cooldown_timer = 0.0
    hits = mgr.update(0.01, player, [e1, e2], stats)
    hit_enemies = {h[0] for h in hits}
    assert e1 in hit_enemies and e2 not in hit_enemies            # 仅锥内受伤
    assert e1.dot_timer == 2.0 and e1.dot_damage == 1             # 燃烧 DoT 附加


def v_flame_crit():
    mgr = FlameSpitterManager()
    player = pygame.Rect(200, 200, 32, 32)
    e = Enemy(300, 200)
    stats = {"has_flame": 1, "flame_interval": 0.28, "flame_damage": 2, "flame_burn": 1,
             "crit_chance": 1.0, "crit_multiplier": 2.0}          # 100% 暴击
    mgr.cooldown_timer = 0.0
    hits = mgr.update(0.01, player, [e], stats)
    assert any(h[1] == 4.0 for h in hits)                          # 2 × crit_mult 2.0


def v_weapon_desc_not_empty():
    st = fresh_stats()
    apply_skill(st, get_skill("凛冬之环"))
    apply_skill(st, get_skill("圣焰喷射器"))
    assert get_skill_effect_desc("凛冬之环", st) != "未激活"
    assert get_skill_effect_desc("圣焰喷射器", st) != "未激活"


# ---------- §2.6 新敌人 ----------

def v_wraith_behavior():
    w = Wraith(300, 300)
    player = pygame.Rect(600, 300, 32, 32)
    w._blink_timer = 0.01
    w.update(0.02, player)
    assert w._telegraph_timer > 0 and w._telegraph_pos is not None   # 落点提示期
    target = w._telegraph_pos
    # 推进提示期结束 → 闪现到落点 + 落地停顿
    for _ in range(6):
        w.update(0.1, player)
        if w._telegraph_timer <= 0 and w._land_pause_timer > 0:
            break
    # 已闪现到落点（pygame rect.center 对 sub-pixel 取整，允许 ≤1.5px 偏差）
    assert abs(w.rect.centerx - target[0]) < 1.5 and abs(w.rect.centery - target[1]) < 1.5
    assert w._land_pause_timer > 0                                       # 落地停顿


def v_warlock_events():
    wk = Warlock(300, 300)
    player = pygame.Rect(600, 300, 32, 32)
    wk.summon_timer = WARLOCK_SUMMON_INTERVAL - 0.01
    wk.orb_timer = WARLOCK_ORB_INTERVAL - 0.01
    wk.update(0.02, player)
    evs = wk.drain_events()
    types = {e["type"] for e in evs}
    assert "summon" in types and "orb" in types
    orb = next(e for e in evs if e["type"] == "orb")
    assert orb["damage"] == wk.contact_damage


def v_homing_orb_speed():
    player = pygame.Rect(400, 300, 32, 32)
    orb = HomingOrb(100, 100, player, 2)
    assert abs(math.hypot(orb.vx, orb.vy) - WARLOCK_ORB_SPEED) < 1e-6
    orb.update(0.1)
    # 弯曲追踪：弹向玩家方向靠拢
    d0 = math.hypot(player.centerx - 100, player.centery - 100)
    d1 = math.hypot(player.centerx - orb.rect.centerx, player.centery - orb.rect.centery)
    assert d1 < d0


def v_master_servant_binding():
    class FakeGS:
        elapsed_time = 100.0

    class FakeGame:
        def __init__(self, enemies):
            self.enemies = enemies
            self.game_state = FakeGS()

    wk = Warlock(300, 300)
    minion = Enemy(100, 100)
    minion._master_id = id(wk)
    other = Enemy(200, 200)
    g = FakeGame([minion, other])
    wk.on_death(g)
    assert minion._disperse_at == 102.0      # 仆从 2s 后消散
    assert not hasattr(other, "_disperse_at")  # 非其仆从不受影响


def v_boss_phase_no_warlock_spawn():
    from game.normal_game import NormalGame
    from entities.enemy_types import Warlock as _W
    g = NormalGame()
    g._init_game()
    g.game_state.elapsed_time = 210.0   # tier6 → warlock 已解锁
    g.game_state.boss_active = True
    saw = any(isinstance(g._spawn_enemy(), _W) for _ in range(300))
    assert not saw                       # Boss 战不刷唤魔师
    g.game_state.boss_active = False
    saw = any(isinstance(g._spawn_enemy(), _W) for _ in range(500))
    assert saw                           # 非 Boss 战可出


# ---------- §4.4 R7 ----------

def v_boss_arrive_effect():
    from game.normal_game import NormalGame
    g = NormalGame()
    g._init_game()
    boss = CorpseKing(400, 400)
    before = len(g.particles)
    g._on_boss_arrive(boss)
    assert len(g.particles) == before + 30       # 粒子爆发
    assert g.effects._flash_alpha > 0            # 白闪（Normal）
    assert g.effects.hitstop_timer > 0           # 长顿帧（Normal）


def v_corpse_king_enrage():
    ck = CorpseKing(400, 400)
    ck.hp = int(ck.max_hp * 0.4)                 # <50%
    player = pygame.Rect(500, 300, 32, 32)
    ck.attack_timer = ck.config["attack_interval"]
    attacks = ck._do_attacks(0.016, player)
    types = {a["type"] for a in attacks}
    assert "boss_enrage" in types                 # 狂暴事件
    assert ck.enraged
    # 狂暴召唤：4基础 + 1冲锋（共5）
    ck.enraged = True
    summons = ck._summon_attacks()
    counts = {a["enemy_type"]: a["count"] for a in summons}
    assert counts.get("basic", 0) == CORPSE_KING_ENRAGE_MINION_COUNT - 1
    assert counts.get("charger", 0) == 1
    # 非狂暴：3 基础
    ck.enraged = False
    summons = ck._summon_attacks()
    assert all(a["enemy_type"] == "basic" for a in summons)
    assert sum(a["count"] for a in summons) == CORPSE_KING_MINION_COUNT


def v_corpse_king_charge_telegraph():
    ck = CorpseKing(400, 400)
    player = pygame.Rect(500, 300, 32, 32)
    ck._begin_charge_telegraph(player)
    assert ck._telegraph_timer > 0 and ck._telegraph_target is not None
    # 蓄力结束 → 进入冲锋
    while ck._telegraph_timer > 0:
        ck._do_movement(0.1, player)
    assert ck.charging and ck.charge_target == (player.centerx, player.centery)


def v_shadow_mage_teleport_telegraph():
    sm = ShadowMage(400, 400)
    player = pygame.Rect(600, 300, 32, 32)
    sm.teleport_timer = SHADOW_MAGE_TELEPORT_INTERVAL
    sm._do_movement(0.016, player)
    assert sm._teleport_telegraph > 0 and sm._teleport_target is not None  # 落点提示
    target = sm._teleport_target
    for _ in range(6):
        sm._do_movement(0.1, player)
        if sm._teleport_telegraph <= 0 and sm._teleport_target is None:
            break
    assert sm.rect.centerx == target[0] and sm.rect.centery == target[1]   # 传送完成


def v_shadow_mage_bolt_trail():
    sm = ShadowMage(400, 400)
    player = pygame.Rect(600, 300, 32, 32)
    sm.attack_timer = sm.config["attack_interval"]
    attacks = sm._do_attacks(0.016, player)
    projs = [a for a in attacks if a["type"] == "projectile"]
    assert projs and all(a.get("trail") for a in projs)   # 弹幕带尾迹标记


def v_boss_hud_renders():
    from ui.boss_hud import draw_boss_hp_bar
    from ui.drawables import get_font
    class B:
        hp = 400; max_hp = 1000
        config = {"name": "尸王", "color": (40, 80, 20)}
        enraged = True
    b = B()
    screen = pygame.display.get_surface()
    for _ in range(5):
        draw_boss_hp_bar(screen, get_font(20), b)   # 阶段刻度/低血脉动/狂暴横幅不报错


# ---------- fx-spec-v1.md 贴图 ----------

def v_fx_textures_loaded():
    assert get_explosion_fire() is not None
    assert get_explosion_purple() is not None
    assert get_nova_ring() is not None
    assert get_lightning_bolt() is not None
    assert get_muzzle_flash() is not None


def v_fx_draw_paths():
    from entities.explosion import Explosion
    from effects.orbital_blade import OrbitalBladeManager
    from effects.chain_lightning import ChainLightning, LightningBolt
    from effects.juice import EffectManager
    from systems.camera import Camera
    cam = Camera()
    screen = pygame.display.get_surface()

    ex = Explosion(300, 300, 4)
    ex.radius = 30
    ex.draw(screen, cam)

    obm = OrbitalBladeManager()
    obm.pulses.append({"x": 300, "y": 300, "radius": 100, "age": 0.1, "duration": 0.42})
    obm.draw(screen, cam, pygame.Rect(300, 300, 32, 32))

    bolt = LightningBolt((100, 100), (200, 200))
    bolt.draw(screen, cam)

    em = EffectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    em.add_muzzle_flash(150, 150, 0.5)
    em.update(0.01)
    em.draw_world(screen, cam)


# ---------- 回归：R3 武器行为不回归 ----------
def v_r3_no_regression():
    st = fresh_stats()
    apply_skill(st, get_skill("暗影新星"))
    assert st["blade_damage"] == 12 and st["nova_cooldown"] == 3.8
    st2 = fresh_stats()
    apply_skill(st2, get_skill("连锁闪电"))
    assert st2["lightning_chains"] == 5 and st2["lightning_damage"] == 7
    st3 = fresh_stats()
    apply_skill(st3, get_skill("剧毒地雷"))
    assert st3["trap_damage"] == 4 and st3["trap_interval"] == 2.0


checks = [
    ("C02 技能池 16 + 三选一不重复", v_pool_size),
    ("C02 凛冬之环 数值权威表（1/3次 100/124, 2/4, 20%/50%）", v_frost_values),
    ("C02 圣焰喷射器 数值权威表（1/5次, 封底0.18）", v_flame_values),
    ("C02 凛冬之环 减速生效/离开恢复/tick伤害", v_frost_slow_effect),
    ("C02 圣焰喷射器 仅锥内受伤 + 燃烧DoT", v_flame_cone_and_burn),
    ("C02 圣焰喷射器 暴击触发", v_flame_crit),
    ("C02 新武器 desc 非空", v_weapon_desc_not_empty),
    ("C02 怨灵 闪现→提示→落地停顿", v_wraith_behavior),
    ("C02 唤魔师 召唤+追踪弹事件", v_warlock_events),
    ("C02 追踪弹 homing 弯曲追踪", v_homing_orb_speed),
    ("C02 主从绑定 仆从2s无奖励消散", v_master_servant_binding),
    ("C02 Boss战不刷唤魔师 / 非Boss战可出", v_boss_phase_no_warlock_spawn),
    ("R7 Boss降临入场（震动+粒子+白闪+顿帧）", v_boss_arrive_effect),
    ("R7 尸王狂暴 召唤3→5混合 + 事件", v_corpse_king_enrage),
    ("R7 尸王冲锋蓄力提示", v_corpse_king_charge_telegraph),
    ("R7 暗影巫师传送落点提示 + 落地", v_shadow_mage_teleport_telegraph),
    ("R7 暗影巫师弹幕尾迹标记", v_shadow_mage_bolt_trail),
    ("R7 Boss血条 阶段刻度/低血脉动/狂暴横幅", v_boss_hud_renders),
    ("FX 4类贴图资源可加载", v_fx_textures_loaded),
    ("FX 4类贴图 draw 路径不报错", v_fx_draw_paths),
    ("回归 R3 新星/闪电/地雷不回归", v_r3_no_regression),
]


def _main():
    for name, fn in checks:
        check(name, fn)
    print()
    if FAILED:
        print("CONTENT_VERIFY_FAIL:", ", ".join(FAILED))
        rc = 1
    else:
        print("CONTENT_VERIFY_ALL_PASS")
        rc = 0
    out.close()
    return rc


if __name__ == "__main__":
    sys.exit(_main())
out.close()
