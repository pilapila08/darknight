import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, PLAYER_SIZE, PLAYER_SPEED, PLAYER_MAX_HP, WHITE
from entities.animation import Animation
from entities.walk_anim import compute_walk_frame, resolve_params
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
        self._tilt = 0.0  # 移动时的身体倾斜角（土豆兄弟式动态）
        self.vx = 0.0     # 水平速度（px/s，L1 程序动画 flip 用）
        self.vy = 0.0     # 垂直速度（px/s）
        self._facing = 1  # 朝向：1=右，-1=左（静止时保持上次朝向）

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
            self.vx = dx * self.speed
            self.vy = dy * self.speed
            if dx < 0:
                self._facing = -1
            elif dx > 0:
                self._facing = 1
        else:
            self.anim.reset()
            self.vx = 0.0
            self.vy = 0.0

        # 向移动方向倾斜，停下时回正
        target_tilt = -dx * 8.0
        self._tilt += (target_tilt - self._tilt) * min(1.0, 12.0 * dt)

        self.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))
        self._was_moving = is_moving

    def draw(self, screen, camera):
        screen_rect = camera.apply(self.rect)
        image = self.anim.get_image()
        bob = 0.0
        shadow_scale = 1.2
        if self._was_moving:
            # L1 程序动画：bob/squash/flip + 阴影联动（仅移动时激活）
            params = resolve_params("player")
            frame = compute_walk_frame(image, pygame.time.get_ticks() / 1000.0,
                                       id(self), self.vx, params)
            image = frame.surface
            bob = frame.bob
            shadow_scale = 1.2 * frame.shadow_scale
        elif self._facing < 0:
            # 静止时保持上次朝向（不 bob/squash）
            image = pygame.transform.flip(image, True, False)
        draw_ground_shadow(screen, camera, self.rect, scale=shadow_scale, alpha=115)
        glow = pygame.Surface((self.rect.width + 20, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 190, 255, 70), glow.get_rect())
        screen.blit(glow, (screen_rect.centerx - glow.get_width() // 2,
                           screen_rect.bottom - glow.get_height() // 2))
        if abs(self._tilt) > 0.5:
            image = pygame.transform.rotate(image, self._tilt)
        # 以脚底中心对齐，旋转/挤压时不会浮离地面
        rect = image.get_rect(midbottom=(screen_rect.centerx, screen_rect.bottom + bob))
        screen.blit(image, rect)
