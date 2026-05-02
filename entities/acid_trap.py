import math
import pygame
from settings import (TRAP_DURATION, TRAP_RADIUS, TRAP_DOT_DURATION,
                      TRAP_DOT_TICK, TRAP_COLOR, TRAP_INTERVAL)


class AcidTrap(pygame.sprite.Sprite):
    def __init__(self, x, y, trap_damage=4, radius_mult=1.0):
        super().__init__()
        self.trap_damage = trap_damage
        self.radius = int(TRAP_RADIUS * radius_mult)
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*TRAP_COLOR, 120),
                          (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=(x, y))
        self.center = (x, y)
        self.lifetime = TRAP_DURATION
        self._affected_enemies = {}  # enemy_id -> remaining_duration

    def update(self, dt):
        self.lifetime -= dt
        alpha = int(120 * max(0, min(1, self.lifetime / 2.0)))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (*TRAP_COLOR, alpha),
                          (self.radius, self.radius), self.radius)
        if self.lifetime <= 0:
            self.kill()

    def check_enemies(self, enemies):
        """Apply/refresh DoT to enemies within the trap radius."""
        results = []
        for enemy in enemies:
            # 使用距离检测，比rect碰撞更可靠
            dist = math.hypot(enemy.rect.centerx - self.center[0],
                            enemy.rect.centery - self.center[1])
            if dist < self.radius + enemy._size / 2:
                enemy_id = id(enemy)
                # 刷新或重新应用DoT
                self._affected_enemies[enemy_id] = TRAP_DOT_DURATION
                enemy.apply_dot(TRAP_DOT_DURATION, TRAP_DOT_TICK, self.trap_damage)
                results.append(enemy)
        return results


class TrapManager:
    def __init__(self):
        self.timer = 0.0
        self.group = pygame.sprite.Group()

    def update(self, dt, player, is_moving, interval=None, trap_damage=4, radius_mult=1.0):
        if interval is None:
            interval = TRAP_INTERVAL
        if is_moving:
            self.timer += dt
            while self.timer >= interval:
                self.timer -= interval
                self.group.add(AcidTrap(player.rect.centerx, player.rect.centery,
                                        trap_damage=trap_damage, radius_mult=radius_mult))
        else:
            self.timer = min(self.timer, interval * 0.5)

        self.group.update(dt)