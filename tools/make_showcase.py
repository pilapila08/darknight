# -*- coding: utf-8 -*-
"""暗夜求生 · 玩法与特色介绍图生成器（信息图风格 PNG）。

背景用 Key Art（无水印版），叠加精确中文文字层：标题 / 核心玩法 / 6 大特色 / 版本信息。
输出：design/art/ai-samples/darknight_gameplay_intro.png
"""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.display.set_mode((64, 64))

W, H = 1280, 1600
OUT = os.path.join("design", "art", "ai-samples", "darknight_gameplay_intro.png")
BG_SRC = os.path.join("design", "art", "ai-samples", "darknight_version_showcase.png")

FONT = "microsoftyahei"


def make_font(size, bold=False):
    return pygame.font.SysFont(FONT, size, bold=bold)


def draw_text(screen, text, size, color, x, y, bold=False, anchor="tl", outline=None, alpha=255):
    f = make_font(size, bold)
    surf = f.render(text, True, color)
    if alpha < 255:
        surf.set_alpha(alpha)
    r = surf.get_rect()
    if anchor == "c":
        r.center = (x, y)
    elif anchor == "tc":
        r.midtop = (x, y)
    elif anchor == "tr":
        r.topright = (x, y)
    elif anchor == "br":
        r.bottomright = (x, y)
    elif anchor == "bl":
        r.bottomleft = (x, y)
    elif anchor == "bc":
        r.midbottom = (x, y)
    else:
        r.topleft = (x, y)
    if outline:
        o = f.render(text, True, outline)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            screen.blit(o, (r.x + dx, r.y + dy))
    screen.blit(surf, r)
    return r


def card(screen, x, y, w, h, bg=(20, 24, 34), border=(255, 200, 80)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*bg, 215))
    screen.blit(s, (x, y))
    pygame.draw.rect(screen, border, (x, y, w, h), 2, border_radius=10)


def main():
    screen = pygame.Surface((W, H))

    # 背景：Key Art 放大 + 上下渐变压暗
    bg = pygame.image.load(BG_SRC)
    bg = pygame.transform.smoothscale(bg, (W, H))
    screen.blit(bg, (0, 0))
    veil = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(H):
        t = y / H
        a = int(120 + 60 * t)  # 顶部稍暗，底部更暗
        pygame.draw.line(veil, (8, 10, 16, a), (0, y), (W, y))
    screen.blit(veil, (0, 0))

    GOLD = (255, 200, 80)
    WHITE = (240, 244, 250)
    SOFT = (190, 200, 214)

    # ===== 标题区 =====
    draw_text(screen, "暗夜求生", 92, GOLD, W // 2, 60, bold=True, anchor="tc", outline=(10, 8, 4))
    draw_text(screen, "DARKNIGHT SURVIVAL", 34, SOFT, W // 2, 170, anchor="tc", outline=(10, 8, 4))
    draw_text(screen, "俯视角自动射击 Roguelite · 在永夜中杀出一条生路", 28, WHITE, W // 2, 220, anchor="tc", outline=(10, 8, 4))

    # ===== 核心玩法卡 =====
    card(screen, 90, 300, W - 180, 250)
    draw_text(screen, "核心玩法", 30, GOLD, 130, 325, bold=True, outline=(10, 8, 4))
    steps = ["击杀敌人", "获取经验", "升级三选一", "变强", "面对更强敌人"]
    x = 130
    for i, s in enumerate(steps):
        draw_text(screen, s, 26, WHITE, x, 375, bold=True, outline=(10, 8, 4))
        r = make_font(26).size(s)
        if i < len(steps) - 1:
            draw_text(screen, "→", 30, GOLD, x + r[0] + 18, 375, bold=True, outline=(10, 8, 4))
        x += r[0] + 62
    draw_text(screen, "胜利条件：在怪物狂潮中存活 10 分钟，挑战最高分", 26, SOFT, W // 2, 470, anchor="tc", outline=(10, 8, 4))

    # ===== 六大特色 =====
    draw_text(screen, "游戏特色", 32, GOLD, W // 2, 620, bold=True, anchor="tc", outline=(10, 8, 4))
    features = [
        ("5 大主题地图", "墓地 / 沼泽 / 庭院 / 废墟 / 虚空，各具专属机制"),
        ("4 个时间轴 Boss", "尸王 → 暗影巫师 → 钢铁巨像 → 虚空之主"),
        ("14 种技能构筑", "穿透弹、连锁闪电、联动技能自由搭配"),
        ("3 个可解锁角色", "火枪手 / 重装坦克 / 游侠，玩法差异鲜明"),
        ("AI 像素美术", "全套 AI 生成素材 + 程序动画 + 动态光照"),
        ("程序合成音效", "真枪声与重低音爆炸，零版权负担"),
    ]
    cw, ch, gx, gy = (W - 120 - 40) // 2, 118, 60, 700
    for i, (title, desc) in enumerate(features):
        cx = gx + (i % 2) * (cw + 40)
        cy = gy + (i // 2) * (ch + 24)
        card(screen, cx, cy, cw, ch)
        draw_text(screen, title, 28, GOLD, cx + 24, cy + 18, bold=True, outline=(10, 8, 4))
        draw_text(screen, desc, 22, SOFT, cx + 24, cy + 62, outline=(10, 8, 4))

    # ===== 底部 =====
    draw_text(screen, "v1.0 开发版 · 单人开发 · 动态难度 · 每 25 秒世界变强", 24, WHITE, W // 2, H - 120, anchor="bc", outline=(10, 8, 4))
    draw_text(screen, "类《吸血鬼幸存者》 · 挑战你的极限生存", 22, SOFT, W // 2, H - 70, anchor="bc", outline=(10, 8, 4))

    pygame.image.save(screen, OUT)
    print(f"介绍图已生成: {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
