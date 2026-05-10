import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT


class Camera:
    def __init__(self):
        self.offset = pygame.Vector2(0, 0)
        self._shake_duration = 0.0
        self._shake_intensity = 0.0

    def shake(self, duration, intensity):
        self._shake_duration = duration
        self._shake_intensity = intensity

    def update(self, target_rect, dt):
        self.offset.x = target_rect.centerx - SCREEN_WIDTH // 2
        self.offset.y = target_rect.centery - SCREEN_HEIGHT // 2

        if self._shake_duration > 0:
            self._shake_duration -= dt
            sx = random.uniform(-self._shake_intensity, self._shake_intensity)
            sy = random.uniform(-self._shake_intensity, self._shake_intensity)
            self.offset.x += sx
            self.offset.y += sy

        self.offset.x = max(0, min(self.offset.x, MAP_WIDTH - SCREEN_WIDTH))
        self.offset.y = max(0, min(self.offset.y, MAP_HEIGHT - SCREEN_HEIGHT))

    def apply(self, rect):
        return rect.move(-self.offset.x, -self.offset.y)
