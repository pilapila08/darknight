import math
import pygame
from settings import ENEMY_SIZE, ENEMY_SPEED, ENEMY_HP, RED, WHITE
from entities.animation import Animation
from effects.asset_loader import load_image


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, hp=None, speed=None, size=None, color=None,
                 is_elite=False, sprite_name="enemy", contact_damage=None):
        super().__init__()
        self.hp = hp if hp is not None else ENEMY_HP
        self.max_hp = self.hp
        self.speed = speed if speed is not None else ENEMY_SPEED
        self.is_elite = is_elite
        self.contact_damage = contact_damage if contact_damage is not None else 1
        size = size if size is not None else ENEMY_SIZE
        color = color if color is not None else RED

        self._base_color = color
        self._size = size
        self.flash_timer = 0.0

        # DoT debuff
        self.dot_timer = 0.0
        self.dot_tick_timer = 0.0
        self.dot_damage = 0

        # Frostbite
        self.frostbitten = False

        # Base speed (for slow calculation)
        self._base_speed = self.speed

        # Animation
        frames = load_image(sprite_name, color, size, animated=True)
        self._normal_frames = [frame.copy() for frame in frames]
        self._flash_frames = [self._make_flash_frame(frame) for frame in frames]
        self._anim = Animation(frames, frame_duration=0.15)
        self._frames = frames

        self.image = self._anim.get_image()
        self.rect = self.image.get_rect(topleft=(x, y))

    def _make_flash_frame(self, frame):
        flash = frame.copy()
        mask = pygame.mask.from_surface(frame)
        silhouette = mask.to_surface(
            setcolor=(255, 255, 255, 170),
            unsetcolor=(0, 0, 0, 0)
        ).convert_alpha()
        flash.blit(silhouette, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return flash

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp > 0:
            self.flash_timer = 0.1
        return self.hp <= 0

    def apply_dot(self, duration, tick_interval, damage_per_tick):
        self.dot_timer = duration
        self.dot_tick_timer = 0.0
        self.dot_damage = damage_per_tick

    def apply_frostbite(self, slow_factor):
        if not self.frostbitten:
            self.frostbitten = True
            self.speed *= slow_factor

    def _update_flash(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt

    def _update_dot(self, dt):
        if self.dot_timer > 0:
            self.dot_timer -= dt
            self.dot_tick_timer -= dt
            if self.dot_tick_timer <= 0:
                self.dot_tick_timer = 1.0
                if self.take_damage(self.dot_damage):
                    return True
            if self.dot_timer <= 0:
                self.dot_damage = 0
        return False

    def _move_toward(self, tx, ty, dt):
        dx = tx - self.rect.centerx
        dy = ty - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += (dx / dist) * self.speed * dt
            self.rect.y += (dy / dist) * self.speed * dt

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)
        self._anim.update(dt)
        if self.flash_timer > 0:
            self.image = self._flash_frames[self._anim.current]
        else:
            self.image = self._normal_frames[self._anim.current]
        self._move_toward(player_rect.centerx, player_rect.centery, dt)
