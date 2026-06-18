import math
import random
import pygame


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.base_size = random.randint(4, 8)
        self.image = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*color, 75),
                           (self.base_size // 2, self.base_size // 2), self.base_size // 2)
        pygame.draw.circle(self.image, color,
                           (self.base_size // 2, self.base_size // 2), max(1, self.base_size // 3))
        self._base_image = self.image.copy()
        self.rect = self.image.get_rect(center=(x, y))

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(90, 230)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.max_lifetime = random.uniform(0.35, 0.75)
        self.lifetime = self.max_lifetime

    def update(self, dt):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
        self.vx *= max(0.0, 1 - 2.2 * dt)
        self.vy *= max(0.0, 1 - 2.2 * dt)
        self.lifetime -= dt
        life_ratio = max(0, self.lifetime / self.max_lifetime)
        alpha = int(255 * life_ratio)
        size = max(1, int(self.base_size * (0.45 + life_ratio * 0.55)))
        center = self.rect.center
        self.image = pygame.transform.smoothscale(self._base_image, (size, size))
        self.image.set_alpha(alpha)
        self.rect = self.image.get_rect(center=center)
        if self.lifetime <= 0:
            self.kill()
