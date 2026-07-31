import random
import pygame
from settings import WHITE


class DamageNumber:
    """伤害飘字：出现时放大回弹（pop），暴击金色加大更醒目。"""

    def __init__(self, x, y, amount, font, crit=False):
        color = (255, 205, 60) if crit else WHITE
        outline_color = (60, 30, 5) if crit else (25, 10, 10)
        text = str(amount)
        raw = font.render(text, True, color)
        outline = font.render(text, True, outline_color)
        self.text = pygame.Surface((raw.get_width() + 4, raw.get_height() + 4), pygame.SRCALPHA)
        for ox, oy in ((0, 2), (2, 0), (2, 4), (4, 2), (0, 0), (4, 4), (0, 4), (4, 0)):
            self.text.blit(outline, (ox, oy))
        self.text.blit(raw, (2, 2))
        self.crit = crit
        self.x = x + random.uniform(-6, 6)
        self.y = y
        self.age = 0.0
        self.lifetime = 1.0 if crit else 0.8
        self.vy = -70 if crit else -50
        self.vx = random.uniform(-16, 16)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 60 * dt  # 轻微减速上浮，更有重量感
        self.lifetime -= dt

    @property
    def alive(self):
        return self.lifetime > 0

    def draw(self, screen, camera):
        alpha = int(255 * max(0, min(1, self.lifetime / 0.3)))
        # 入场弹跳：前 0.15s 从大到小回弹
        pop = 0.15
        base_scale = 1.35 if self.crit else 1.0
        if self.age < pop:
            t = self.age / pop
            scale = base_scale * (1.8 - 0.8 * t)
        else:
            scale = base_scale
        surf = self.text
        if scale != 1.0:
            w = max(1, int(surf.get_width() * scale))
            h = max(1, int(surf.get_height() * scale))
            surf = pygame.transform.scale(surf, (w, h))
        else:
            surf = surf.copy()
        surf.set_alpha(alpha)
        pos = camera.apply(pygame.Rect(self.x, self.y, 0, 0))
        screen.blit(surf, (pos.x - surf.get_width() // 2, pos.y - surf.get_height() // 2))
