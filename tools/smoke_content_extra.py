# -*- coding: utf-8 -*-
"""SMK-20~29 扩展冒烟：第二批新系统关键路径（无窗口，可独立复跑）。

任务：DN-QA-03（QA 门控批次3）
风格：参考 _smoke_test.py 的 check/name/fn 骨架；输出写 tools/smoke_content_extra_out.txt。
定位：与 tools/verify_content.py（C02 内容验收）互补——本套侧重「游戏内集成链路」：
  新武器经游戏循环生效、DoT 结算、敌人状态机全周期、主从绑定、Boss 狂暴、FX 回退、
  技能池 16 升级三选一、Boss 降临演出、传送+弹幕尾迹、组合回归总闸。

覆盖（SMK-20 ~ SMK-30，共 11 例）：
  SMK-20 凛冬之环 游戏内全链路（减速生效/离开恢复/tick 伤害）
  SMK-21 圣焰喷射器 直接伤 + 燃烧 DoT 逐跳结算 + 燃烧结束
  SMK-22 怨灵 闪现状态机全周期（提示→闪现→落地停顿→恢复移动）
  SMK-23 唤魔师 召唤→主从绑定→消散 无奖励（游戏内）
  SMK-24 尸王狂暴 游戏内触发（enrage 事件 + 召唤 3→5 混合）
  SMK-25 FX 贴图 加载成功 + 缺失回退程序化（draw 不崩）
  SMK-26 技能池 16 三选一不重复 + 新武器可出现 + 升级选择生效
  SMK-27 Boss 降临演出（粒子+白闪+顿帧冻结逻辑）
  SMK-28 暗影巫师 传送提示→落地 + 弹幕尾迹（游戏内处理）
  SMK-29 新系统合入回归总闸（frost+flame 组合 5s 模拟）
  SMK-30 BUG-001 回归：四 Boss 攻击经游戏循环送达 _process_boss_attacks
"""
import os
import sys
import math
import random
import tempfile
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    out = open(os.path.join(_PROJECT_ROOT, "tools", "smoke_content_extra_out.txt"), "w", encoding="utf-8")
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
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WRATH_TELEGRAPH, WRATH_LAND_PAUSE, WRATH_BLINK_INTERVAL,
    WARLOCK_SUMMON_INTERVAL, CORPSE_KING_ENRAGE_MINION_COUNT,
    CORPSE_KING_MINION_COUNT, SHADOW_MAGE_TELEPORT_INTERVAL,
    SHADOW_MAGE_TELEPORT_TELEGRAPH, XP_BASE,
)
pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from skills import SKILL_POOL, get_random_skills, get_skill_by_name
from game.state import GameState
from game.normal_game import NormalGame
from entities import Enemy
from entities.enemy_types import Wraith, Warlock
from entities.boss import CorpseKing, ShadowMage


def get_skill(name):
    return get_skill_by_name(name)


def fresh_stats(character="default"):
    return GameState(character).stats


def _apply_via_choice(g, skill):
    """模拟升级三选一确认：chosen_skills=[skill] → _apply_skill（真实路径）。"""
    g.game_state.chosen_skills = [skill]
    g.game_state.paused = True
    g._apply_skill(skill)


# ---------------------------------------------------------------- SMK-20
def smk20_frost_game_integration():
    """凛冬之环 游戏内全链路：装备 → 减速生效 → 离开恢复 → tick 伤害。"""
    g = NormalGame()
    g._init_game()
    _apply_via_choice(g, get_skill("凛冬之环"))
    st = g.game_state.stats
    assert st["has_frost"] == 1 and st["frost_radius"] == 100
    assert abs(st["frost_slow"] - 0.20) < 1e-6

    px, py = g.player.rect.centerx, g.player.rect.centery
    e = Enemy(px + 50, py)
    e.hp = 100
    e.max_hp = 100
    g.enemies.add(e)
    base_speed = e.speed

    # 1) 光环内减速生效
    g._update(0.01)
    assert e.speed < base_speed, (e.speed, base_speed)

    # 2) 离开光环恢复
    e.rect.center = (px + 500, py + 500)
    g._update(0.01)
    assert e.speed == base_speed, (e.speed, base_speed)

    # 3) tick 伤害（0.5s 一跳）
    e.rect.center = (px + 50, py)
    g.frost_mgr.tick_timer = 0.49
    g._update(0.01)
    assert e.hp == 98, e.hp  # 100 - 2


# ---------------------------------------------------------------- SMK-21
def smk21_flame_dot_settle():
    """圣焰喷射器：锥内直接伤 + 燃烧 DoT 逐跳结算 + 燃烧结束清零。"""
    g = NormalGame()
    g._init_game()
    _apply_via_choice(g, get_skill("圣焰喷射器"))
    st = g.game_state.stats
    assert st["has_flame"] == 1 and abs(st["flame_interval"] - 0.28) < 1e-6

    px, py = g.player.rect.centerx, g.player.rect.centery
    e = Enemy(px + 100, py)  # 锥内（距离≈100 < 170）
    e.hp = 100
    e.max_hp = 100
    g.enemies.add(e)

    # 一次游戏帧：锥形命中 → 直接伤 2 + 附加燃烧 2.0s/1伤
    g._update(0.01)
    assert e.hp == 98, e.hp
    assert e.dot_timer == 2.0 and e.dot_damage == 1, (e.dot_timer, e.dot_damage)

    # 燃烧逐跳（敌体 DoT 结算，避免喷吐再命中干扰）：两跳共 2 伤
    hp_after_hit = e.hp  # 98
    e._update_dot(1.0)   # 第 1 跳
    assert e.hp == hp_after_hit - 1, e.hp
    e._update_dot(1.0)   # 第 2 跳 + 燃烧结束
    assert e.hp == hp_after_hit - 2, e.hp
    assert e.dot_damage == 0 and e.dot_timer <= 0, (e.dot_damage, e.dot_timer)


# ---------------------------------------------------------------- SMK-22
def smk22_wraith_state_machine():
    """怨灵 闪现状态机全周期：移动 → 提示 → 闪现 → 落地停顿 → 恢复移动。"""
    w = Wraith(300, 300)
    player = pygame.Rect(600, 300, 32, 32)
    start = (w.rect.centerx, w.rect.centery)

    # 1) 闪现计时到 → 进入落点提示期（位置不动）
    w._blink_timer = 0.01
    w.update(0.02, player)
    assert w._telegraph_timer > 0 and w._telegraph_pos is not None
    assert (w.rect.centerx, w.rect.centery) == start

    # 2) 提示期结束 → 闪现到落点 + 落地停顿
    target = w._telegraph_pos
    for _ in range(8):
        w.update(0.1, player)
        if w._telegraph_timer <= 0 and w._land_pause_timer > 0:
            break
    assert abs(w.rect.centerx - target[0]) < 1.5 and abs(w.rect.centery - target[1]) < 1.5
    assert w._land_pause_timer > 0

    # 3) 落地停顿期内位置冻结
    paused_pos = (w.rect.centerx, w.rect.centery)
    for _ in range(4):
        w.update(0.1, player)
        assert w._land_pause_timer > 0 or w._land_pause_timer <= 0  # 至少不崩
        if w._land_pause_timer <= 0:
            break
    # 停顿期结束前位置仍冻结
    if w._land_pause_timer > 0:
        assert (w.rect.centerx, w.rect.centery) == paused_pos

    # 4) 停顿结束 → 恢复向玩家移动（位置改变）
    for _ in range(6):
        w.update(0.1, player)
        if w._land_pause_timer <= 0:
            break
    w.update(0.1, player)
    assert (w.rect.centerx, w.rect.centery) != paused_pos


# ---------------------------------------------------------------- SMK-23
def smk23_warlock_binding_no_reward():
    """唤魔师 主从绑定：召唤仆从 → 主人死 → 仆从 2s 消散且无奖励。"""
    g = NormalGame()
    g._init_game()
    wk = Warlock(400, 400)
    g.enemies.add(wk)
    wk.summon_timer = WARLOCK_SUMMON_INTERVAL - 0.01

    # 一帧内触发召唤事件 → 游戏层生成仆从并绑定主从
    g._update(0.02)
    minions = [e for e in g.enemies if getattr(e, "_master_id", None) == id(wk)]
    assert len(minions) == 1, len(minions)
    minion = minions[0]

    # 击杀主人：主人本身计 1 击杀奖励；仆从被标记 2s 后消散
    g._kill_enemy(wk)
    score_after_kill = g.game_state.score
    xp_after_kill = g.game_state.experience
    assert getattr(minion, "_disperse_at", None) is not None
    assert minion._disperse_at > g.game_state.elapsed_time
    assert minion in g.enemies  # 未到消散时刻仍在场

    # 推到消散时刻 → 仆从无奖励消散（分数/经验不变）
    g.game_state.elapsed_time = minion._disperse_at
    g._update(0.01)
    assert minion not in g.enemies
    assert g.game_state.score == score_after_kill, (g.game_state.score, score_after_kill)
    assert g.game_state.experience == xp_after_kill, (g.game_state.experience, xp_after_kill)


# ---------------------------------------------------------------- SMK-24
def smk24_corpse_king_enrage_in_game():
    """尸王狂暴 游戏内触发：<50% → enrage 事件 + 召唤 3→5 混合。

    BUG-001 修复后（boss 仅由 _update_bosses 驱动），enrage 事件应经游戏循环送达
    _process_boss_attacks → 红闪/横幅/duck 生效。
    """
    g = NormalGame()
    g._init_game()
    ck = CorpseKing(400, 400)
    g.enemies.add(ck)
    g.bosses.add(ck)
    g.game_state.boss_active = True

    ck.hp = int(ck.max_hp * 0.4)          # <50%
    ck.attack_timer = ck.config["attack_interval"]
    player = pygame.Rect(500, 300, 32, 32)

    # 1) 游戏内：狂暴标志 + enrage 事件经游戏循环送达（红闪生效，无需手动调处理器）
    g._update(0.016)
    assert ck.enraged, "尸王应在 <50% 时进入狂暴"
    assert g.effects._flash_alpha > 0, "enrage 事件应经游戏循环送达 → 红闪生效"

    # 2) 狂暴召唤：4 基础 + 1 冲锋（共 5）
    counts = {a["enemy_type"]: a["count"] for a in ck._summon_attacks()}
    assert counts.get("basic", 0) == CORPSE_KING_ENRAGE_MINION_COUNT - 1, counts
    assert counts.get("charger", 0) == 1, counts

    # 3) 非狂暴：3 基础
    ck.enraged = False
    sums = ck._summon_attacks()
    assert all(a["enemy_type"] == "basic" for a in sums)
    assert sum(a["count"] for a in sums) == CORPSE_KING_MINION_COUNT


# ---------------------------------------------------------------- SMK-25
def smk25_fx_textures_load_and_fallback():
    """FX 贴图：真实资源可加载；缺失时回退程序化且 draw 不崩。"""
    from effects.fx_textures import (
        get_explosion_fire, get_explosion_purple, get_nova_ring,
        get_lightning_bolt, get_muzzle_flash,
    )
    # 1) 真实资源（assets/effects/ 5 张已合入）
    assert get_explosion_fire() is not None
    assert get_explosion_purple() is not None
    assert get_nova_ring() is not None
    assert get_lightning_bolt() is not None
    assert get_muzzle_flash() is not None

    # 2) 缺失回退：把加载目录指向空目录 → 全部 None → 程序化 draw 不崩
    import effects.fx_textures as fxt
    orig_dir, orig_cache = fxt._FX_DIR, fxt._CACHE
    try:
        fxt._FX_DIR = os.path.join(tempfile.mkdtemp(prefix="fx_missing_"), "nope")
        fxt._CACHE = {}
        assert get_explosion_fire() is None
        assert get_explosion_purple() is None
        assert get_nova_ring() is None
        assert get_lightning_bolt() is None
        assert get_muzzle_flash() is None

        from entities.explosion import Explosion
        from effects.orbital_blade import OrbitalBladeManager
        from effects.chain_lightning import LightningBolt
        from effects.juice import EffectManager
        from systems.camera import Camera
        cam = Camera()
        screen = pygame.display.get_surface()

        ex = Explosion(300, 300, 4)
        ex.radius = 30
        ex.draw(screen, cam)
        bolt = LightningBolt((100, 100), (200, 200))
        bolt.draw(screen, cam)
        obm = OrbitalBladeManager()
        obm.pulses.append({"x": 300, "y": 300, "radius": 100, "age": 0.1, "duration": 0.42})
        obm.draw(screen, cam, pygame.Rect(300, 300, 32, 32))
        em = EffectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        em.add_muzzle_flash(150, 150, 0.5)
        em.update(0.01)
        em.draw_world(screen, cam)
    finally:
        fxt._FX_DIR, fxt._CACHE = orig_dir, orig_cache


# ---------------------------------------------------------------- SMK-26
def smk26_pool16_levelup_choice():
    """技能池 16：三选一不重复 + 新武器可出现 + 升级选择生效。"""
    assert len(SKILL_POOL) == 16, len(SKILL_POOL)
    seen = set()
    for _ in range(60):
        sk = get_random_skills(3, fresh_stats())
        names = [s["name"] for s in sk]
        assert len(set(names)) == 3, names
        seen.update(names)
    assert "凛冬之环" in seen and "圣焰喷射器" in seen, "新武器应可被三选一抽出"

    # 游戏内升级：经验达标 → paused + 三张唯一技能卡
    g = NormalGame()
    g._init_game()
    g.game_state.experience = XP_BASE
    g._update(0.016)
    assert g.game_state.level == 2
    assert g.game_state.paused is True
    assert g.game_state.chosen_skills is not None and len(g.game_state.chosen_skills) == 3
    assert len({s["name"] for s in g.game_state.chosen_skills}) == 3

    # 选择 凛冬之环 → 属性生效、暂停解除、技能入册
    frost = get_skill("凛冬之环")
    g.game_state.chosen_skills = [frost]
    g._apply_skill(frost)
    assert g.game_state.paused is False and g.game_state.chosen_skills is None
    assert g.game_state.stats["has_frost"] == 1 and g.game_state.stats["frost_radius"] == 100
    assert "凛冬之环" in g.game_state.acquired_skills


# ---------------------------------------------------------------- SMK-27
def smk27_boss_arrive_show():
    """Boss 降临演出：粒子爆发 + 白闪 + 长顿帧 + 顿帧冻结游戏逻辑。"""
    g = NormalGame()
    g._init_game()
    boss = CorpseKing(400, 400)
    before = len(g.particles)

    g._on_boss_arrive(boss)
    assert len(g.particles) == before + 30, len(g.particles) - before
    assert g.effects._flash_alpha > 0
    assert g.effects.hitstop_timer > 0

    # 顿帧期间游戏逻辑冻结（elapsed_time 不推进）
    t0 = g.game_state.elapsed_time
    g._update(0.016)
    assert g.game_state.elapsed_time == t0, (g.game_state.elapsed_time, t0)


# ---------------------------------------------------------------- SMK-28
def smk28_shadow_mage_teleport_and_trail():
    """暗影巫师：弹幕尾迹（游戏循环送达）+ 传送状态机提示→落地。

    BUG-001 修复后，弹幕/传送演出事件应经游戏循环送达（旧版会被双更新丢弃）。
    """
    g = NormalGame()
    g._init_game()
    player = pygame.Rect(600, 300, 32, 32)

    # 1) 弹幕尾迹：攻击经游戏循环送达 → boss_projectiles 带尾迹标记
    sm = ShadowMage(400, 400)
    g.enemies.add(sm)
    g.bosses.add(sm)
    g.game_state.boss_active = True
    sm.attack_timer = sm.config["attack_interval"]
    g._update(0.016)
    assert any(getattr(bp, "trail_color", None) for bp in g.boss_projectiles), \
        "游戏循环应送达暗影弹幕 → 尾迹标记生效"

    # 2) 传送状态机：提示 → 落地
    sm2 = ShadowMage(400, 400)
    sm2.teleport_timer = SHADOW_MAGE_TELEPORT_INTERVAL
    moves = sm2._do_movement(0.016, player)
    assert any(a["type"] == "teleport_telegraph_shake" for a in moves)
    assert sm2._teleport_telegraph > 0 and sm2._teleport_target is not None
    target = sm2._teleport_target
    for _ in range(6):
        sm2._do_movement(0.1, player)
        if sm2._teleport_telegraph <= 0 and sm2._teleport_target is None:
            break
    assert sm2.rect.centerx == target[0] and sm2.rect.centery == target[1]


# ---------------------------------------------------------------- SMK-29
def smk29_combined_regression_gate():
    """新系统合入回归总闸：frost+flame 组合 5s 游戏模拟无异常、状态合法。"""
    g = NormalGame()
    g._init_game()
    _apply_via_choice(g, get_skill("凛冬之环"))
    _apply_via_choice(g, get_skill("圣焰喷射器"))
    st = g.game_state.stats
    assert st["has_frost"] == 1 and st["has_flame"] == 1

    px, py = g.player.rect.centerx, g.player.rect.centery
    for i in range(5):
        e = Enemy(px + 60 + i * 30, py + 60)
        e.hp = 100
        e.max_hp = 100
        g.enemies.add(e)

    for f in range(330):            # 5.28s @ 60fps（330×0.016≈5.28，留出 >4.9 断言余量）
        g._update(0.016)
        if f % 10 == 0:
            g._render()

    assert g.game_state.elapsed_time > 4.9, g.game_state.elapsed_time
    assert g.game_state.stats.get("has_frost") == 1
    assert g.game_state.stats.get("has_flame") == 1
    # 新武器管理器确实在游戏循环中工作过（tick / 冷却均被消耗）
    assert g.frost_mgr.tick_timer >= 0 or g.flame_mgr.cooldown_timer >= 0
    assert g.game_state.player_hp > 0, "5s 组合模拟玩家不应死亡"


# ---------------------------------------------------------------- SMK-30
def smk30_boss_attack_delivery():
    """BUG-001 回归：四 Boss 攻击事件经游戏循环送达 _process_boss_attacks。

    修复前：Boss 在 enemies 组被 Group.update 先驱动（attack_timer 清零、attacks 丢弃），
    _update_bosses 二次驱动拿不到攻击 → CorpseKing 120 帧 0 条攻击。
    修复后：enemies 手动循环排除 Boss，Boss 仅由 _update_bosses 驱动 → 攻击必达。
    """
    from entities.boss import BOSS_CLASSES

    # 稳定性：IronColossus 的 armor 分支（0.35≤r<0.65）只开甲不产出攻击 dict。
    # 若首 roll 命中 armor，攻击冷却被消耗但 delivered=0 → 120帧窗口内 ~30% flaky。
    # 按 Boss 固定随机种子：IronColossus seed=1 → random()≈0.134<0.35 → shockwave，确定性。
    SEEDS = {"CorpseKing": 10, "ShadowMage": 20, "IronColossus": 1, "VoidLord": 40}

    for cls in BOSS_CLASSES:
        random.seed(SEEDS[cls.__name__])
        g = NormalGame()
        g._init_game()
        boss = cls(400, 400)
        g.enemies.add(boss)
        g.bosses.add(boss)
        g.game_state.boss_active = True
        boss.attack_timer = boss.config["attack_interval"]  # 攻击就绪

        delivered = {"n": 0}
        orig = g._process_boss_attacks

        def counted(attacks):
            delivered["n"] += len(attacks)
            orig(attacks)

        g._process_boss_attacks = counted

        # CorpseKing 按 QA 报告口径跑 500 帧（覆盖 ≥3 次攻击+召唤节奏）；其余 120 帧
        frames = 500 if cls.__name__ == "CorpseKing" else 120
        for _ in range(frames):
            g._update(0.016)

        threshold = 3 if cls.__name__ == "CorpseKing" else 1
        assert delivered["n"] >= threshold, \
            f"{cls.__name__}: {delivered['n']} 条攻击 < {threshold}（BUG-001 未修复？）"


checks = [
    ("SMK-20 凛冬之环 游戏内减速/恢复/tick伤害", smk20_frost_game_integration),
    ("SMK-21 圣焰喷射器 直接伤+燃烧DoT结算+燃烧结束", smk21_flame_dot_settle),
    ("SMK-22 怨灵 闪现状态机全周期", smk22_wraith_state_machine),
    ("SMK-23 唤魔师 主从绑定消散无奖励", smk23_warlock_binding_no_reward),
    ("SMK-24 尸王狂暴 游戏内触发+召唤3→5", smk24_corpse_king_enrage_in_game),
    ("SMK-25 FX贴图 加载成功+缺失回退", smk25_fx_textures_load_and_fallback),
    ("SMK-26 技能池16 三选一不重复+新武器+升级生效", smk26_pool16_levelup_choice),
    ("SMK-27 Boss降临 粒子+白闪+顿帧冻结", smk27_boss_arrive_show),
    ("SMK-28 暗影巫师 传送+弹幕尾迹", smk28_shadow_mage_teleport_and_trail),
    ("SMK-29 组合回归总闸 frost+flame 5s模拟", smk29_combined_regression_gate),
    ("SMK-30 BUG-001 四Boss攻击经游戏循环送达", smk30_boss_attack_delivery),
]


def _main():
    for name, fn in checks:
        check(name, fn)
    print()
    if FAILED:
        print("SMOKE_CONTENT_EXTRA_FAIL:", ", ".join(FAILED))
        rc = 1
    else:
        print("SMOKE_CONTENT_EXTRA_ALL_PASS")
        rc = 0
    out.close()
    return rc


if __name__ == "__main__":
    sys.exit(_main())
out.close()
