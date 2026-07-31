"""
AssetLoader — detailed pixel-art sprite generation.
All characters drawn with pygame primitives at native resolution.
"""
import os
import random
import math
import sys
import pygame
from array import array


def _resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


ASSETS = _resource_path("assets")
SPRITES = os.path.join(ASSETS, "sprites")
SOUNDS = os.path.join(ASSETS, "sounds")
SAMPLE_RATE = 22050


# ============================================================
#  Pixel-art sprite generators (drawn at native resolution)
# ============================================================

def _px(surf, x, y, color):
    """Draw a single pixel at (x, y)."""
    if 0 <= x < surf.get_width() and 0 <= y < surf.get_height():
        surf.set_at((x, y), color)


def _px_rect(surf, x, y, w, h, color):
    """Draw a filled pixel rectangle."""
    pygame.draw.rect(surf, color, (x, y, w, h))


def _px_hline(surf, x, y, length, color):
    pygame.draw.line(surf, color, (x, y), (x + length - 1, y))


def _px_vline(surf, x, y, length, color):
    pygame.draw.line(surf, color, (x, y), (x, y + length - 1))


# ---- Player: White mage (32x32) ----

def _gen_player_frames(size, base_color):
    frames = []
    s = size  # shorthand
    mid = s // 2
    robe_color = (220, 220, 240)
    skin_color = (255, 220, 180)
    hat_color = (180, 180, 220)
    eye_color = (40, 40, 80)

    for bounce in (0, -1, 0):
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        y_off = bounce

        # Robe / body
        body_top = s // 3 + y_off
        body_bot = s - 2 + y_off
        body_left = s // 4
        body_right = s - s // 4
        # Trapezoid robe: wider at bottom
        for row in range(body_top, body_bot):
            t = (row - body_top) / max(1, body_bot - body_top)
            l = int(body_left - t * 2)
            r = int(body_right + t * 2)
            _px_hline(surf, max(0, l), row, min(s, r - l), robe_color)

        # Belt
        belt_y = body_top + (body_bot - body_top) // 2
        _px_hline(surf, body_left - 1, belt_y, body_right - body_left + 3, (120, 100, 60))
        # Belt buckle
        _px_rect(surf, mid - 2, belt_y - 1, 4, 3, GOLD)

        # Head
        head_r = s // 6
        pygame.draw.circle(surf, skin_color, (mid, body_top - head_r // 2 + 1), head_r)

        # Eyes
        _px(surf, mid - 2, body_top - 2, eye_color)
        _px(surf, mid + 1, body_top - 2, eye_color)

        # Hat (pointed wizard hat)
        hat_base = body_top - head_r
        hat_tip = max(0, hat_base - s // 4)
        hat_width = head_r
        for row in range(hat_tip, hat_base):
            t = (row - hat_tip) / max(1, hat_base - hat_tip)
            w = int(t * hat_width)
            if w > 0:
                _px_hline(surf, mid - w // 2, row, w, hat_color)
        # Hat brim
        _px_hline(surf, mid - hat_width // 2 - 1, hat_base, hat_width + 2, hat_color)

        # Staff (on the side)
        staff_x = body_right - 2
        staff_top = body_top - 3
        staff_bot = s - 1
        _px_vline(surf, staff_x, staff_top, staff_bot - staff_top, (140, 100, 60))
        # Staff orb
        pygame.draw.circle(surf, CYAN, (staff_x, staff_top), 3)

        frames.append(surf)
    return frames


# ---- Basic Enemy: Red imp (28x28) ----

def _gen_enemy_frames(size, color):
    frames = []
    s = size
    mid = s // 2
    dark = tuple(max(0, c - 60) for c in color)
    light = tuple(min(255, c + 40) for c in color)
    eye_c = (255, 255, 200)

    for i in range(3):
        wobble = int(math.sin(i * 2.1) * 2)
        surf = pygame.Surface((s, s), pygame.SRCALPHA)

        # Body: rounded rect
        body_margin = s // 8
        body_rect = (body_margin, body_margin + wobble,
                     s - body_margin * 2, s - body_margin * 2 - abs(wobble))
        pygame.draw.rect(surf, color, body_rect, border_radius=s // 8)

        # Darker belly
        belly_m = s // 4
        belly_rect = (belly_m, belly_m + 2 + wobble,
                      s - belly_m * 2, s - belly_m * 2 - 2)
        pygame.draw.rect(surf, dark, belly_rect, border_radius=s // 8)

        # Eyes
        eye_y = s // 3 + wobble
        eye_spacing = s // 6
        for ex in (mid - eye_spacing, mid + eye_spacing):
            pygame.draw.circle(surf, eye_c, (ex, eye_y), max(2, s // 12))
            pygame.draw.circle(surf, (0, 0, 0), (ex + 1, eye_y), max(1, s // 20))

        # Mouth
        mouth_y = s // 2 + wobble
        _px_hline(surf, mid - 3, mouth_y, 6, (0, 0, 0))
        _px(surf, mid - 3, mouth_y - 1, (0, 0, 0))
        _px(surf, mid + 2, mouth_y - 1, (0, 0, 0))

        # Small horns
        horn_h = s // 7
        for hx in (body_margin + 2, s - body_margin - 3):
            _px_vline(surf, hx, body_margin - horn_h + wobble, horn_h, light)
        _px(surf, body_margin + 1, body_margin - horn_h + wobble, light)
        _px(surf, s - body_margin - 2, body_margin - horn_h + wobble, light)

        frames.append(surf)
    return frames


# ---- Elite Enemy: Blue champion (40x40, larger) ----

def _gen_elite_frames(size, color):
    frames = []
    s = size
    mid = s // 2
    dark = tuple(max(0, c - 50) for c in color)
    light = tuple(min(255, c + 50) for c in color)
    gold_c = GOLD

    for i in range(3):
        wobble = int(math.sin(i * 2.1) * 2)
        surf = pygame.Surface((s, s), pygame.SRCALPHA)

        # Larger body
        m = s // 10
        body_rect = (m, m + wobble, s - m * 2, s - m * 2 - abs(wobble))
        pygame.draw.rect(surf, color, body_rect, border_radius=s // 6)

        # Darker inner
        inner_m = s // 5
        inner_rect = (inner_m, inner_m + wobble + 2,
                      s - inner_m * 2, s - inner_m * 2 - 2)
        pygame.draw.rect(surf, dark, inner_rect, border_radius=s // 6)

        # Crown / crest on top
        crown_y = m - s // 6 + wobble
        crown_w = s // 3
        for spike in range(3):
            cx = mid + (spike - 1) * (crown_w // 2)
            cy = crown_y - (s // 9 if spike == 1 else s // 14)
            _px_vline(surf, cx, cy, crown_y - cy, gold_c)
        _px_hline(surf, mid - crown_w // 2, crown_y, crown_w, gold_c)

        # Glowing eyes
        eye_y = s // 3 + wobble
        for ex in (mid - 4, mid + 4):
            pygame.draw.circle(surf, (255, 255, 100), (ex, eye_y), 3)
            pygame.draw.circle(surf, (0, 0, 0), (ex + 1, eye_y), 1)

        # Scary mouth
        mouth_y = s // 2 + wobble + 2
        _px_hline(surf, mid - 4, mouth_y, 8, (0, 0, 0))
        for tx in range(mid - 4, mid + 4, 2):
            _px(surf, tx, mouth_y + 1, (200, 0, 0))

        frames.append(surf)
    return frames


# ---- Specialist enemy frames ----

def _gen_charger_frames(size, color):
    frames = []
    s = size
    mid = s // 2
    dark = tuple(max(0, c - 70) for c in color)
    for i in range(3):
        wobble = int(math.sin(i * 2.1) * 1)
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        # Arrow-shaped body (wider at top)
        m = s // 8
        bot_m = s // 4
        for row in range(m, s - bot_m):
            t = (row - m) / max(1, s - bot_m - m)
            w = s // 3 + int(t * s // 4)
            l = mid - w // 2
            _px_hline(surf, l, row + wobble, w, color)
        # Head/crest
        _px_rect(surf, mid - 4, m - 3 + wobble, 8, 6, dark)
        # Eyes
        pygame.draw.circle(surf, (255, 255, 200), (mid - 2, m + wobble + 1), 2)
        pygame.draw.circle(surf, (255, 255, 200), (mid + 2, m + wobble + 1), 2)
        _px(surf, mid - 2, m + wobble + 1, (0, 0, 0))
        _px(surf, mid + 2, m + wobble + 1, (0, 0, 0))
        frames.append(surf)
    return frames


def _gen_ranger_frames(size, color):
    frames = []
    s = size
    mid = s // 2
    dark = tuple(max(0, c - 60) for c in color)
    for i in range(3):
        wobble = int(math.sin(i * 2.1) * 1)
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        # Slim body
        m = s // 5
        _px_rect(surf, m, m + wobble, s - m * 2, s - m * 2, color)
        # Darker hood
        _px_rect(surf, m + 1, m + wobble, s - m * 2 - 2, s // 3, dark)
        # Eyes (glowing)
        eye_y = m + wobble + s // 6
        pygame.draw.circle(surf, (255, 255, 100), (mid - 2, eye_y), 2)
        pygame.draw.circle(surf, (255, 255, 100), (mid + 2, eye_y), 2)
        # "Gun barrel" on right side
        gun_x = s - m
        gun_y = mid + wobble
        pygame.draw.circle(surf, (255, 100, 50), (gun_x + 2, gun_y), 3)
        _px_hline(surf, s - m - 1, gun_y, 4, (180, 180, 180))
        frames.append(surf)
    return frames


def _gen_exploder_frames(size, color):
    frames = []
    s = size
    mid = s // 2
    light = tuple(min(255, c + 70) for c in color)
    for i in range(3):
        pulse = int(math.sin(i * 2.5) * 2)
        r = s // 2 - 2 + pulse
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        # Round body
        pygame.draw.circle(surf, color, (mid, mid), r)
        # Inner glow
        pygame.draw.circle(surf, light, (mid, mid), r // 2)
        # "Fuse" on top
        fuse_y = mid - r
        _px_vline(surf, mid, fuse_y - 3, 4, (255, 200, 100))
        _px(surf, mid, fuse_y - 4, (255, 100, 0))
        # Spikes around edge
        for ang in range(0, 360, 45):
            rad = math.radians(ang + i * 10)
            sx = int(mid + math.cos(rad) * (r + 1))
            sy = int(mid + math.sin(rad) * (r + 1))
            _px(surf, sx, sy, light)
        frames.append(surf)
    return frames


# ---- Bullet shapes ----

def _gen_bullet_surf(radius, color):
    size = radius * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    # Glowing core
    pygame.draw.circle(surf, color, (mid, mid), radius)
    # Brighter center
    light = tuple(min(255, c + 80) for c in color)
    pygame.draw.circle(surf, light, (mid, mid), max(1, radius // 2))
    # Trail
    pygame.draw.circle(surf, (*color, 100), (mid - radius, mid), radius // 2)
    return surf


# ---- XP Orb ----

def _gen_orb_surf(radius, color):
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    pygame.draw.circle(surf, color, (mid, mid), radius)
    light = tuple(min(255, c + 100) for c in color)
    pygame.draw.circle(surf, light, (mid - 1, mid - 1), max(1, radius // 2))
    return surf


# ---- Colors (imported locally to avoid circular imports) ----
GOLD = (255, 200, 0)
CYAN = (100, 200, 255)

# 卡通描边颜色（深色，土豆兄弟式的统一视觉语言）
OUTLINE_COLOR = (18, 14, 26)


def _apply_outline(frame, color=OUTLINE_COLOR, thickness=2):
    """给精灵加粗描边：用 mask 剪影向 8 方向偏移铺底，再盖上原图。"""
    mask = pygame.mask.from_surface(frame)
    sil = mask.to_surface(setcolor=(*color, 255),
                          unsetcolor=(0, 0, 0, 0)).convert_alpha()
    out = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
    t2 = thickness * thickness
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if (dx or dy) and dx * dx + dy * dy <= t2:
                out.blit(sil, (dx, dy))
    out.blit(frame, (0, 0))
    return out


# ---- Sound helpers ----

def _make_sound(samples):
    pcm = array("h")
    for value in samples:
        sample = int(max(-1.0, min(1.0, value)) * 32767)
        pcm.append(sample)
        pcm.append(sample)
    return pygame.mixer.Sound(buffer=pcm)


def _gen_shoot_sound():
    dur = 0.04
    n = int(SAMPLE_RATE * dur)
    noise_n = int(SAMPLE_RATE * 0.005)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1 - i / n
        value = math.sin(2 * math.pi * 800 * t) * env
        value += math.sin(2 * math.pi * 1200 * t) * env * 0.3
        if i < noise_n:
            value += random.uniform(-1, 1) * 0.15 * (1 - i / noise_n)
        samples.append(value * 0.7)
    return _make_sound(samples)


def _gen_death_sound():
    dur = 0.12
    freq = random.uniform(130, 180)
    n = int(SAMPLE_RATE * dur)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - i / n) ** 2
        value = math.sin(2 * math.pi * freq * t) * env * 0.6
        value += random.uniform(-1, 1) * env * 0.4
        samples.append(value * 0.5)
    return _make_sound(samples)


# ---- Public API ----

def load_image(name, fallback_color, size, animated=False):
    path = os.path.join(SPRITES, f"{name}.png")
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if animated:
            fw = img.get_width() // 3
            fh = img.get_height()
            frames = [pygame.transform.scale(img.subsurface((c * fw, 0, fw, fh)), (size, size))
                      for c in range(3)]
            return [_apply_outline(f) for f in frames]
        img = pygame.transform.scale(img, (size, size))
        if "bullet" in name or "orb" in name:
            return [img]
        return [_apply_outline(img)]

    # ---- Fallback: generated pixel art ----
    if animated:
        if name == "player":
            frames = _gen_player_frames(size, fallback_color)
        elif name == "elite":
            frames = _gen_elite_frames(size, fallback_color)
        elif name == "charger":
            frames = _gen_charger_frames(size, fallback_color)
        elif name == "ranger":
            frames = _gen_ranger_frames(size, fallback_color)
        elif name == "exploder":
            frames = _gen_exploder_frames(size, fallback_color)
        else:
            frames = _gen_enemy_frames(size, fallback_color)
        return [_apply_outline(f) for f in frames]

    if "bullet" in name:
        return [_gen_bullet_surf(size // 2, fallback_color)]
    if "orb" in name:
        return [_gen_orb_surf(size // 2, fallback_color)]
    # Simple colored square
    surf = pygame.Surface((size, size))
    surf.fill(fallback_color)
    return [surf]


def load_sound(name):
    path = os.path.join(SOUNDS, f"{name}.wav")
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    if name == "shoot":
        return _gen_shoot_sound()
    if name == "death":
        return _gen_death_sound()
    return None
