import math
import pygame
from settings import ENEMY_BULLET_RADIUS, ENEMY_BULLET_SPEED, ORANGE


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        size = ENEMY_BULLET_RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ORANGE,
                          (ENEMY_BULLET_RADIUS, ENEMY_BULLET_RADIUS),
                          ENEMY_BULLET_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))

        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * ENEMY_BULLET_SPEED
            self.vy = (dy / dist) * ENEMY_BULLET_SPEED
        else:
            self.vx = 0
            self.vy = 0
        self.damage = 1

    def update(self, dt):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
