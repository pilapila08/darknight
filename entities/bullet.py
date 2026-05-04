import math
import pygame
from settings import BULLET_RADIUS, BULLET_SPEED, BLUE


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_pos, speed_mult=1.0):
        super().__init__()
        size = BULLET_RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (BULLET_RADIUS, BULLET_RADIUS), BULLET_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))
        dx = target_pos[0] - x
        dy = target_pos[1] - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            speed = BULLET_SPEED * speed_mult
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed

    def update(self, dt):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
