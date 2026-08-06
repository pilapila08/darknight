import math
import random
import pygame
from settings import (LIGHTNING_COOLDOWN, LIGHTNING_CHAIN_RANGE,
                      LIGHTNING_DECAY, LIGHTNING_COLOR, CYAN)
from effects.fx_textures import get_lightning_bolt


class LightningBolt:
    """Visual effect for a single lightning bolt segment."""
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.lifetime = 0.25
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def alive(self):
        return self.elapsed < self.lifetime

    def draw(self, screen, camera):
        alpha = int(200 * (1 - self.elapsed / self.lifetime))
        p1 = camera.apply(pygame.Rect(self.start[0], self.start[1], 0, 0))
        p2 = camera.apply(pygame.Rect(self.end[0], self.end[1], 0, 0))

        # C02 FX（fx-spec-v1.md §4）：单段纹理旋转+缩放 blit，保留随机抖动感
        fx = get_lightning_bolt()
        if fx is not None:
            dx, dy = p2.x - p1.x, p2.y - p1.y
            seg_len = math.hypot(dx, dy)
            if seg_len > 2:
                angle = math.degrees(math.atan2(dy, dx)) - 90  # 贴图竖直（96×256）
                surf = pygame.transform.rotozoom(fx, angle, max(0.05, seg_len / 256.0))
                surf.set_alpha(alpha)
                # 沿段方向加一点抖动偏移，保留闪电感
                jx = random.uniform(-4, 4)
                jy = random.uniform(-4, 4)
                screen.blit(surf, (p1.x - surf.get_width() // 2 + jx,
                                   p1.y - surf.get_height() // 2 + jy))
            return

        # 回退：程序化折线（原实现）
        points = [(p1.x, p1.y)]
        segments = 3
        for i in range(1, segments):
            t = i / segments
            px = p1.x + (p2.x - p1.x) * t + random.uniform(-8, 8)
            py = p1.y + (p2.y - p1.y) * t + random.uniform(-8, 8)
            points.append((px, py))
        points.append((p2.x, p2.y))
        if len(points) >= 2:
            fx_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(fx_surf, (*CYAN, max(35, alpha // 2)), False, points, 6)
            pygame.draw.lines(fx_surf, (210, 245, 255, alpha), False, points, 2)
            screen.blit(fx_surf, (0, 0))


class ChainLightning:
    def __init__(self):
        self.cooldown_timer = 0.0
        self.bolts = []

    def update(self, dt, player_rect, enemies, stats):
        self.cooldown_timer -= dt

        # Update existing bolts
        for bolt in self.bolts:
            bolt.update(dt)
        self.bolts = [b for b in self.bolts if b.alive]

        results = []  # (enemy, damage, dead)

        if self.cooldown_timer <= 0 and enemies:
            self.cooldown_timer = LIGHTNING_COOLDOWN

            # Find nearest enemy
            best = None
            best_dist = float("inf")
            for e in enemies:
                d = math.hypot(e.rect.centerx - player_rect.centerx,
                              e.rect.centery - player_rect.centery)
                if d < best_dist:
                    best_dist = d
                    best = e

            if best:
                # 使用stats中的闪电弹跳次数和伤害（兜底值 = 权威表 5跳/7伤，见 SKILL_DEFS）
                chain_count = stats.get("lightning_chains", 5)
                chain_count = max(1, chain_count)
                damage = stats.get("lightning_damage", 7)
                hit_ids = set()
                current = best
                prev_pos = (player_rect.centerx, player_rect.centery)

                for hop in range(chain_count):
                    if current is None:
                        break
                    # Crit check
                    final_dmg = damage
                    if random.random() < stats.get("crit_chance", 0):
                        final_dmg *= stats.get("crit_multiplier", 2.0)
                    dead = current.take_damage(final_dmg)
                    results.append((current, final_dmg, dead))

                    self.bolts.append(LightningBolt(prev_pos, current.rect.center))
                    hit_ids.add(id(current))
                    prev_pos = current.rect.center

                    # Find next target
                    next_target = None
                    next_dist = LIGHTNING_CHAIN_RANGE
                    for e in enemies:
                        if id(e) in hit_ids:
                            continue
                        d = math.hypot(e.rect.centerx - current.rect.centerx,
                                      e.rect.centery - current.rect.centery)
                        if d < next_dist:
                            next_dist = d
                            next_target = e
                    current = next_target
                    damage *= LIGHTNING_DECAY

        return results

    def draw(self, screen, camera):
        for bolt in self.bolts:
            bolt.draw(screen, camera)
