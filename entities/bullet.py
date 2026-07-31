import math
import pygame
from settings import BULLET_RADIUS, BULLET_SPEED, BLUE


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_pos, speed_mult=1.0, pierce=0, damage_mult=1.0):
        super().__init__()
        dx = target_pos[0] - x
        dy = target_pos[1] - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            speed = BULLET_SPEED * speed_mult
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed
            dir_x = dx / dist
            dir_y = dy / dist
        else:
            self.vx = 0
            self.vy = 0
            dir_x = 1
            dir_y = 0

        # R3 技能平衡：穿透剩余次数 + 每发伤害倍率（弹量边际惩罚 / 穿透弹 ×0.85）
        self.pierce = pierce
        self.damage_mult = damage_mult
        self._hit_ids = set()  # 已命中敌人 id（穿透多段不重复命中同一目标）

        size = BULLET_RADIUS * 4 + 10
        center = size // 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        tail = (center - int(dir_x * BULLET_RADIUS * 2.2),
                center - int(dir_y * BULLET_RADIUS * 2.2))
        head = (center + int(dir_x * BULLET_RADIUS * 0.8),
                center + int(dir_y * BULLET_RADIUS * 0.8))
        pygame.draw.line(self.image, (*BLUE, 95), tail, head, BULLET_RADIUS * 2)
        pygame.draw.circle(self.image, (*BLUE, 70), (center, center), BULLET_RADIUS * 2)
        pygame.draw.circle(self.image, BLUE, (center, center), BULLET_RADIUS)
        pygame.draw.circle(self.image, (180, 230, 255), (center - 1, center - 1), max(2, BULLET_RADIUS // 2))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
