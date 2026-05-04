"""底部技能栏UI"""
import math
import pygame
from settings import GOLD
from .drawables import draw_skill_icon_shape, get_font, SKILL_ICONS
from skills import get_skill_effect_desc


def draw_skill_bar(screen, font, acquired_skills, mouse_pos=None, elapsed_time=0, stats=None):
    """在屏幕底部绘制已获得技能的图标栏
    stats: 当前游戏属性字典（用于显示技能效果）
    """
    if not acquired_skills:
        return

    sw = screen.get_width()
    icon_size = 44
    icon_spacing = 8
    padding = 12
    bar_height = icon_size + padding * 2 + 18
    tooltip_height = 30  # 悬停提示区域高度

    # 计算每个技能的获得次数
    skill_counts = {}
    for name in acquired_skills:
        skill_counts[name] = skill_counts.get(name, 0) + 1

    # 去除重复项，保留唯一技能
    unique_skills = []
    seen = set()
    for name in acquired_skills:
        if name not in seen:
            unique_skills.append(name)
            seen.add(name)

    # 计算总宽度并居中
    total_width = len(unique_skills) * icon_size + (len(unique_skills) - 1) * icon_spacing + padding * 2
    bar_x = (sw - total_width) // 2
    bar_y = screen.get_height() - bar_height - tooltip_height - 8

    # 绘制半透明背景
    bg_surf = pygame.Surface((total_width, bar_height), pygame.SRCALPHA)
    bg_surf.fill((15, 10, 25, 200))
    screen.blit(bg_surf, (bar_x, bar_y))

    # 绘制发光边框
    glow_alpha = int(80 + 30 * math.sin(elapsed_time * 3))
    glow_surf = pygame.Surface((total_width + 8, bar_height + 8), pygame.SRCALPHA)
    glow_surf.fill((100, 80, 60, glow_alpha))
    screen.blit(glow_surf, (bar_x - 4, bar_y - 4))

    pygame.draw.rect(screen, (120, 100, 80), (bar_x, bar_y, total_width, bar_height), 2, border_radius=8)

    hovered_skill = None  # 记录当前悬停的技能

    # 绘制每个技能图标
    for i, skill_name in enumerate(unique_skills):
        icon_x = bar_x + padding + i * (icon_size + icon_spacing)
        icon_y = bar_y + padding

        icon_info = SKILL_ICONS.get(skill_name, {
            "color": (150, 150, 150), "glow": (200, 200, 200),
            "shape": "trap", "border": (100, 100, 100)
        })
        count = skill_counts.get(skill_name, 1)

        # 检测是否hover
        is_hovered = mouse_pos and (
            icon_x <= mouse_pos[0] <= icon_x + icon_size and
            icon_y <= mouse_pos[1] <= icon_y + icon_size
        )

        if is_hovered:
            hovered_skill = skill_name

        # 图标背景发光
        if is_hovered:
            glow_size = icon_size + 8
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_surf.fill((*icon_info["glow"], 60))
            pygame.draw.rect(glow_surf, (*icon_info["glow"], 40), glow_surf.get_rect(), border_radius=6)
            screen.blit(glow_surf, (icon_x - 4, icon_y - 4))

        # 图标背景
        bg_rect = pygame.Rect(icon_x, icon_y, icon_size, icon_size)
        pygame.draw.rect(screen, (30, 25, 40), bg_rect, border_radius=6)
        pygame.draw.rect(screen, icon_info["border"], bg_rect, 2, border_radius=6)

        # 绘制技能形状
        draw_skill_icon_shape(screen, icon_x, icon_y, icon_size, icon_info)

        # 绘制技能计数
        if count > 1:
            count_font = get_font(14)
            count_text = count_font.render(f"x{count}", True, GOLD)
            count_rect = count_text.get_rect(bottomright=(icon_x + icon_size - 2, icon_y + icon_size - 2))
            screen.blit(count_text, count_rect)

        # 绘制技能名称
        small_font = get_font(11)
        name_text = small_font.render(skill_name[:4], True, (200, 190, 170) if is_hovered else (150, 140, 120))
        name_rect = name_text.get_rect(center=(icon_x + icon_size // 2, icon_y + icon_size + 12))
        screen.blit(name_text, name_rect)

    # 绘制悬停技能效果提示
    if hovered_skill and stats:
        # 获取该技能的选取次数
        skill_count = skill_counts.get(hovered_skill, 1)
        effect_desc = get_skill_effect_desc(hovered_skill, stats, skill_count)
        tooltip_y = bar_y - 35

        # 提示背景
        tooltip_font = get_font(13)
        text_surface = tooltip_font.render(f"{hovered_skill}: {effect_desc}", True, (220, 210, 180))
        text_rect = text_surface.get_rect(center=(sw // 2, tooltip_y))

        # 背景框
        bg_width = text_rect.width + 20
        bg_height = text_rect.height + 8
        bg_rect = pygame.Rect(text_rect.centerx - bg_width // 2, text_rect.top - 4, bg_width, bg_height)
        pygame.draw.rect(screen, (20, 15, 35), bg_rect, border_radius=4)
        pygame.draw.rect(screen, (150, 130, 80), bg_rect, 1, border_radius=4)

        screen.blit(text_surface, text_rect)
