import math
import random
import pygame


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(2, 4)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 180)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.3, 0.6)

    def update(self, dt):
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
        self.lifetime -= dt
        alpha = int(255 * max(0, self.lifetime / 0.5))
        self.image.set_alpha(alpha)
        if self.lifetime <= 0:
            self.kill()
