"""角色选择界面（R5）。

依据 design/gdd/playability-pack-v1.md §3：主菜单"开始游戏"前插入角色选择层；
锁定角色显示解锁条件；解锁状态持久化（systems.save_data）；展示 meta 统计。
"""
import pygame
from settings import GOLD, GREEN, RED, SCREEN_WIDTH, SCREEN_HEIGHT
from characters import CHARACTERS, CHARACTER_ORDER

# 卡片顶部到解锁状态行的相对 y 偏移
_NAME_Y = 30
_DESC_Y0 = 66
_DESC_LH = 20
_STATUS_Y = 150
_UNLOCK_TEXT_Y = 172
_PASSIVE_Y = 205
_SELECT_Y = 235


def build_character_select_layout(sw, sh):
    """计算角色卡片与按钮区域；返回 (card_rects, start_btn_rect, back_btn_rect)。"""
    card_w, card_h = 268, 300
    gap = 22
    total = len(CHARACTER_ORDER) * card_w + (len(CHARACTER_ORDER) - 1) * gap
    x0 = (sw - total) // 2
    y0 = 130
    card_rects = {}
    for i, ch in enumerate(CHARACTER_ORDER):
        card_rects[ch] = pygame.Rect(x0 + i * (card_w + gap), y0, card_w, card_h)
    start_btn = pygame.Rect(sw // 2 - 110, sh - 112, 220, 52)
    back_btn = pygame.Rect(sw // 2 - 110, sh - 52, 220, 40)
    return card_rects, start_btn, back_btn


def draw_character_select(screen, big_font, font, small_font, selected_character,
                          meta, unlocks, card_rects, start_btn_rect, back_btn_rect):
    """绘制角色选择层；meta/unlocks 为读到的存档数据（不在此处落盘）。"""
    sw, sh = screen.get_width(), screen.get_height()
    screen.fill((10, 5, 20))

    # 顶部标题 + 装饰线
    title = big_font.render("选 择 角 色", True, GOLD)
    screen.blit(title, title.get_rect(center=(sw // 2, 60)))
    line_w = 260
    pygame.draw.line(screen, (150, 120, 60), (sw // 2 - line_w, 100),
                     (sw // 2 + line_w, 100), 1)

    mouse_pos = pygame.mouse.get_pos()
    unlocks = unlocks or {}

    for ch in CHARACTER_ORDER:
        cfg = CHARACTERS[ch]
        rect = card_rects[ch]
        locked = not unlocks.get(ch, True)
        selected = (ch == selected_character)
        hovered = rect.collidepoint(mouse_pos)

        # 卡片背景
        bg = (58, 50, 88) if selected else (44, 38, 66)
        if hovered and not locked:
            bg = (66, 58, 100)
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        if selected:
            border = GOLD
        else:
            border = (110, 60, 60) if locked else ((120, 110, 150) if hovered else (100, 92, 128))
        pygame.draw.rect(screen, border, rect, 3 if selected else (2 if hovered else 1),
                         border_radius=10)

        # 名称
        name_color = GOLD if selected else ((200, 200, 210) if not locked else (150, 130, 130))
        name = font.render(cfg["name"], True, name_color)
        screen.blit(name, name.get_rect(center=(rect.centerx, rect.y + _NAME_Y)))

        # 描述（两行）
        dy = rect.y + _DESC_Y0
        for line in cfg.get("desc", []):
            ds = small_font.render(line, True, (190, 190, 200))
            screen.blit(ds, ds.get_rect(center=(rect.centerx, dy)))
            dy += _DESC_LH

        # 解锁状态
        if ch == "default":
            status = small_font.render("默认解锁", True, GREEN)
            screen.blit(status, status.get_rect(center=(rect.centerx, rect.y + _STATUS_Y)))
        elif locked:
            status = small_font.render("未解锁", True, RED)
            screen.blit(status, status.get_rect(center=(rect.centerx, rect.y + _STATUS_Y)))
            ut = small_font.render(cfg.get("unlock_text", ""), True, (220, 170, 170))
            screen.blit(ut, ut.get_rect(center=(rect.centerx, rect.y + _UNLOCK_TEXT_Y)))
        else:
            status = small_font.render("已解锁", True, GREEN)
            screen.blit(status, status.get_rect(center=(rect.centerx, rect.y + _STATUS_Y)))

        # 被动提示
        pt = small_font.render(cfg.get("passive_text", ""), True, (170, 200, 230))
        screen.blit(pt, pt.get_rect(center=(rect.centerx, rect.y + _PASSIVE_Y)))

        # 当前选择标记
        if selected:
            sel = small_font.render("▼ 当前选择", True, GOLD)
            screen.blit(sel, sel.get_rect(center=(rect.centerx, rect.y + _SELECT_Y)))

    # meta 统计行（总击杀/胜利/最高分/总场次/单局纪录）
    meta = meta or {}
    stats_line = "总击杀: {}    胜利: {}    最高分: {}    总场次: {}    单局纪录: {}".format(
        meta.get("total_kills", 0), meta.get("victories", 0),
        meta.get("high_score", 0), meta.get("total_runs", 0),
        meta.get("best_run_kills", 0))
    st = small_font.render(stats_line, True, (180, 180, 195))
    screen.blit(st, st.get_rect(center=(sw // 2, sh - 150)))

    # 开始按钮
    hover_start = start_btn_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (70, 55, 110) if hover_start else (50, 40, 80),
                     start_btn_rect, border_radius=8)
    pygame.draw.rect(screen, GOLD, start_btn_rect, 2, border_radius=8)
    st2 = font.render("开 始 游 戏", True, GOLD)
    screen.blit(st2, st2.get_rect(center=start_btn_rect.center))

    # 返回按钮
    hover_back = back_btn_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (50, 46, 72) if hover_back else (40, 36, 58),
                     back_btn_rect, border_radius=6)
    pygame.draw.rect(screen, (120, 120, 150), back_btn_rect, 1, border_radius=6)
    bk = small_font.render("返回 (ESC)", True, (170, 170, 185))
    screen.blit(bk, bk.get_rect(center=back_btn_rect.center))


def handle_character_select_input(event, card_rects, start_btn_rect, back_btn_rect,
                                  selected_character="default", unlocks=None):
    """处理角色选择层输入。

    返回动作：
      "start"          开始游戏（当前选择角色）
      "back"           返回开始界面
      "select:<char>"  选中某角色
      None             无动作
    锁定角色不可选中/启动（unlocks.get(ch, True) 判定，default 恒 True）。
    """
    unlocks = unlocks or {}
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return "back"
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "start"
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            unlocked_order = [c for c in CHARACTER_ORDER if unlocks.get(c, True)]
            if not unlocked_order:
                return None
            if selected_character in unlocked_order:
                idx = unlocked_order.index(selected_character)
            else:
                idx = -1
            if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                nxt = (idx + 1) % len(unlocked_order)
            else:
                nxt = (idx - 1) % len(unlocked_order)
            return "select:" + unlocked_order[nxt]
        if pygame.K_1 <= event.key <= pygame.K_9:
            idx = event.key - pygame.K_1
            if idx < len(CHARACTER_ORDER) and unlocks.get(CHARACTER_ORDER[idx], True):
                return "select:" + CHARACTER_ORDER[idx]
    if event.type == pygame.MOUSEBUTTONDOWN:
        if start_btn_rect is not None and start_btn_rect.collidepoint(event.pos):
            return "start"
        if back_btn_rect is not None and back_btn_rect.collidepoint(event.pos):
            return "back"
        for ch, rect in card_rects.items():
            if rect.collidepoint(event.pos) and unlocks.get(ch, True):
                return "select:" + ch
    return None
