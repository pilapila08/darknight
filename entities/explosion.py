import pygame
from settings import EXPLODER_RADIUS, EXPLODER_DAMAGE, PURPLE
from effects.fx_textures import get_explosion_fire


class Explosion:
    def __init__(self, x, y, damage=None):
        self.x = x
        self.y = y
        self.radius = 0.0
        self.max_radius = EXPLODER_RADIUS
        self.lifetime = 0.3
        self.elapsed = 0.0
        self.damage = damage if damage is not None else EXPLODER_DAMAGE
        self._applied = False

    def apply_damage(self, player, enemies):
        """Call once to deal damage to everything in range."""
        if self._applied:
            return
        self._applied = True

        # Damage enemies
        for enemy in list(enemies):
            dx = enemy.rect.centerx - self.x
            dy = enemy.rect.centery - self.y
            if (dx * dx + dy * dy) <= self.max_radius * self.max_radius:
                if enemy.take_damage(self.damage):
                    enemy.kill()

        # Damage player
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        if (dx * dx + dy * dy) <= self.max_radius * self.max_radius:
            return True  # player was in range
        return False

    def update(self, dt):
        self.elapsed += dt
        self.radius = self.max_radius * min(1.0, self.elapsed / self.lifetime)

    @property
    def alive(self):
        return self.elapsed < self.lifetime

    def draw(self, screen, camera):
        alpha = int(180 * max(0, 1 - self.elapsed / self.lifetime))
        radius = max(1, int(self.radius))
        pos = camera.apply(pygame.Rect(self.x, self.y, 0, 0))

        # C02 FX（fx-spec-v1.md §2）：优先 blit 贴图（保留半径+alpha 缩放逻辑）
        fx = get_explosion_fire()
        if fx is not None:
            size = max(4, radius * 2)
            surf = pygame.transform.scale(fx, (size, size))
            surf.set_alpha(alpha)
            screen.blit(surf, (pos.x - radius, pos.y - radius))
            return

        # 回退：程序化三层圆（原实现）
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*PURPLE, alpha),
                          (radius, radius), radius)
        pygame.draw.circle(surf, (255, 190, 255, min(255, alpha + 40)),
                          (radius, radius), max(1, radius // 2), 2)
        pygame.draw.circle(surf, (*PURPLE, min(255, alpha + 60)),
                          (radius, radius), radius, 2)
        screen.blit(surf, (pos.x - radius, pos.y - radius))
