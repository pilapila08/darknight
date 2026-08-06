"""凛冬之环：以玩家为中心的冰霜光环（贴身减速 AOE）。

依据：content-pack-v2.md §1.2（C02 新武器一）。
- 光环内敌人每 0.5s 受 1 次冰伤，并被减速（直接覆盖 speed，基于 _base_speed，
  离开光环立即恢复——避免多次乘法累积）。
- 减速按层数叠加：第 N 层总减速 = slow_base + slow_per_stack×(N−1)，上限 slow_max。
- 全武器池中唯一的控制/减速维度；激活 Enemy.apply_frostbite 死钩子（本项目首个调用方）。
"""
import math
import pygame

from settings import CYAN, SKILL_DEFS

_FROST = SKILL_DEFS["frost"]


class FrostAuraManager:
    """凛冬之环光环管理器（参照 orbital_blade.py 结构）。"""

    def __init__(self):
        self.tick_timer = 0.0
        self._pulse = 0.0  # 绘制脉冲相位

    def update(self, dt, player_rect, enemies, stats):
        """每帧调用；返回 (enemy, dmg, dead) 列表，供上层结算击杀。"""
        if stats.get("has_frost", 0) <= 0:
            return []
        radius = stats.get("frost_radius", _FROST["base_radius"])
        damage = stats.get("frost_damage", _FROST["base_damage"])
        slow = stats.get("frost_slow", _FROST["slow_base"])
        tick_interval = _FROST["tick_interval"]

        self.tick_timer += dt
        self._pulse += dt
        tick_now = self.tick_timer >= tick_interval
        if tick_now:
            self.tick_timer -= tick_interval

        results = []
        for enemy in list(enemies):
            dx = enemy.rect.centerx - player_rect.centerx
            dy = enemy.rect.centery - player_rect.centery
            inside = math.hypot(dx, dy) <= radius + getattr(enemy, "_size", enemy.rect.width) * 0.5

            # 减速：直接覆盖 speed（基于 _base_speed），离开光环恢复
            base_speed = getattr(enemy, "_base_speed", enemy.speed)
            if inside:
                enemy.speed = base_speed * (1 - slow)
            else:
                enemy.speed = base_speed

            if inside and tick_now:
                dead = enemy.take_damage(damage)
                results.append((enemy, damage, dead))
        return results

    def draw(self, screen, camera, player_rect, stats):
        if stats.get("has_frost", 0) <= 0:
            return
        radius = stats.get("frost_radius", _FROST["base_radius"])
        t = self._pulse
        pulse = 0.5 + 0.5 * math.sin(t * 6.0)
        pos = camera.apply(pygame.Rect(player_rect.centerx, player_rect.centery, 0, 0))
        r = max(1, int(radius * (1.0 + 0.04 * pulse)))
        size = r * 2 + 12
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        alpha = int(60 + 40 * pulse)
        pygame.draw.circle(surf, (*CYAN, alpha // 2), (c, c), r)
        pygame.draw.circle(surf, (*CYAN, min(255, alpha + 60)), (c, c), r, 2)
        screen.blit(surf, (pos.x - c, pos.y - c))
