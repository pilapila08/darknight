import math
import pygame
from settings import ENEMY_BULLET_RADIUS, ENEMY_BULLET_SPEED, ORANGE


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, damage=1):
        super().__init__()
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * ENEMY_BULLET_SPEED
            self.vy = (dy / dist) * ENEMY_BULLET_SPEED
            dir_x = dx / dist
            dir_y = dy / dist
        else:
            self.vx = 0
            self.vy = 0
            dir_x = 1
            dir_y = 0
        size = ENEMY_BULLET_RADIUS * 4 + 8
        center = size // 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        tail = (center - int(dir_x * ENEMY_BULLET_RADIUS * 2.2),
                center - int(dir_y * ENEMY_BULLET_RADIUS * 2.2))
        pygame.draw.line(self.image, (*ORANGE, 90), tail, (center, center), ENEMY_BULLET_RADIUS * 2)
        pygame.draw.circle(self.image, (*ORANGE, 70), (center, center), ENEMY_BULLET_RADIUS * 2)
        pygame.draw.circle(self.image, ORANGE, (center, center), ENEMY_BULLET_RADIUS)
        pygame.draw.circle(self.image, (255, 230, 150), (center - 1, center - 1),
                           max(1, ENEMY_BULLET_RADIUS // 2))
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = damage  # 使用传入的伤害值，不再硬编码为1

    def update(self, dt):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
