# -*- coding: utf-8 -*-
"""AI 概念图 → 像素精灵表 后处理流水线（ai-asset-pipeline §3 的实现）。

流程：亮度抠图(matte) → bbox 裁剪居中 → 降采样到帧尺寸 → 3 帧 wobble 扩展 → 合成精灵表。

用法：python tools/ai_sprite_pipeline.py
输出：design/art/ai-samples/final/{name}.png（不直接覆盖 assets/sprites/，先人工确认）
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.display.set_mode((64, 64))

BASE = os.path.join("design", "art", "ai-samples")
OUT = os.path.join(BASE, "final")

# 定稿映射：资产名 -> (候选图相对路径, 帧尺寸)
ASSETS = {
    # 角色类（3 帧 × 16px）
    "player":   ("p1-player/pixel_art_hero_character_varia_2026-07-31T16-16-50.png", 16),
    "enemy":    ("p1-enemy/pixel_art_monster_concept__bas_2026-07-31T16-13-55.png", 16),
    "elite":    ("p0-elite/pixel_art_monster_concept__eli_2026-07-31T15-53-51.png", 16),
    "charger":  ("p0-charger/pixel_art_monster_concept__cha_2026-07-31T15-54-16.png", 16),
    "ranger":   ("p1-ranger/pixel_art_monster_concept__hoo_2026-07-31T16-14-21.png", 16),
    "exploder": ("p1-exploder/pixel_art_monster_concept__exp_2026-07-31T16-16-26.png", 16),
    "shadow":   ("p2-minion/pixel_art_monster_concept__sha_2026-07-31T16-21-48.png", 16),
    "voidling": ("p2-minion/pixel_art_monster_concept__voi_2026-07-31T16-22-12.png", 16),
    # Boss 类（3 帧 × 96px）
    "boss_corpse_king":    ("p2-boss/pixel_art_boss_monster_concept_2026-07-31T16-18-25.png", 96),
    "boss_shadow_mage":    ("p2-boss/pixel_art_boss_monster_concept_2026-07-31T16-20-32.png", 96),
    "boss_iron_colossus":  ("p2-boss/pixel_art_boss_monster_concept_2026-07-31T16-19-16.png", 96),
    "boss_void_lord":      ("p2-boss/pixel_art_boss_monster_concept_2026-07-31T16-19-41.png", 96),
}

BG_THRESHOLD = 45  # 与背景色距离小于此值视为背景（透明）


def estimate_bg(surf):
    """用四角均值估计背景亮度。"""
    w, h = surf.get_size()
    pts = [(5, 5), (w - 6, 5), (5, h - 6), (w - 6, h - 6)]
    vals = [sum(tuple(surf.get_at(p))[:3]) / 3.0 for p in pts]
    return sum(vals) / len(vals)


def matte(surf):
    """亮度差分抠图：背景(亮) → 透明，主体(暗) → 保留。"""
    w, h = surf.get_size()
    bg = estimate_bg(surf)
    bgc = (int(bg), int(bg), int(bg))
    bg_mask = pygame.mask.from_threshold(surf, bgc, (BG_THRESHOLD, BG_THRESHOLD, BG_THRESHOLD, 255))
    bg_mask.invert()  # 原地反转：主体为 1
    body = bg_mask
    alpha = body.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.blit(surf, (0, 0))
    out.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def crop_center(surf, frame_size):
    """bbox 裁剪 → 等比缩放到帧高 80% → 居中到 frame。"""
    mask = pygame.mask.from_surface(surf)
    rects = mask.get_bounding_rects()
    if not rects:
        return pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
    x0 = min(r.x for r in rects); y0 = min(r.y for r in rects)
    x1 = max(r.x + r.w for r in rects); y1 = max(r.y + r.h for r in rects)
    crop = surf.subsurface(pygame.Rect(x0, y0, x1 - x0, y1 - y0))
    target_h = max(2, int(frame_size * 0.8))
    scale = target_h / crop.get_height()
    new_w = max(1, int(crop.get_width() * scale))
    scaled = pygame.transform.scale(crop, (new_w, target_h))
    frame = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
    frame.blit(scaled, ((frame_size - new_w) // 2, (frame_size - target_h) // 2))
    return frame


def wobble(frame, frame_size):
    """3 帧扩展：静止 / 下移1px / 上移1px（走路感）。"""
    f1 = frame
    f2 = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
    f2.blit(frame, (0, 1))
    f3 = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
    f3.blit(frame, (0, -1))
    return f1, f2, f3


def compose(frames, frame_size):
    sheet = pygame.Surface((frame_size * 3, frame_size), pygame.SRCALPHA)
    for i, f in enumerate(frames):
        sheet.blit(f, (i * frame_size, 0))
    return sheet


def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    for name, (rel, fs) in ASSETS.items():
        path = os.path.join(BASE, rel)
        if not os.path.exists(path):
            results.append(f"{name}: MISSING {rel}")
            continue
        src = pygame.image.load(path)
        m = matte(src)
        f0 = crop_center(m, fs)
        frames = wobble(f0, fs)
        sheet = compose(frames, fs)
        out_path = os.path.join(OUT, f"{name}.png")
        pygame.image.save(sheet, out_path)
        # 统计不透明占比
        mask = pygame.mask.from_surface(sheet)
        results.append(f"{name}: {fs*3}x{fs}  opaque={mask.count()/(fs*3*fs)*100:.0f}%  -> {out_path}")
    print("\n".join(results))


if __name__ == "__main__":
    main()
