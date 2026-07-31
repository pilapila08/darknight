"""[废弃] XpOrb 经验球模块。

v3.0 起经验改为击杀直给，本模块不再被任何代码引用（entities/__init__.py 已移除导出）。
仅保留文件以便日后如需恢复拾取机制可参考；待 ORB_RADIUS/ORB_SPEED 等常量一并清理后删除。
"""
import math
import pygame
from settings import ORB_RADIUS, ORB_SPEED, PICKUP_RANGE, YELLOW
from effects.asset_loader import load_image


class XpOrb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        frames = load_image("xp_orb", YELLOW, ORB_RADIUS * 2, animated=False)
        self.image = frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt, player_rect, pickup_range=None):
        if pickup_range is None:
            pickup_range = PICKUP_RANGE
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist < pickup_range and dist > 0:
            self.rect.x += (dx / dist) * ORB_SPEED * dt
            self.rect.y += (dy / dist) * ORB_SPEED * dt
