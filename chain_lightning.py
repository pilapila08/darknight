import math
import random
import pygame
from settings import (LIGHTNING_COOLDOWN, LIGHTNING_DAMAGE, LIGHTNING_CHAINS,
                      LIGHTNING_CHAIN_RANGE, LIGHTNING_DECAY, LIGHTNING_COLOR, CYAN)


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
        color = (*CYAN, alpha)
        p1 = camera.apply(pygame.Rect(self.start[0], self.start[1], 0, 0))
        p2 = camera.apply(pygame.Rect(self.end[0], self.end[1], 0, 0))
        # Draw a jagged line between p1 and p2
        points = [(p1.x, p1.y)]
        segments = 3
        for i in range(1, segments):
            t = i / segments
            px = p1.x + (p2.x - p1.x) * t + random.uniform(-8, 8)
            py = p1.y + (p2.y - p1.y) * t + random.uniform(-8, 8)
            points.append((px, py))
        points.append((p2.x, p2.y))
        if len(points) >= 2:
            pygame.draw.lines(screen, color, False, points, 2)


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
                chain_count = LIGHTNING_CHAINS + (stats.get("bullet_count", 1) - 1) + (stats.get("has_lightning", 1) - 1)
                chain_count = max(1, chain_count)
                damage = LIGHTNING_DAMAGE
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
                    # Frostbite
                    if stats.get("has_frostbite", 0) > 0:
                        current.apply_frostbite(0.8)

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
