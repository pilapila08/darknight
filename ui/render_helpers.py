"""Shared rendering helpers for world sprites."""
import pygame


def draw_ground_shadow(screen, camera, rect, scale=1.0, alpha=90):
    """Draw a soft oval shadow under a world-space rect."""
    width = max(10, int(rect.width * 0.9 * scale))
    height = max(4, int(rect.height * 0.24 * scale))
    surf = pygame.Surface((width + 6, height + 6), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (0, 0, 0, alpha), (3, 3, width, height))
    pos = camera.apply(pygame.Rect(rect.centerx, rect.bottom, 0, 0))
    screen.blit(surf, (pos.x - surf.get_width() // 2, pos.y - surf.get_height() // 2))


def draw_shadowed_sprite(screen, camera, image, rect, shadow_scale=1.0, shadow_alpha=90):
    """Draw an image with a soft ground shadow."""
    draw_ground_shadow(screen, camera, rect, shadow_scale, shadow_alpha)
    screen.blit(image, camera.apply(rect))
