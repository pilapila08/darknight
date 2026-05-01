import pygame
from settings import WHITE


class DamageNumber:
    def __init__(self, x, y, amount, font):
        self.text = font.render(str(amount), True, WHITE)
        self.x = x
        self.y = y
        self.lifetime = 0.8
        self.vy = -50

    def update(self, dt):
        self.y += self.vy * dt
        self.lifetime -= dt

    @property
    def alive(self):
        return self.lifetime > 0

    def draw(self, screen, camera):
        alpha = int(255 * max(0, min(1, self.lifetime / 0.3)))
        surf = self.text.copy()
        surf.set_alpha(alpha)
        pos = camera.apply(pygame.Rect(self.x, self.y, 0, 0))
        screen.blit(surf, (pos.x - surf.get_width() // 2, pos.y))
