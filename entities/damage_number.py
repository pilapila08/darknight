import pygame
from settings import WHITE


class DamageNumber:
    def __init__(self, x, y, amount, font):
        raw = font.render(str(amount), True, WHITE)
        self.text = pygame.Surface((raw.get_width() + 4, raw.get_height() + 4), pygame.SRCALPHA)
        outline = font.render(str(amount), True, (25, 10, 10))
        for ox, oy in ((0, 2), (2, 0), (2, 4), (4, 2)):
            self.text.blit(outline, (ox, oy))
        self.text.blit(raw, (2, 2))
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
