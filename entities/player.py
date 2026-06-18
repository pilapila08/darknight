import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, PLAYER_SIZE, PLAYER_SPEED, PLAYER_MAX_HP, WHITE
from entities.animation import Animation
from effects.asset_loader import load_image
from ui.render_helpers import draw_ground_shadow


class Player:
    def __init__(self):
        frames = load_image("player", WHITE, PLAYER_SIZE, animated=True)
        self.anim = Animation(frames, frame_duration=0.1)
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.speed = PLAYER_SPEED
        self.max_hp = PLAYER_MAX_HP  # 血量上限
        self._was_moving = False

    def update(self, dt, keys):
        dx = 0
        dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        is_moving = dx != 0 or dy != 0
        if is_moving:
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
            self.rect.x += dx * self.speed * dt
            self.rect.y += dy * self.speed * dt
            self.anim.update(dt)
        else:
            self.anim.reset()

        self.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))
        self._was_moving = is_moving

    def draw(self, screen, camera):
        screen_rect = camera.apply(self.rect)
        draw_ground_shadow(screen, camera, self.rect, scale=1.2, alpha=115)
        glow = pygame.Surface((self.rect.width + 20, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 190, 255, 70), glow.get_rect())
        screen.blit(glow, (screen_rect.centerx - glow.get_width() // 2,
                           screen_rect.bottom - glow.get_height() // 2))
        screen.blit(self.anim.get_image(), screen_rect)
