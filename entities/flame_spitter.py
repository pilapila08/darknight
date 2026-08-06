"""圣焰喷射器：短程锥形喷吐 + 燃烧 DoT。

依据：content-pack-v2.md §1.3（C02 新武器二）。
- 每 0.28s 向最近敌人方向喷出锥形火焰（长 170px、半角 30°），锥内全部敌人受直接
  伤害并附加 2.0s 燃烧 DoT（每 0.5s 一跳）。
- 直接伤害可暴击（复用 crit_chance/crit_multiplier，与 chain_lightning 一致）；
  燃烧不可暴击（复用 Enemy.apply_dot 机制）。
"""
import math
import random
import pygame

from settings import SKILL_DEFS

_FLAME = SKILL_DEFS["flame"]


class FlameSpitterManager:
    """圣焰喷射器管理器（参照 chain_lightning.py 结构）。"""

    def __init__(self):
        self.cooldown_timer = 0.0
        self._flames = []  # 绘制用火焰粒子（短橙线条，程序化）

    def update(self, dt, player_rect, enemies, stats):
        """每帧调用；返回 (enemy, dmg, dead) 列表，供上层结算击杀。"""
        # 清理绘制粒子
        for f in self._flames:
            f["age"] += dt
        self._flames = [f for f in self._flames if f["age"] < f["duration"]]

        if stats.get("has_flame", 0) <= 0:
            return []
        self.cooldown_timer -= dt
        if self.cooldown_timer > 0:
            return []
        interval = stats.get("flame_interval", _FLAME["base_interval"])
        self.cooldown_timer = interval

        damage = stats.get("flame_damage", _FLAME["base_damage"])
        burn = stats.get("flame_burn", _FLAME["burn_damage"])
        cone_len = _FLAME["cone_length"]
        half_angle = math.radians(_FLAME["cone_half_angle"])

        # 最近敌人方向为锥心轴
        best = None
        best_dist = float("inf")
        for e in enemies:
            d = math.hypot(e.rect.centerx - player_rect.centerx,
                           e.rect.centery - player_rect.centery)
            if d < best_dist:
                best_dist = d
                best = e
        if best is None:
            return []
        base_angle = math.atan2(best.rect.centery - player_rect.centery,
                                best.rect.centerx - player_rect.centerx)

        # 喷吐视觉粒子
        for _ in range(10):
            a = base_angle + random.uniform(-half_angle, half_angle)
            dist = random.uniform(20, cone_len)
            self._flames.append({
                "x": player_rect.centerx + math.cos(a) * dist,
                "y": player_rect.centery + math.sin(a) * dist,
                "age": 0.0,
                "duration": random.uniform(0.12, 0.2),
                "angle": a,
            })

        results = []
        crit_chance = stats.get("crit_chance", 0)
        crit_mult = stats.get("crit_multiplier", 2.0)
        for enemy in list(enemies):
            dx = enemy.rect.centerx - player_rect.centerx
            dy = enemy.rect.centery - player_rect.centery
            dist = math.hypot(dx, dy)
            if dist > cone_len:
                continue
            angle_to = math.atan2(dy, dx)
            diff = abs(((angle_to - base_angle + math.pi) % (2 * math.pi)) - math.pi)
            if diff > half_angle:
                continue
            dmg = damage
            if random.random() < crit_chance:
                dmg *= crit_mult
            enemy.apply_dot(_FLAME["burn_duration"], _FLAME["burn_tick"], burn)
            dead = enemy.take_damage(dmg)
            results.append((enemy, dmg, dead))
        return results

    def draw(self, screen, camera, player_rect, stats):
        for f in self._flames:
            life = 1.0 - f["age"] / max(0.001, f["duration"])
            pos = camera.apply(pygame.Rect(f["x"], f["y"], 0, 0))
            sx, sy = pos.x, pos.y
            length = 4 + 6 * life
            ex = sx - math.cos(f["angle"]) * length
            ey = sy - math.sin(f["angle"]) * length
            color = (255, int(150 + 105 * life), 40)
            pygame.draw.line(screen, color, (sx, sy), (ex, ey), 3)
