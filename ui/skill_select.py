"""技能选择界面"""
import pygame
from settings import GOLD, WHITE
from .drawables import get_font
from skills import get_skill_effect_desc


def draw_skill_selection(screen, big_font, small_font, skills, mouse_pos, acquired_skills=None, stats=None):
    """绘制技能选择界面，返回卡片区域列表
    acquired_skills: 已获得的技能名称列表
    stats: 当前游戏属性字典
    """
    sw, sh = screen.get_width(), screen.get_height()

    # 半透明遮罩
    overlay = pygame.Surface((sw, sh))
    overlay.set_alpha(235)
    overlay.fill((5, 2, 15))
    screen.blit(overlay, (0, 0))

    # 标题
    title = big_font.render("选 择 强 化", True, GOLD)
    title_rect = title.get_rect(center=(sw // 2, sh // 7))
    line_w = sw // 5
    line_y = title_rect.centery
    pygame.draw.line(screen, (80, 60, 30), (title_rect.left - line_w - 20, line_y),
                     (title_rect.left - 20, line_y), 2)
    pygame.draw.line(screen, (80, 60, 30), (title_rect.right + 20, line_y),
                     (title_rect.right + line_w + 20, line_y), 2)
    screen.blit(title, title_rect)

    card_w, card_h = 420, 95  # 增加高度以容纳效果显示
    card_x = (sw - card_w) // 2
    start_y = sh // 4
    gap = 14
    card_rects = []

    # 统计已获得技能数量
    acquired_count = {}
    if acquired_skills:
        for name in acquired_skills:
            acquired_count[name] = acquired_count.get(name, 0) + 1

    for i, skill in enumerate(skills):
        rect = pygame.Rect(card_x, start_y + i * (card_h + gap), card_w, card_h)
        card_rects.append(rect)
        hovered = rect.collidepoint(mouse_pos)

        # 卡片阴影
        shadow = rect.inflate(6, 6)
        pygame.draw.rect(screen, (20, 15, 35), shadow, border_radius=6)

        # 卡片背景
        if hovered:
            bg_color = (45, 35, 70)
            border_color = (255, 230, 100)
            border_w = 3
        else:
            bg_color = (20, 15, 35)
            border_color = (180, 140, 60)
            border_w = 2
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, border_w, border_radius=6)

        # 按键提示
        badge = pygame.Rect(rect.x + 10, rect.y + 12, 26, 26)
        pygame.draw.rect(screen, border_color, badge, border_radius=4)
        key_hint = small_font.render(str(i + 1), True, (10, 5, 20))
        key_rect = key_hint.get_rect(center=badge.center)
        screen.blit(key_hint, key_rect)

        # 技能名称
        name = small_font.render(skill["name"], True, GOLD if hovered else WHITE)
        screen.blit(name, (rect.x + 48, rect.y + 14))

        # 获取当前效果描述
        current_count = acquired_count.get(skill["name"], 0)
        effect_desc = ""
        if stats and current_count > 0:
            effect_desc = get_skill_effect_desc(skill["name"], stats)
        elif current_count == 0:
            effect_desc = skill["desc"]

        # 效果描述（第三行）
        desc_y = rect.y + 38
        if current_count > 0 and stats:
            # 显示当前效果
            effect_color = (100, 255, 150) if hovered else (80, 200, 120)
            effect_text = small_font.render(f"[当前 {effect_desc}]", True, effect_color)
            screen.blit(effect_text, (rect.x + 48, desc_y))

            # 显示本次选择效果
            next_effect = get_skill_effect_desc(skill["name"], stats)
            if hovered and effect_desc != next_effect:
                next_color = (255, 230, 100)
                next_text = small_font.render(f"→ {next_effect}", True, next_color)
                screen.blit(next_text, (rect.x + 48, desc_y + 16))
        else:
            # 首次选择
            desc_color = (210, 200, 225) if hovered else (170, 160, 190)
            desc = small_font.render(skill["desc"], True, desc_color)
            screen.blit(desc, (rect.x + 48, desc_y))

    return card_rects


def build_card_rects(count, sw, sh):
    """构建技能卡片区域（兼容旧接口）"""
    card_w, card_h = 420, 95
    card_x = (sw - card_w) // 2
    start_y = sh // 4
    gap = 14
    return [pygame.Rect(card_x, start_y + i * (card_h + gap), card_w, card_h)
            for i in range(count)]
