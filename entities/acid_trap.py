import pygame
from settings import (TRAP_DURATION, TRAP_RADIUS, TRAP_DOT_DURATION,
                      TRAP_DOT_DAMAGE, TRAP_DOT_TICK, TRAP_COLOR, TRAP_INTERVAL)


class AcidTrap(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = TRAP_RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*TRAP_COLOR, 120),
                          (TRAP_RADIUS, TRAP_RADIUS), TRAP_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = TRAP_DURATION
        self._hit_ids = set()  # enemies already affected by this trap

    def update(self, dt):
        self.lifetime -= dt
        alpha = int(120 * max(0, min(1, self.lifetime / 2.0)))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (*TRAP_COLOR, alpha),
                          (TRAP_RADIUS, TRAP_RADIUS), TRAP_RADIUS)
        if self.lifetime <= 0:
            self.kill()

    def check_enemies(self, enemies):
        """Apply DoT to enemies touching this trap. Returns newly affected enemies."""
        results = []
        for enemy in enemies:
            if id(enemy) in self._hit_ids:
                continue
            if self.rect.colliderect(enemy.rect):
                self._hit_ids.add(id(enemy))
                enemy.apply_dot(TRAP_DOT_DURATION, TRAP_DOT_TICK, TRAP_DOT_DAMAGE)
                results.append(enemy)
        return results


class TrapManager:
    def __init__(self):
        self.timer = 0.0
        self.group = pygame.sprite.Group()

    def update(self, dt, player, is_moving, interval=None):
        if interval is None:
            interval = TRAP_INTERVAL
        if is_moving:
            self.timer += dt
            while self.timer >= interval:
                self.timer -= interval
                self.group.add(AcidTrap(player.rect.centerx, player.rect.centery))
        else:
            self.timer = min(self.timer, TRAP_INTERVAL * 0.5)

        self.group.update(dt)
