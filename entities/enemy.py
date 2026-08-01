import math
import pygame
from settings import (
    ENEMY_SIZE, ENEMY_SPEED, ENEMY_HP, RED, WHITE, WALK_ANIM_PER_TYPE,
    ENEMY_GLOW_COLOR, ENEMY_GLOW_WIDTH, ENEMY_GLOW_ALPHA,
    ENEMY_RING_COLOR, ENEMY_RING_ALPHA,
    EXPLODER_RADIUS, EXPLODER_RING_COLOR, EXPLODER_RING_ALPHA,
)
from entities.animation import Animation
from entities.walk_anim import compute_walk_frame, resolve_params, flip_for_direction
from effects.asset_loader import load_image
from ui.render_helpers import draw_ground_shadow


# ---- 可见性层缓存（DN-ENG-VIS-01）----
# 轮廓光 / 光圈按 (类型, 尺寸, 帧) / (半径, 颜色, alpha) 缓存，避免每帧 mask 膨胀与建面。
_GLOW_CACHE = {}
_RING_CACHE = {}


def _build_glow_surface(frame, color, width, alpha):
    """基于 sprite 蒙版生成外发光描边：mask 剪影向 width 半径内偏移铺底，暖色半透明。"""
    mask = pygame.mask.from_surface(frame)
    sil = mask.to_surface(setcolor=(*color, alpha),
                          unsetcolor=(0, 0, 0, 0)).convert_alpha()
    pad = width + 1
    w, h = frame.get_size()
    glow = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                glow.blit(sil, (pad + dx, pad + dy))
    return glow


def _build_ring_surface(radius, color, alpha):
    """脚底危险光圈：半透明填充圆 + 稍亮细描边。"""
    size = radius * 2 + 10
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(surf, (*color, alpha), (c, c), radius)
    pygame.draw.circle(surf, (*color, min(255, alpha + 30)), (c, c), radius, 2)
    return surf


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
        self._sprite_name = sprite_name  # 用于 L1 程序动画按类型取参
        self.flash_timer = 0.0

        # L1 程序动画：水平速度（px/s，负=朝左），由 _move_toward 维护
        self.vx = 0.0

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

        # 轮廓光（按类型/尺寸/帧缓存，150 敌人共享同一套 surface）
        self._glow_frames = []
        for i, frame in enumerate(self._normal_frames):
            key = (sprite_name, size, i)
            glow = _GLOW_CACHE.get(key)
            if glow is None:
                glow = _build_glow_surface(frame, ENEMY_GLOW_COLOR,
                                           ENEMY_GLOW_WIDTH, ENEMY_GLOW_ALPHA)
                if len(_GLOW_CACHE) > 512:
                    _GLOW_CACHE.clear()
                _GLOW_CACHE[key] = glow
            self._glow_frames.append(glow)

        self.image = self._anim.get_image()
        self.rect = self.image.get_rect(topleft=(x, y))

    def _make_flash_frame(self, frame):
        # 土豆兄弟式受击反馈：整体变为纯白剪影，识别度最高
        mask = pygame.mask.from_surface(frame)
        return mask.to_surface(
            setcolor=(255, 255, 255, 255),
            unsetcolor=(0, 0, 0, 0)
        ).convert_alpha()

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
            self.vx = (dx / dist) * self.speed

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)
        self._anim.update(dt)
        if self.flash_timer > 0:
            self.image = self._flash_frames[self._anim.current]
        else:
            self.image = self._normal_frames[self._anim.current]
        self._move_toward(player_rect.centerx, player_rect.centery, dt)

    def _get_ring(self, radius, color, alpha):
        """按 (半径, 颜色, alpha) 缓存光圈 surface。"""
        key = (radius, color, alpha)
        surf = _RING_CACHE.get(key)
        if surf is None:
            surf = _build_ring_surface(radius, color, alpha)
            if len(_RING_CACHE) > 256:
                _RING_CACHE.clear()
            _RING_CACHE[key] = surf
        return surf

    def _draw_exploder_ring(self, screen, ground_x, ground_y):
        """自爆怪：爆炸范围（EXPLODER_RADIUS）红色脉冲光圈。"""
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.5 + 0.5 * math.sin(t * 8.0)
        alpha = int(EXPLODER_RING_ALPHA * (0.7 + 0.3 * pulse))
        ring = self._get_ring(EXPLODER_RADIUS, EXPLODER_RING_COLOR, alpha)
        screen.blit(ring, (ground_x - ring.get_width() // 2,
                           ground_y - ring.get_height() // 2))
        # 亮描边随脉冲缩放（直接画屏，代价低）
        r = int(EXPLODER_RADIUS * (0.9 + 0.2 * pulse))
        pygame.draw.circle(screen, EXPLODER_RING_COLOR, (ground_x, ground_y), r, 2)

    def _draw_visibility_layers(self, screen, base, frame, ring_scale=1.0, ring_alpha=None):
        """脚底危险光圈 + 轮廓光（绘制在 sprite 下层）。

        - 光圈贴地（rect.bottom，不随 bob 浮动），半径略大于 sprite。
        - 轮廓光中心对齐 sprite 中心（含 bob），随 flip 镜像。
        """
        ground_x, ground_y = base.centerx, base.bottom
        # 脚底危险光圈
        radius = max(8, int(self.rect.width * 0.62 * ring_scale))
        alpha = ENEMY_RING_ALPHA if ring_alpha is None else ring_alpha
        ring = self._get_ring(radius, ENEMY_RING_COLOR, alpha)
        screen.blit(ring, (ground_x - ring.get_width() // 2,
                           ground_y - ring.get_height() // 2))
        # 自爆怪特殊：爆炸范围红色脉冲光圈
        if self._sprite_name == "exploder":
            self._draw_exploder_ring(screen, ground_x, ground_y)
        # 轮廓光（中心对齐 sprite 中心，含 bob；随 flip 镜像）
        img_rect = frame.surface.get_rect(midbottom=(ground_x, ground_y + frame.bob))
        glow = self._glow_frames[self._anim.current]
        glow = flip_for_direction(glow, self.vx)
        glow_rect = glow.get_rect(center=img_rect.center)
        screen.blit(glow, glow_rect)

    def _draw_animated(self, screen, camera, anim_type, shadow_scale=1.0,
                       shadow_alpha=90, ring_scale=1.0, ring_alpha=None):
        """L1 程序动画 + 可见性层：阴影(底) → 光圈/轮廓光 → 精灵(顶)。"""
        t = pygame.time.get_ticks() / 1000.0
        params = resolve_params(anim_type)
        frame = compute_walk_frame(self.image, t, id(self), self.vx, params)
        base = camera.apply(self.rect)
        # 1) 脚底阴影（最底层，贴地）
        draw_ground_shadow(screen, camera, self.rect,
                           shadow_scale * frame.shadow_scale, shadow_alpha)
        # 2) 危险光圈 + 轮廓光（sprite 下层）
        self._draw_visibility_layers(screen, base, frame, ring_scale, ring_alpha)
        # 3) 精灵（含 bob，受击闪白即 self.image=flash frame，天然在最上层）
        img_rect = frame.surface.get_rect(midbottom=(base.centerx, base.bottom + frame.bob))
        screen.blit(frame.surface, img_rect)

    def draw(self, screen, camera):
        """绘制：L1 程序动画（bob/squash/flip）+ 脚底阴影 + 危险光圈 + 轮廓光。"""
        anim_type = self._sprite_name if self._sprite_name in WALK_ANIM_PER_TYPE \
            else ("elite" if self.is_elite else "enemy")
        self._draw_animated(screen, camera, anim_type)
