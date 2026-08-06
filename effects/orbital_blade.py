import math
import pygame

from settings import CYAN, PURPLE, SKILL_DEFS
from effects.fx_textures import get_nova_ring

_NOVA = SKILL_DEFS["nova"]


class OrbitalBladeManager:
    """Backward-compatible manager for the Shadow Nova skill."""

    def __init__(self):
        self.cooldown_timer = 0.0
        self.pulses = []

    def set_count(self, count):
        # Kept for compatibility with GameState.apply_skill_update.
        return

    def update(self, dt):
        self.cooldown_timer -= dt
        for pulse in self.pulses:
            pulse["age"] += dt
        self.pulses = [p for p in self.pulses if p["age"] < p["duration"]]

    def check_damage(self, player_rect, enemies, dt, stats):
        cooldown = stats.get("nova_cooldown", _NOVA["base_cooldown"])
        if self.cooldown_timer > 0:
            return []
        self.cooldown_timer = cooldown

        radius = stats.get("nova_radius", _NOVA["base_radius"])
        damage = stats.get("blade_damage", _NOVA["base_damage"])
        self.pulses.append({
            "x": player_rect.centerx,
            "y": player_rect.centery,
            "radius": radius,
            "age": 0.0,
            "duration": 0.42,
        })

        results = []
        for enemy in enemies:
            dx = enemy.rect.centerx - player_rect.centerx
            dy = enemy.rect.centery - player_rect.centery
            dist = math.hypot(dx, dy)
            if dist <= radius + getattr(enemy, "_size", enemy.rect.width) * 0.5:
                falloff = 0.72 + 0.28 * (1 - min(1.0, dist / max(1, radius)))
                dmg = damage * falloff
                dead = enemy.take_damage(dmg)
                if dist > 0:
                    enemy.rect.x += (dx / dist) * 16
                    enemy.rect.y += (dy / dist) * 16
                results.append((enemy, dmg, dead))
        return results

    def draw(self, screen, camera, player_rect):
        for pulse in self.pulses:
            progress = min(1.0, pulse["age"] / pulse["duration"])
            radius = max(1, int(pulse["radius"] * progress))
            alpha = int(180 * (1 - progress))
            pos = camera.apply(pygame.Rect(pulse["x"], pulse["y"], 0, 0))

            # C02 FX（fx-spec-v1.md §3）：优先 blit 环形贴图（冲击波感更明显）
            fx = get_nova_ring()
            if fx is not None:
                size = max(4, radius * 2 + 8)
                surf = pygame.transform.scale(fx, (size, size))
                surf.set_alpha(alpha)
                screen.blit(surf, (pos.x - size // 2, pos.y - size // 2))
                continue

            # 回退：程序化三层圆（原实现）
            size = radius * 2 + 8
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            center = size // 2
            pygame.draw.circle(surf, (*PURPLE, max(20, alpha // 3)), (center, center), radius)
            pygame.draw.circle(surf, (*CYAN, alpha), (center, center), radius, 3)
            pygame.draw.circle(surf, (235, 220, 255, min(255, alpha + 40)),
                               (center, center), max(1, int(radius * 0.55)), 2)
            screen.blit(surf, (pos.x - center, pos.y - center))

        cooldown = max(0.0, self.cooldown_timer)
        if cooldown > 0:
            ready = 1 - min(1.0, cooldown / _NOVA["base_cooldown"])
            radius = 24 + int(10 * ready)
            pos = camera.apply(pygame.Rect(player_rect.centerx, player_rect.centery, 0, 0))
            surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (120, 80, 210, 45), (radius + 2, radius + 2), radius, 2)
            screen.blit(surf, (pos.x - radius - 2, pos.y - radius - 2))
