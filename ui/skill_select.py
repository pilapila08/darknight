"""Skill selection overlay."""
import pygame
from settings import GOLD, WHITE
from .drawables import draw_skill_icon_shape, get_font, SKILL_ICONS
from skills import get_skill_detail_desc


def _fit_lines(font, text, max_width, max_lines=2):
    if not text:
        return []
    lines = []
    current = ""
    for ch in text:
        trial = current + ch
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and font.size(lines[-1])[0] > max_width:
        while lines[-1] and font.size(lines[-1] + "...")[0] > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "..."
    return lines


def _draw_card(screen, rect, skill, index, hovered, small_font, acquired_count, stats):
    shadow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=8)
    screen.blit(shadow, (rect.x - 8, rect.y - 5))

    bg = (28, 30, 42) if not hovered else (36, 40, 58)
    border = (88, 96, 122) if not hovered else (250, 205, 90)
    pygame.draw.rect(screen, bg, rect, border_radius=8)
    pygame.draw.rect(screen, border, rect, 2 if not hovered else 3, border_radius=8)

    icon_info = SKILL_ICONS.get(skill["name"], {
        "color": (150, 150, 150), "glow": (200, 200, 200),
        "shape": "trap", "border": (100, 100, 100)
    })
    icon_rect = pygame.Rect(rect.x + 20, rect.y + 18, 58, 58)
    pygame.draw.rect(screen, (16, 18, 26), icon_rect, border_radius=8)
    pygame.draw.rect(screen, icon_info["border"], icon_rect, 2, border_radius=8)
    draw_skill_icon_shape(screen, icon_rect.x + 7, icon_rect.y + 7, 44, icon_info)

    key_badge = pygame.Rect(rect.right - 46, rect.y + 18, 28, 28)
    pygame.draw.rect(screen, border, key_badge, border_radius=6)
    key_text = small_font.render(str(index + 1), True, (12, 12, 16))
    screen.blit(key_text, key_text.get_rect(center=key_badge.center))

    title_font = get_font(23)
    desc_font = get_font(15)
    tiny_font = get_font(13)
    title = title_font.render(skill["name"], True, GOLD if hovered else WHITE)
    screen.blit(title, (rect.x + 92, rect.y + 20))

    current_skill_count = acquired_count.get(skill["name"], 0)
    base_desc, current_desc, next_desc = get_skill_detail_desc(skill["name"], stats, current_skill_count)
    if current_skill_count > 0:
        count_text = tiny_font.render(f"x{current_skill_count}", True, (255, 225, 150))
        screen.blit(count_text, (rect.x + 94, rect.y + 48))

    y = rect.y + 88
    for line in _fit_lines(desc_font, base_desc, rect.width - 40, 2):
        text = desc_font.render(line, True, (205, 213, 226))
        screen.blit(text, (rect.x + 20, y))
        y += 22

    info_rect = pygame.Rect(rect.x + 18, rect.bottom - 78, rect.width - 36, 58)
    pygame.draw.rect(screen, (16, 18, 27), info_rect, border_radius=7)
    pygame.draw.rect(screen, (55, 62, 80), info_rect, 1, border_radius=7)
    label = "下次" if hovered or current_skill_count == 0 else "当前"
    detail = next_desc if (hovered and next_desc) else current_desc
    label_text = tiny_font.render(label, True, (145, 158, 180))
    screen.blit(label_text, (info_rect.x + 12, info_rect.y + 8))
    for line in _fit_lines(tiny_font, str(detail), info_rect.width - 24, 2):
        text = tiny_font.render(line, True, (115, 245, 165) if label == "下次" else (245, 215, 145))
        screen.blit(text, (info_rect.x + 12, info_rect.y + 28))
        break


def draw_skill_selection(screen, big_font, small_font, skills, mouse_pos, acquired_skills=None, stats=None):
    sw, sh = screen.get_width(), screen.get_height()
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((5, 7, 13, 225))
    screen.blit(overlay, (0, 0))

    title = big_font.render("选择强化", True, WHITE)
    title_rect = title.get_rect(center=(sw // 2, 88))
    screen.blit(title, title_rect)
    sub = small_font.render("按 1 / 2 / 3 或点击卡片", True, (145, 158, 180))
    screen.blit(sub, sub.get_rect(center=(sw // 2, 132)))

    acquired_count = {}
    if acquired_skills:
        for name in acquired_skills:
            acquired_count[name] = acquired_count.get(name, 0) + 1

    card_rects = build_card_rects(len(skills), sw, sh)
    for i, skill in enumerate(skills):
        rect = card_rects[i]
        _draw_card(screen, rect, skill, i, rect.collidepoint(mouse_pos),
                   small_font, acquired_count, stats or {})
    return card_rects


def build_card_rects(count, sw, sh):
    card_w, card_h = 340, 230
    gap = 24
    total_w = count * card_w + max(0, count - 1) * gap
    start_x = (sw - total_w) // 2
    y = max(170, sh // 2 - card_h // 2 + 35)
    return [pygame.Rect(start_x + i * (card_w + gap), y, card_w, card_h)
            for i in range(count)]
