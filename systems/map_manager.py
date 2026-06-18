"""Map system: background colors, grid styles, and unique mechanics per map."""
import math
import random
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT, GRID_SIZE,
    BLACK, GRAY
)


MAP_CONFIGS = [
    {
        "index": 0,
        "name": "荒芜墓地",
        "name_en": "Bleak Graveyard",
        "bg_color": (15, 18, 12),
        "grid_color": (30, 40, 25),
        "accent_color": (80, 95, 55),
        "mechanic": None,
    },
    {
        "index": 1,
        "name": "腐化沼泽",
        "name_en": "Corrupted Swamp",
        "bg_color": (20, 30, 10),
        "grid_color": (40, 50, 20),
        "accent_color": (60, 130, 45),
        "mechanic": "poison_pools",
        "mechanic_interval": 5.0,
        "poison_pool_radius": 40,
        "poison_pool_duration": 10.0,
        "poison_pool_damage": 1,
    },
    {
        "index": 2,
        "name": "暗影庭院",
        "name_en": "Shadow Court",
        "bg_color": (15, 5, 25),
        "grid_color": (35, 20, 45),
        "accent_color": (95, 55, 130),
        "mechanic": "darkness_waves",
        "darkness_interval": 30.0,
        "darkness_duration": 3.0,
        "darkness_vision_radius": 150,
    },
    {
        "index": 3,
        "name": "钢铁废墟",
        "name_en": "Iron Ruins",
        "bg_color": (25, 18, 12),
        "grid_color": (50, 45, 40),
        "accent_color": (110, 105, 95),
        "mechanic": "debris_fields",
        "debris_count": 10,
        "debris_size": 32,
        "debris_color": (80, 75, 70),
    },
    {
        "index": 4,
        "name": "虚空裂缝",
        "name_en": "Void Rift",
        "bg_color": (8, 0, 15),
        "grid_color": (25, 0, 40),
        "accent_color": (120, 45, 155),
        "mechanic": "gravity_anomalies",
        "anomaly_count": 4,
        "anomaly_radius": 100,
        "anomaly_pull_strength": 50,
        "anomaly_damage": 1,
    },
]


class MapManager:
    """Manages the current map, background, grid, and mechanics."""

    def __init__(self):
        self.current_map_index = 0
        self.map_data = MAP_CONFIGS[0]
        self.transition_active = False
        self.transition_timer = 0.0
        self.transition_text = ""
        self.poison_pools = []
        self.pool_timer = 0.0
        self.darkness_timer = 0.0
        self.darkness_active = False
        self.debris_rects = []
        self.debris_generated = False
        self.anomalies = []
        self.scenery = []
        self._vignette = None
        self._generate_scenery()

    def switch_to_map(self, map_index):
        """Transition to a new map."""
        if map_index >= len(MAP_CONFIGS):
            return
        self.current_map_index = map_index
        self.map_data = MAP_CONFIGS[map_index]
        self.transition_active = True
        self.transition_timer = 2.0
        self.transition_text = "进入 " + self.map_data["name"]
        self._clear_mechanics()
        self._init_map_mechanics()

    def _clear_mechanics(self):
        self.poison_pools = []
        self.pool_timer = 0.0
        self.darkness_timer = 0.0
        self.darkness_active = False
        self.debris_rects = []
        self.debris_generated = False
        self.anomalies = []
        self.scenery = []

    def _init_map_mechanics(self):
        mechanic = self.map_data.get("mechanic")
        self._generate_scenery()
        if mechanic == "debris_fields":
            self._generate_debris()
        elif mechanic == "gravity_anomalies":
            self._generate_anomalies()

    def _generate_scenery(self):
        rng = random.Random(9000 + self.current_map_index)
        self.scenery = []
        for _ in range(220):
            x = rng.randint(0, MAP_WIDTH)
            y = rng.randint(0, MAP_HEIGHT)
            kind_roll = rng.random()
            if kind_roll < 0.58:
                kind = "speck"
                size = rng.randint(2, 5)
            elif kind_roll < 0.82:
                kind = "tuft"
                size = rng.randint(5, 11)
            else:
                kind = "stone"
                size = rng.randint(8, 18)
            self.scenery.append({
                "x": x,
                "y": y,
                "kind": kind,
                "size": size,
                "phase": rng.random() * math.pi * 2,
            })

    def _generate_debris(self):
        count = self.map_data["debris_count"]
        size = self.map_data["debris_size"]
        self.debris_rects = []
        for _ in range(count * 3):
            x = random.randint(100, MAP_WIDTH - 100)
            y = random.randint(100, MAP_HEIGHT - 100)
            if abs(x - MAP_WIDTH // 2) > 250 or abs(y - MAP_HEIGHT // 2) > 250:
                self.debris_rects.append(pygame.Rect(x, y, size, size))
            if len(self.debris_rects) >= count:
                break

    def _generate_anomalies(self):
        count = self.map_data["anomaly_count"]
        self.anomalies = []
        for _ in range(count):
            x = random.randint(300, MAP_WIDTH - 300)
            y = random.randint(300, MAP_HEIGHT - 300)
            self.anomalies.append({
                "x": x, "y": y, "radius": self.map_data["anomaly_radius"],
                "pulse": random.uniform(0, math.pi * 2),
            })

    def update(self, dt, player_rect, enemies):
        """Update map mechanic. Returns list of damage/effect events."""
        effects = []

        if self.transition_active:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.transition_active = False

        mechanic = self.map_data.get("mechanic")
        if mechanic == "poison_pools":
            effects.extend(self._update_poison_pools(dt, player_rect))
        elif mechanic == "darkness_waves":
            self._update_darkness(dt)
        elif mechanic == "gravity_anomalies":
            self._update_anomalies(dt, enemies)

        return effects

    def _update_poison_pools(self, dt, player_rect):
        self.pool_timer += dt
        effects = []
        if self.pool_timer >= self.map_data["mechanic_interval"]:
            self.pool_timer = 0
            x = player_rect.centerx + random.randint(-250, 250)
            y = player_rect.centery + random.randint(-250, 250)
            x = max(50, min(MAP_WIDTH - 50, x))
            y = max(50, min(MAP_HEIGHT - 50, y))
            self.poison_pools.append({
                "x": x, "y": y,
                "radius": self.map_data["poison_pool_radius"],
                "duration": self.map_data["poison_pool_duration"],
                "elapsed": 0.0,
                "damage": self.map_data["poison_pool_damage"],
                "tick_timer": 0.0,
            })

        for pool in list(self.poison_pools):
            pool["elapsed"] += dt
            pool["tick_timer"] += dt
            if pool["tick_timer"] >= 0.5:
                pool["tick_timer"] = 0
                dist = math.hypot(player_rect.centerx - pool["x"],
                                  player_rect.centery - pool["y"])
                if dist < pool["radius"]:
                    effects.append({"type": "player_damage", "amount": pool["damage"]})
            if pool["elapsed"] >= pool["duration"]:
                self.poison_pools.remove(pool)
        return effects

    def _update_darkness(self, dt):
        if self.darkness_active:
            self.darkness_timer -= dt
            if self.darkness_timer <= 0:
                self.darkness_active = False
                self.darkness_timer = 0
        else:
            self.darkness_timer += dt
            if self.darkness_timer >= self.map_data["darkness_interval"]:
                self.darkness_active = True
                self.darkness_timer = self.map_data["darkness_duration"]

    def _update_anomalies(self, dt, enemies):
        for anomaly in self.anomalies:
            anomaly["pulse"] += dt * 2
            for enemy in list(enemies):
                if hasattr(enemy, 'boss_index'):
                    continue
                dx = anomaly["x"] - enemy.rect.centerx
                dy = anomaly["y"] - enemy.rect.centery
                dist = math.hypot(dx, dy)
                if dist < anomaly["radius"] and dist > 5:
                    pull = self.map_data["anomaly_pull_strength"] * (1 - dist / anomaly["radius"])
                    enemy.rect.x += (dx / dist) * pull * dt
                    enemy.rect.y += (dy / dist) * pull * dt
                    if dist < 25:
                        enemy.take_damage(self.map_data["anomaly_damage"] * dt * 2)

    def check_debris_collision(self, rect):
        """Check if a rect collides with any debris."""
        if self.map_data.get("mechanic") != "debris_fields":
            return False
        return any(d.colliderect(rect) for d in self.debris_rects)

    def check_debris_collision_point(self, cx, cy, radius=16):
        """Check if a circle collides with any debris."""
        if self.map_data.get("mechanic") != "debris_fields":
            return False
        test_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        return any(d.colliderect(test_rect) for d in self.debris_rects)

    def get_valid_spawn_pos(self, cx, cy, radius=400):
        """Get a valid spawn position not on debris."""
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            dist = random.randint(50, radius)
            x = cx + int(math.cos(angle) * dist)
            y = cy + int(math.sin(angle) * dist)
            x = max(50, min(MAP_WIDTH - 50, x))
            y = max(50, min(MAP_HEIGHT - 50, y))
            if not self.check_debris_collision_point(x, y):
                return x, y
        return cx + random.randint(-200, 200), cy + random.randint(-200, 200)

    def draw_background(self, screen, camera):
        """Draw the map background and grid."""
        screen.fill(self.map_data["bg_color"])

        gs = GRID_SIZE
        start_x = int(camera.offset.x % gs)
        start_y = int(camera.offset.y % gs)
        grid_color = self.map_data["grid_color"]
        minor_color = tuple(max(0, c - 8) for c in grid_color)

        for x in range(-start_x % (gs // 2), SCREEN_WIDTH, gs // 2):
            pygame.draw.line(screen, minor_color, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(-start_y % (gs // 2), SCREEN_HEIGHT, gs // 2):
            pygame.draw.line(screen, minor_color, (0, y), (SCREEN_WIDTH, y))
        for x in range(-start_x, SCREEN_WIDTH, gs):
            pygame.draw.line(screen, grid_color, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(-start_y, SCREEN_HEIGHT, gs):
            pygame.draw.line(screen, grid_color, (0, y), (SCREEN_WIDTH, y))

        self._draw_scenery(screen, camera)
        self._draw_mechanics(screen, camera)
        self._draw_vignette(screen)

        if self.transition_active:
            alpha = int(255 * min(1.0, self.transition_timer))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, min(200, alpha)))
            screen.blit(overlay, (0, 0))

    def _draw_scenery(self, screen, camera):
        accent = self.map_data["accent_color"]
        dim = tuple(max(0, c - 45) for c in accent)
        glow = tuple(min(255, c + 35) for c in accent)

        for item in self.scenery:
            rect = pygame.Rect(item["x"], item["y"], item["size"], item["size"])
            pos = camera.apply(rect)
            if not (-30 <= pos.x <= SCREEN_WIDTH + 30 and -30 <= pos.y <= SCREEN_HEIGHT + 30):
                continue

            size = item["size"]
            if item["kind"] == "speck":
                pygame.draw.circle(screen, dim, pos.center, max(1, size // 2))
            elif item["kind"] == "tuft":
                base_x, base_y = pos.centerx, pos.bottom
                pygame.draw.line(screen, accent, (base_x, base_y),
                                 (base_x - size // 2, base_y - size), 2)
                pygame.draw.line(screen, dim, (base_x, base_y),
                                 (base_x + size // 2, base_y - size + 2), 2)
            else:
                pygame.draw.ellipse(screen, dim, pos)
                pygame.draw.arc(screen, glow, pos, math.pi, math.pi * 1.65, 2)

    def _draw_vignette(self, screen):
        if self._vignette is None:
            self._vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            edge = 160
            for i in range(edge):
                alpha = int(70 * (1 - i / edge) ** 2)
                pygame.draw.line(self._vignette, (0, 0, 0, alpha), (0, i), (SCREEN_WIDTH, i))
                pygame.draw.line(self._vignette, (0, 0, 0, alpha),
                                 (0, SCREEN_HEIGHT - 1 - i), (SCREEN_WIDTH, SCREEN_HEIGHT - 1 - i))
                pygame.draw.line(self._vignette, (0, 0, 0, alpha), (i, 0), (i, SCREEN_HEIGHT))
                pygame.draw.line(self._vignette, (0, 0, 0, alpha),
                                 (SCREEN_WIDTH - 1 - i, 0), (SCREEN_WIDTH - 1 - i, SCREEN_HEIGHT))
        screen.blit(self._vignette, (0, 0))

    def _draw_mechanics(self, screen, camera):
        mechanic = self.map_data.get("mechanic")

        if mechanic == "poison_pools":
            for pool in self.poison_pools:
                alpha = int(100 * max(0, 1 - pool["elapsed"] / pool["duration"]))
                size = pool["radius"] * 2
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(surf, (60, 180, 40, alpha),
                                   (pool["radius"], pool["radius"]), pool["radius"])
                pos = camera.apply(pygame.Rect(pool["x"], pool["y"], 0, 0))
                screen.blit(surf, (pos.x - pool["radius"], pos.y - pool["radius"]))

        elif mechanic == "darkness_waves" and self.darkness_active:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            player_screen = camera.apply(pygame.Rect(0, 0, 0, 0))
            cx = player_screen.x + SCREEN_WIDTH // 2
            cy = player_screen.y + SCREEN_HEIGHT // 2
            r = self.map_data["darkness_vision_radius"]
            pygame.draw.circle(overlay, (0, 0, 0, 0), (cx, cy), r)
            screen.blit(overlay, (0, 0))

        elif mechanic == "debris_fields":
            for rect in self.debris_rects:
                screen_rect = camera.apply(rect)
                if (-50 <= screen_rect.x <= SCREEN_WIDTH + 50 and
                        -50 <= screen_rect.y <= SCREEN_HEIGHT + 50):
                    pygame.draw.rect(screen, self.map_data["debris_color"], screen_rect)
                    pygame.draw.rect(screen, (100, 95, 90), screen_rect, 2)

        elif mechanic == "gravity_anomalies":
            for anomaly in self.anomalies:
                pos = camera.apply(pygame.Rect(anomaly["x"], anomaly["y"], 0, 0))
                r = anomaly["radius"]
                alpha = int(20 + 10 * math.sin(anomaly["pulse"]))
                size = r * 2
                if (-size <= pos.x <= SCREEN_WIDTH + size and
                        -size <= pos.y <= SCREEN_HEIGHT + size):
                    surf = pygame.Surface((size, size), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (180, 0, 200, alpha),
                                       (r, r), r)
                    pygame.draw.circle(surf, (200, 50, 220, alpha + 20),
                                       (r, r), r, 2)
                    screen.blit(surf, (pos.x - r, pos.y - r))
