# -*- coding: utf-8 -*-
"""暗夜求生 · 宣传长图生成器（1080×2600 竖版海报）。

分区排版：标题区 → 主视觉立绘 → 核心循环 → 特色卡 → Boss 画廊 → 地图画廊 → 角色画廊 → 版本。
输出：design/art/ai-samples/darknight_poster.png
"""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.display.set_mode((64, 64))

W, H = 1080, 2600
OUT = os.path.join("design", "art", "ai-samples", "darknight_poster.png")
HERO_SRC = os.path.join("design", "art", "ai-samples", "dark_fantasy_pixel_art_hero_ch_2026-08-01T17-19-12.png")
SPR = "assets/sprites"
MAPS = "assets/maps"
FONT = "microsoftyahei"

GOLD = (255, 200, 80)
GOLD_DIM = (190, 150, 60)
WHITE = (245, 248, 252)
SOFT = (190, 200, 216)
DARK = (14, 16, 26)
PANEL = (20, 24, 38)


def F(size, bold=False):
    return pygame.font.SysFont(FONT, size, bold=bold)


def text(screen, s, size, color, x, y, bold=False, anchor="tl", outline=None):
    f = F(size, bold)
    surf = f.render(s, True, color)
    r = surf.get_rect()
    if anchor == "tc":
        r.midtop = (x, y)
    elif anchor == "c":
        r.center = (x, y)
    elif anchor == "bc":
        r.midbottom = (x, y)
    else:
        r.topleft = (x, y)
    if outline:
        o = f.render(s, True, outline)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            screen.blit(o, (r.x + dx, r.y + dy))
    screen.blit(surf, r)
    return r


def gold_line(screen, cx, y, w, tip="◆"):
    pygame.draw.line(screen, GOLD_DIM, (cx - w // 2, y), (cx + w // 2, y), 2)
    text(screen, tip, 18, GOLD, cx, y - 9, anchor="c")


def sprite_frame(path, height):
    s = pygame.image.load(path).convert_alpha()
    w, h = s.get_size()
    frame = s.subsurface((0, 0, w // 3, h))
    nw = max(1, int(frame.get_width() * height / frame.get_height()))
    return pygame.transform.scale(frame, (nw, height))


def disc(screen, cx, cy, r, color=(255, 200, 80, 60)):
    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(s, color, (r, r), r)
    screen.blit(s, (cx - r, cy - r))


def card(screen, x, y, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*PANEL, 225))
    screen.blit(s, (x, y))
    pygame.draw.rect(screen, GOLD_DIM, (x, y, w, h), 2, border_radius=14)


def main():
    screen = pygame.Surface((W, H))
    screen.fill(DARK)

    # ===== 1. 标题区 =====
    text(screen, "暗夜求生", 120, GOLD, W // 2, 90, bold=True, anchor="tc", outline=(10, 8, 4))
    text(screen, "DARKNIGHT SURVIVAL", 36, SOFT, W // 2, 240, anchor="tc", outline=(10, 8, 4))
    text(screen, "在永夜中杀出一条生路 · 类《吸血鬼幸存者》Roguelite", 27, WHITE, W // 2, 300, anchor="tc", outline=(10, 8, 4))
    gold_line(screen, W // 2, 372, 360)

    # ===== 2. 主视觉立绘 =====
    hero = pygame.image.load(HERO_SRC)
    hw, hh = hero.get_size()
    target_h = 560
    hero = pygame.transform.smoothscale(hero, (int(hw * target_h / hh), target_h))
    # 立绘底部渐隐融入背景
    fade = pygame.Surface(hero.get_size(), pygame.SRCALPHA)
    for y in range(hero.get_height()):
        a = max(0, int(255 * (y - hero.get_height() * 0.72) / (hero.get_height() * 0.28)))
        pygame.draw.line(fade, (*DARK, a), (0, y), (hero.get_width(), y))
    hero.blit(fade, (0, 0))
    screen.blit(hero, ((W - hero.get_width()) // 2, 400))
    # 两侧金色角标
    for x, flip in ((150, False), (W - 150, True)):
        for cy in range(480, 900, 24):
            pass

    # ===== 3. 核心循环 =====
    y0 = 1020
    text(screen, "核心玩法", 42, GOLD, W // 2, y0, bold=True, anchor="tc", outline=(10, 8, 4))
    gold_line(screen, W // 2, y0 + 62, 200)
    steps = ["击杀敌人", "获取经验", "升级三选一", "变强", "更强敌人"]
    sw = sum(F(26).size(s)[0] for s in steps) + (len(steps) - 1) * 96
    x = (W - sw) // 2
    for i, s in enumerate(steps):
        text(screen, s, 26, WHITE, x, y0 + 95, bold=True, outline=(10, 8, 4))
        w_ = F(26).size(s)[0]
        if i < len(steps) - 1:
            text(screen, "→", 34, GOLD, x + w_ + 40, y0 + 90, bold=True, anchor="c")
        x += w_ + 96
    text(screen, "胜利条件：在怪物狂潮中存活 10 分钟，挑战最高分", 25, SOFT, W // 2, y0 + 165, anchor="tc")

    # ===== 4. 特色卡 =====
    y1 = 1310
    text(screen, "游戏特色", 42, GOLD, W // 2, y1, bold=True, anchor="tc", outline=(10, 8, 4))
    gold_line(screen, W // 2, y1 + 62, 200)
    feats = [
        ("5 大主题地图", "墓地 / 沼泽 / 庭院 / 废墟 / 虚空", "boss_corpse_king"),
        ("4 个时间轴 Boss", "尸王 → 暗影巫师 → 钢铁巨像 → 虚空之主", "boss_shadow_mage"),
        ("14 种技能构筑", "穿透弹 · 连锁闪电 · 联动技能自由搭配", "elite"),
        ("3 个可解锁角色", "火枪手 · 重装坦克 · 游侠，玩法差异鲜明", "player"),
        ("5 类敌人", "基础 / 冲锋 / 远程 / 自爆 / 精英", "charger"),
        ("AI 像素美术", "程序动画 · 动态光照 · 打击感与合成音效", "ranger"),
    ]
    cw, ch, gx, gy = (W - 100 - 36) // 2, 150, 50, y1 + 100
    for i, (title, desc, icon) in enumerate(feats):
        cx = gx + (i % 2) * (cw + 36)
        cy = gy + (i // 2) * (ch + 24)
        card(screen, cx, cy, cw, ch)
        disc(screen, cx + 66, cy + ch // 2, 46)
        img = sprite_frame(os.path.join(SPR, f"{icon}.png"), 84)
        screen.blit(img, (cx + 66 - img.get_width() // 2, cy + (ch - 84) // 2))
        text(screen, title, 28, GOLD, cx + 126, cy + 28, bold=True, outline=(10, 8, 4))
        text(screen, desc, 21, SOFT, cx + 126, cy + 78, outline=(10, 8, 4))

    # ===== 5. Boss 画廊 =====
    y2 = gy + 3 * (ch + 24) + 60
    text(screen, "时间轴 Boss 战", 42, GOLD, W // 2, y2, bold=True, anchor="tc", outline=(10, 8, 4))
    gold_line(screen, W // 2, y2 + 62, 240)
    bosses = [("尸王", "120s", "boss_corpse_king"), ("暗影巫师", "240s", "boss_shadow_mage"),
              ("钢铁巨像", "360s", "boss_iron_colossus"), ("虚空之主", "480s", "boss_void_lord")]
    bw = (W - 100 - 3 * 24) // 4
    for i, (name, t, icon) in enumerate(bosses):
        cx = 50 + i * (bw + 24)
        cy = y2 + 100
        card(screen, cx, cy, bw, 240)
        disc(screen, cx + bw // 2, cy + 92, 56)
        img = sprite_frame(os.path.join(SPR, f"{icon}.png"), 100)
        screen.blit(img, (cx + bw // 2 - img.get_width() // 2, cy + 42))
        text(screen, name, 26, GOLD, cx + bw // 2, cy + 168, bold=True, anchor="tc", outline=(10, 8, 4))
        text(screen, t, 21, SOFT, cx + bw // 2, cy + 208, anchor="tc")

    # ===== 6. 地图画廊 =====
    y3 = y2 + 100 + 240 + 60
    text(screen, "五张主题地图", 42, GOLD, W // 2, y3, bold=True, anchor="tc", outline=(10, 8, 4))
    gold_line(screen, W // 2, y3 + 62, 220)
    maps = [("荒芜墓地", "bleak_graveyard_256"), ("腐化沼泽", "corrupted_swamp_256"),
            ("暗影庭院", "shadow_court_256"), ("钢铁废墟", "iron_ruins_256"), ("虚空裂缝", "void_rift_256")]
    mw = (W - 100 - 4 * 20) // 5
    for i, (name, icon) in enumerate(maps):
        cx = 50 + i * (mw + 20)
        cy = y3 + 100
        card(screen, cx, cy, mw, mw + 60)
        thumb = pygame.transform.scale(pygame.image.load(os.path.join(MAPS, f"{icon}.png")), (mw - 24, mw - 24))
        screen.blit(thumb, (cx + 12, cy + 12))
        text(screen, name, 21, SOFT, cx + mw // 2, cy + mw + 22, anchor="tc")

    # ===== 7. 角色画廊 =====
    y4 = y3 + 100 + mw + 60 + 60
    text(screen, "可解锁角色", 42, GOLD, W // 2, y4, bold=True, anchor="tc", outline=(10, 8, 4))
    gold_line(screen, W // 2, y4 + 62, 220)
    chars = [("幸存者", "默认", "player"), ("火枪手", "累计500杀", "player"),
             ("重装坦克", "击杀Boss1", "player"), ("游侠", "单局200杀", "player")]
    pw = (W - 100 - 3 * 24) // 4
    for i, (name, cond, icon) in enumerate(chars):
        cx = 50 + i * (pw + 24)
        cy = y4 + 100
        card(screen, cx, cy, pw, 230)
        disc(screen, cx + pw // 2, cy + 88, 52)
        img = sprite_frame(os.path.join(SPR, f"{icon}.png"), 96)
        screen.blit(img, (cx + pw // 2 - img.get_width() // 2, cy + 40))
        text(screen, name, 25, GOLD, cx + pw // 2, cy + 158, bold=True, anchor="tc", outline=(10, 8, 4))
        text(screen, cond, 20, SOFT, cx + pw // 2, cy + 196, anchor="tc")

    # ===== 8. 底部 =====
    gold_line(screen, W // 2, H - 150, 420)
    text(screen, "v1.0 开发版 · 单人开发 · 动态难度", 26, WHITE, W // 2, H - 118, anchor="tc", outline=(10, 8, 4))
    text(screen, "AI 像素美术 · 程序动画 · 动态光照 · 合成音效", 23, SOFT, W // 2, H - 70, anchor="tc")

    pygame.image.save(screen, OUT)
    print(f"宣传长图已生成: {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
