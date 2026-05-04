"""技能选择界面"""
import pygame
from settings import GOLD, WHITE
from .drawables import get_font
from skills import get_skill_detail_desc


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

    card_w, card_h = 500, 135  # 增大卡片高度
    card_x = (sw - card_w) // 2
    start_y = sh // 4 - 30
    gap = 18
    card_rects = []

    # 统计已获得技能数量
    acquired_count = {}
    if acquired_skills:
        for name in acquired_skills:
            acquired_count[name] = acquired_count.get(name, 0) + 1

    # 使用 small_font 作为描述字体（更大更清晰）
    desc_font = small_font
    line_height = 22  # 行高

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
        badge = pygame.Rect(rect.x + 14, rect.y + 14, 30, 30)
        pygame.draw.rect(screen, border_color, badge, border_radius=4)
        key_hint = small_font.render(str(i + 1), True, (10, 5, 20))
        key_rect = key_hint.get_rect(center=badge.center)
        screen.blit(key_hint, key_rect)

        # 技能名称
        name = small_font.render(skill["name"], True, GOLD if hovered else WHITE)
        screen.blit(name, (rect.x + 56, rect.y + 14))

        # 获取详细描述
        current_skill_count = acquired_count.get(skill["name"], 0)
        base_desc, current_desc, next_desc = get_skill_detail_desc(skill["name"], stats, current_skill_count)

        # 第一行：基础描述
        base_y = rect.y + 46
        base_color = (200, 210, 230)
        base_text = desc_font.render(base_desc, True, base_color)
        screen.blit(base_text, (rect.x + 56, base_y))

        # 第二行：当前效果（如果已选过）
        if current_skill_count > 0:
            current_y = base_y + line_height
            count_color = (255, 210, 100)
            count_text = desc_font.render(f"已选 {current_skill_count} 次 | {current_desc}", True, count_color)
            screen.blit(count_text, (rect.x + 56, current_y))

        # 第三行：下次选择效果（悬停时）
        if hovered and next_desc:
            next_y = base_y + line_height * (2 if current_skill_count > 0 else 1)
            next_color = (100, 255, 150)
            arrow = "▶ " if current_skill_count == 0 else "→ "
            next_text = desc_font.render(arrow + next_desc, True, next_color)
            screen.blit(next_text, (rect.x + 56, next_y))

    return card_rects


def build_card_rects(count, sw, sh):
    """构建技能卡片区域（兼容旧接口）"""
    card_w, card_h = 500, 135
    card_x = (sw - card_w) // 2
    start_y = sh // 4 - 30
    gap = 18
    return [pygame.Rect(card_x, start_y + i * (card_h + gap), card_w, card_h)
            for i in range(count)]
