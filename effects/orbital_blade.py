import math
import pygame
from settings import BLADE_SIZE, BLADE_ORBIT_RADIUS, BLADE_ORBIT_SPEED, BLADE_COLOR


class OrbitalBladeManager:
    def __init__(self):
        self.blades = []  # list of angle offsets

    def set_count(self, count):
        if len(self.blades) == count:
            return
        # 重新均匀分配所有刀刃
        self.blades = [i * (2 * math.pi / count) for i in range(count)]

    def update(self, dt):
        for i in range(len(self.blades)):
            self.blades[i] = (self.blades[i] + BLADE_ORBIT_SPEED * dt) % (2 * math.pi)

    def get_positions(self, player_rect):
        positions = []
        for angle in self.blades:
            x = player_rect.centerx + math.cos(angle) * BLADE_ORBIT_RADIUS
            y = player_rect.centery + math.sin(angle) * BLADE_ORBIT_RADIUS
            positions.append((x, y, angle))
        return positions

    def check_damage(self, player_rect, enemies, dt, stats):
        """Returns list of (enemy, damage_dealt) for damage numbers."""
        # 使用stats中的刀刃伤害，如果没有则使用默认值
        blade_damage = stats.get("blade_damage", 10)
        total_dps = blade_damage * len(self.blades)
        results = []
        for enemy in enemies:
            for x, y, _ in self.get_positions(player_rect):
                dist = math.hypot(enemy.rect.centerx - x, enemy.rect.centery - y)
                if dist < (BLADE_SIZE + enemy._size) / 2:
                    dmg = total_dps * dt / len(self.blades) if len(self.blades) > 0 else 0
                    dead = enemy.take_damage(dmg)
                    results.append((enemy, dmg, dead))
                    break  # one blade hit per enemy per frame
        return results

    def draw(self, screen, camera, player_rect):
        for x, y, angle in self.get_positions(player_rect):
            pos = camera.apply(pygame.Rect(x, y, 0, 0))
            surf = pygame.Surface((BLADE_SIZE, BLADE_SIZE), pygame.SRCALPHA)
            # Draw a small diagonal rectangle (blade shape)
            pts = [(BLADE_SIZE // 2, 0), (BLADE_SIZE, BLADE_SIZE // 2),
                   (BLADE_SIZE // 2, BLADE_SIZE), (0, BLADE_SIZE // 2)]
            pygame.draw.polygon(surf, BLADE_COLOR, pts)
            # Rotate based on orbit angle for visual spin
            rot_surf = pygame.transform.rotate(surf, math.degrees(-angle))
            r = rot_surf.get_rect(center=(pos.x, pos.y))
            screen.blit(rot_surf, r)
