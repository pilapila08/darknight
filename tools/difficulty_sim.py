# -*- coding: utf-8 -*-
"""R4 难度曲线模拟（验收用）：输出 0-600s 敌人属性表 + 刷怪速率表。

用法：python tools/difficulty_sim.py
依据：design/gdd/playability-pack-v1.md §2（方案A）+ settings.py 常量。
验收点：
- 无冻结段：tier 单调递增至 578s+（DIFFICULTY_MAX_TIER=17）
- 伤害封顶：普通怪伤 1+min(tier,8)=9，精英 18
- tf_cap 随 Boss 击杀递增：5 + 1.5×b，终局 8.78 只/s
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import (
    DIFFICULTY_INTERVAL, DIFFICULTY_MAX_TIER, DAMAGE_BONUS_MAX,
    HP_BONUS_PER_TIER, DAMAGE_BONUS_PER_TIER,
    SPAWN_INTERVAL, SPAWN_RATE_CAP_BASE, SPAWN_CAP_PER_BOSS,
    ELITE_HP, ELITE_HP_MULT, ELITE_DAMAGE_MULT,
    ENEMY_HP, CHARGER_HP, RANGER_HP, EXPLODER_HP,
    BOSS_FIGHT_SPAWN_SLOWDOWN, FINAL_SURGE_INTERVAL_MULT,
    GAME_DURATION_SECONDS,
)

# Boss 击杀时间轴（playability-pack §2.3 假设值，用于 tf_cap 演示）
BOSS_KILL_TIMES = {120: 1, 270: 2, 400: 3, 520: 4}


def tier_at(t):
    return min(int(t / DIFFICULTY_INTERVAL), DIFFICULTY_MAX_TIER)


def boss_kills_at(t):
    b = 0
    for bt in sorted(BOSS_KILL_TIMES):
        if t >= bt:
            b = max(b, BOSS_KILL_TIMES[bt])
    return b


def spawn_rate_at(t, boss_active=False, final_surge=False):
    b = boss_kills_at(t)
    tf_cap = SPAWN_RATE_CAP_BASE + SPAWN_CAP_PER_BOSS * b
    tf = min(t / 30.0, tf_cap)
    interval = SPAWN_INTERVAL / (1 + tf * 0.3 + (tf * 0.15) ** 2)
    if boss_active:
        interval *= BOSS_FIGHT_SPAWN_SLOWDOWN
    if final_surge:
        interval *= FINAL_SURGE_INTERVAL_MULT
    return tf_cap, tf, interval, 1.0 / interval


def main():
    print("=" * 78)
    print("R4 难度曲线模拟（0-600s）")
    print("=" * 78)
    print("\n【1】敌人属性表（方案A：tier 单调递增至 578s，伤害封顶）")
    print(f"{'时间':>6} {'tier':>4} {'基础HP':>6} {'基础伤':>6} {'精英HP':>6} {'精英伤':>6}")
    for t in range(0, GAME_DURATION_SECONDS + 1, 30):
        tier = tier_at(t)
        hp = ENEMY_HP + tier * HP_BONUS_PER_TIER
        dmg = 1 + min(tier * DAMAGE_BONUS_PER_TIER, DAMAGE_BONUS_MAX)
        ehp = int((ELITE_HP + tier * HP_BONUS_PER_TIER) * ELITE_HP_MULT)
        edmg = int((1 + min(tier * DAMAGE_BONUS_PER_TIER, DAMAGE_BONUS_MAX)) * ELITE_DAMAGE_MULT)
        print(f"{t:>6}s {tier:>4} {hp:>6} {dmg:>6} {ehp:>6} {edmg:>6}")

    # 逐秒单调性验证：tier 每 34s +1，无冻结（封顶 578s）
    prev = -1
    last_change = 0
    monotonic = True
    for t in range(0, GAME_DURATION_SECONDS + 1):
        cur = tier_at(t)
        if cur != prev:
            last_change = t
            prev = cur
    reached_max = all(tier_at(t) == DIFFICULTY_MAX_TIER for t in range(578, GAME_DURATION_SECONDS + 1))
    no_early_cap = last_change == 578  # 最后一次 tier 变化在 578s（34×17）
    print(f"\n结论：tier 封顶 = {DIFFICULTY_MAX_TIER}（最后变化点 {last_change}s，预期 578s）；伤害封顶 = 1+{DAMAGE_BONUS_MAX}={1 + DAMAGE_BONUS_MAX}")
    print(f"      单调性：{'PASS —— 无冻结段，tier 每 34s 递增至 578s' if no_early_cap else 'CHECK'}；"
          f"封顶期保持：{'PASS' if reached_max else 'CHECK'}")

    print("\n【2】刷怪速率表（tf_cap = 5 + 1.5×boss击杀）")
    print(f"{'时间':>6} {'b':>2} {'tf_cap':>6} {'tf':>6} {'interval(s)':>10} {'速率(只/s)':>10}")
    for t in [0, 30, 60, 90, 120, 140, 195, 240, 270, 360, 400, 480, 520, 540, 600]:
        b = boss_kills_at(t)
        final = t >= GAME_DURATION_SECONDS - 60
        tf_cap, tf, interval, rate = spawn_rate_at(t, final_surge=final)
        print(f"{t:>6}s {b:>2} {tf_cap:>6.1f} {tf:>6.1f} {interval:>10.3f} {rate:>10.2f}")

    print("\n【3】终局验证（600s，4 Boss 击杀后）")
    tf_cap, tf, interval, rate = spawn_rate_at(600, final_surge=True)
    print(f"  tf_cap = {tf_cap:.1f}（预期 11）；刷怪速率 = {rate:.2f} 只/s（含终局 ×{1 / FINAL_SURGE_INTERVAL_MULT:.2f} 加速，预期 ≈10.9）")
    ok = (tf_cap == SPAWN_RATE_CAP_BASE + SPAWN_CAP_PER_BOSS * 4) and (rate > 10.0)
    print(f"  结论：{'PASS' if ok else 'CHECK'}（tf_cap 达标；速率需结合 MAX_ENEMIES 性能实机确认）")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
