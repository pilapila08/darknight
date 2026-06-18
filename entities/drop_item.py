import math
import pygame

from effects.asset_loader import load_image
from settings import GOLD, GREEN, CYAN


class DropItem(pygame.sprite.Sprite):
    def __init__(self, x, y, kind, amount, image_name, color):
        super().__init__()
        self.kind = kind
        self.amount = amount
        self.image = load_image(image_name, color, 24, animated=False)[0]
        self.base_image = self.image
        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_x = x
        self.spawn_y = y
        self.age = 0.0
        self.lifetime = 16.0
        self.pickup_range = 58

    def update(self, dt, player_rect):
        self.age += dt
        bob = math.sin(self.age * 5.5) * 3
        self.rect.center = (self.spawn_x, self.spawn_y + int(bob))
        if self.age > self.lifetime:
            self.kill()
            return
        dist = math.hypot(player_rect.centerx - self.rect.centerx,
                          player_rect.centery - self.rect.centery)
        if dist < self.pickup_range and dist > 0:
            self.spawn_x += (player_rect.centerx - self.rect.centerx) / dist * 260 * dt
            self.spawn_y += (player_rect.centery - self.rect.centery) / dist * 260 * dt
        if self.age > self.lifetime - 4:
            self.image = self.base_image.copy()
            alpha = 90 + int(165 * (0.5 + 0.5 * math.sin(self.age * 14)))
            self.image.set_alpha(alpha)


class HealthPack(DropItem):
    def __init__(self, x, y, amount=4):
        super().__init__(x, y, "health", amount, "health_pack", GREEN)


class ShieldPickup(DropItem):
    def __init__(self, x, y, amount=5):
        super().__init__(x, y, "shield", amount, "shield_pickup", CYAN)
