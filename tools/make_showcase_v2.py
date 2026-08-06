# -*- coding: utf-8 -*-
"""暗夜求生 · 玩法与特色介绍图 v2（信息图 + 游戏内素材图标）。

在 Key Art 背景上，用游戏真实精灵表/地图纹理做图标，排版标题/核心玩法/特色卡片/版本信息。
输出：design/art/ai-samples/darknight_gameplay_intro_v2.png
"""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.display.set_mode((64, 64))

W, H = 1280, 1600
OUT = os.path.join("design", "art", "ai-samples", "darknight_gameplay_intro_v2.png")
BG_SRC = os.path.join("design", "art", "ai-samples", "darknight_version_showcase.png")
SPR = "assets/sprites"
MAPS = "assets/maps"
FONT = "microsoftyahei"


def make_font(size, bold=False):
    return pygame.font.SysFont(FONT, size, bold=bold)


def draw_text(screen, text, size, color, x, y, bold=False, anchor="tl", outline=None):
    f = make_font(size, bold)
    surf = f.render(text, True, color)
    r = surf.get_rect()
    r.center = (x, y) if anchor == "c" else r.center
    if anchor == "tc":
        r.midtop = (x, y)
    elif anchor == "c":
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    if outline:
        o = f.render(text, True, outline)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            screen.blit(o, (r.x + dx, r.y + dy))
    screen.blit(surf, r)
    return r


def load_sprite_first_frame(path, scale_to):
    """读取精灵表第 1 帧并缩放到目标高度（像素硬边）。"""
    s = pygame.image.load(path).convert_alpha()
    w, h = s.get_size()
    frame = s.subsurface((0, 0, w // 3, h))  # 3 帧表取第 1 帧
    fh = frame.get_height()
    nw = max(1, int(frame.get_width() * scale_to / fh))
    return pygame.transform.scale(frame, (nw, scale_to))


def load_map_thumb(path, size):
    s = pygame.image.load(path)
    return pygame.transform.scale(s, (size, size))


def card(screen, x, y, w, h, bg=(16, 20, 30)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*bg, 210))
    screen.blit(s, (x, y))
    pygame.draw.rect(screen, (255, 200, 80), (x, y, w, h), 2, border_radius=12)


def main():
    GOLD = (255, 200, 80)
    WHITE = (242, 246, 252)
    SOFT = (195, 205, 218)
    OUTLINE = (10, 8, 4)

    screen = pygame.Surface((W, H))
    bg = pygame.transform.smoothscale(pygame.image.load(BG_SRC), (W, H))
    screen.blit(bg, (0, 0))
    # 上下压暗，中间保留 Key Art 主体
    veil = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(H):
        t = y / H
        a = int(150 - 40 * abs(t - 0.45) * 2)  # 中部最亮（显主体），上下暗
        pygame.draw.line(veil, (8, 10, 16, max(40, a)), (0, y), (W, y))
    screen.blit(veil, (0, 0))

    # ===== 标题区 =====
    draw_text(screen, "暗夜求生", 96, GOLD, W // 2, 70, bold=True, anchor="tc", outline=OUTLINE)
    draw_text(screen, "DARKNIGHT SURVIVAL", 32, SOFT, W // 2, 178, anchor="tc", outline=OUTLINE)
    draw_text(screen, "俯视角自动射击 Roguelite", 28, WHITE, W // 2, 222, anchor="tc", outline=OUTLINE)

    # ===== 主角区：玩家精灵 + 核心玩法 =====
    card(screen, 90, 290, W - 180, 210)
    player_img = load_sprite_first_frame(os.path.join(SPR, "player.png"), 140)
    screen.blit(player_img, (150, 320))
    draw_text(screen, "核心循环", 30, GOLD, 330, 320, bold=True, outline=OUTLINE)
    draw_text(screen, "击杀敌人 → 获取经验 → 升级三选一 → 变强 → 面对更强敌人", 26, WHITE, 330, 375, outline=OUTLINE)
    draw_text(screen, "胜利条件：存活 10 分钟 · 挑战最高分", 26, SOFT, 330, 435, outline=OUTLINE)

    # ===== 特色区：图标卡片 =====
    draw_text(screen, "游戏特色", 34, GOLD, W // 2, 560, bold=True, anchor="tc", outline=OUTLINE)

    feats = [
        ("5 大主题地图", "墓地 / 沼泽 / 庭院 / 废墟 / 虚空", load_map_thumb(os.path.join(MAPS, "bleak_graveyard_256.png"), 72)),
        ("4 个时间轴 Boss", "尸王 → 暗影巫师 → 钢铁巨像 → 虚空之主", load_sprite_first_frame(os.path.join(SPR, "boss_corpse_king.png"), 72)),
        ("14 种技能构筑", "穿透弹 · 连锁闪电 · 联动技能自由搭配", load_sprite_first_frame(os.path.join(SPR, "elite.png"), 72)),
        ("3 个可解锁角色", "火枪手 · 重装坦克 · 游侠", load_sprite_first_frame(os.path.join(SPR, "player.png"), 72)),
        ("5 类敌人", "基础 / 冲锋 / 远程 / 自爆 / 精英", load_sprite_first_frame(os.path.join(SPR, "charger.png"), 72)),
        ("AI 像素美术 + 程序动画", "动态光照 · 暗但不黑 · 打击感", load_map_thumb(os.path.join(MAPS, "void_rift_256.png"), 72)),
    ]
    cw, ch, gx, gy = (W - 120 - 40) // 2, 128, 60, 640
    for i, (title, desc, icon) in enumerate(feats):
        cx = gx + (i % 2) * (cw + 40)
        cy = gy + (i // 2) * (ch + 22)
        card(screen, cx, cy, cw, ch)
        screen.blit(icon, (cx + 20, cy + (ch - icon.get_height()) // 2))
        draw_text(screen, title, 28, GOLD, cx + 110, cy + 22, bold=True, outline=OUTLINE)
        draw_text(screen, desc, 21, SOFT, cx + 110, cy + 72, outline=OUTLINE)

    # ===== 底部 =====
    draw_text(screen, "v1.0 开发版 · 单人开发 · 动态难度", 24, WHITE, W // 2, H - 120, anchor="c", outline=OUTLINE)
    draw_text(screen, "类《吸血鬼幸存者》 · 挑战极限生存", 22, SOFT, W // 2, H - 70, anchor="c", outline=OUTLINE)

    pygame.image.save(screen, OUT)
    print(f"介绍图 v2 已生成: {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
