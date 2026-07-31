"""Boss system: Boss class hierarchy, projectiles, and area effects."""
import math
import random
import pygame
from settings import (
    MAP_WIDTH, MAP_HEIGHT,
    CORPSE_KING_HP, CORPSE_KING_DAMAGE, CORPSE_KING_SIZE, CORPSE_KING_COLOR,
    CORPSE_KING_SPEED, CORPSE_KING_ATTACK_INTERVAL, CORPSE_KING_POISON_DURATION,
    CORPSE_KING_POISON_DAMAGE, CORPSE_KING_MINION_COUNT,
    SHADOW_MAGE_HP, SHADOW_MAGE_DAMAGE, SHADOW_MAGE_SIZE, SHADOW_MAGE_COLOR,
    SHADOW_MAGE_SPEED, SHADOW_MAGE_ATTACK_INTERVAL, SHADOW_MAGE_BOLT_COUNT,
    SHADOW_MAGE_BOLT_DAMAGE, SHADOW_MAGE_TELEPORT_INTERVAL,
    SHADOW_MAGE_SHADOW_HP, SHADOW_MAGE_SHADOW_DAMAGE,
    IRON_COLOSSUS_HP, IRON_COLOSSUS_DAMAGE, IRON_COLOSSUS_SIZE, IRON_COLOSSUS_COLOR,
    IRON_COLOSSUS_SPEED, IRON_COLOSSUS_ATTACK_INTERVAL, IRON_COLOSSUS_POUND_DAMAGE,
    IRON_COLOSSUS_ARMOR_REDUCTION, IRON_COLOSSUS_ARMOR_DURATION,
    IRON_COLOSSUS_FIST_SPEED, IRON_COLOSSUS_FIST_DAMAGE, IRON_COLOSSUS_FIST_RADIUS,
    VOID_LORD_HP, VOID_LORD_DAMAGE, VOID_LORD_SIZE, VOID_LORD_COLOR,
    VOID_LORD_SPEED, VOID_LORD_ATTACK_INTERVAL, VOID_LORD_VOID_RIFT_DAMAGE,
    VOID_LORD_VOID_RIFT_RADIUS, VOID_LORD_VOID_RIFT_DURATION,
    VOID_LORD_GRAVITY_STRENGTH, VOID_LORD_BARRAGE_COUNT, VOID_LORD_BARRAGE_DAMAGE,
    VOID_LORD_ENRAGE_THRESHOLD, VOID_LORD_VOIDLING_HP, VOID_LORD_VOIDLING_DAMAGE,
    BOSS_1_TIME, BOSS_2_TIME, BOSS_3_TIME, BOSS_4_TIME,
    ENEMY_BULLET_SPEED,
)
from .enemy import Enemy
from entities.walk_anim import compute_walk_frame, resolve_params
from ui.render_helpers import draw_shadowed_sprite_offset


class BossProjectile(pygame.sprite.Sprite):
    """Boss-specific projectile with configurable behavior."""

    def __init__(self, x, y, target_x, target_y, speed, damage, color, radius=6, lifetime=5.0):
        super().__init__()
        self.radius = radius
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        pygame.draw.circle(self.image, (255, 255, 255, 100), (radius, radius), radius // 2)
        self.rect = self.image.get_rect(center=(x, y))
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        self.vx = (dx / dist) * speed if dist > 0 else speed
        self.vy = (dy / dist) * speed if dist > 0 else 0
        self.damage = damage
        self.lifetime = lifetime
        self.elapsed = 0.0
        self.homing = False
        self.return_to_sender = False
        self.sender_pos = (x, y)

    def update(self, dt):
        self.elapsed += dt
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
        if self.elapsed >= self.lifetime:
            self.kill()


class BoomerangFist(BossProjectile):
    """Iron Colossus rocket fist that returns to sender."""

    def __init__(self, x, y, target_x, target_y, sender_rect, damage, color, radius=12):
        super().__init__(x, y, target_x, target_y, IRON_COLOSSUS_FIST_SPEED, damage, color, radius, lifetime=10.0)
        self.sender_rect = sender_rect
        self.outbound = True

    def update(self, dt):
        self.elapsed += dt
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt

        if self.outbound:
            dist = math.hypot(self.rect.centerx - self.sender_rect.centerx,
                              self.rect.centery - self.sender_rect.centery)
            if dist > 600 or self.elapsed > 2.5:
                self.outbound = False
        else:
            dx = self.sender_rect.centerx - self.rect.centerx
            dy = self.sender_rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 20:
                self.kill()
            elif dist > 0:
                speed = IRON_COLOSSUS_FIST_SPEED * 1.2
                self.vx = (dx / dist) * speed
                self.vy = (dy / dist) * speed

        if self.elapsed >= self.lifetime:
            self.kill()


class AreaEffect:
    """Ground-based persistent effect (poison pool, void rift, etc.)."""

    def __init__(self, x, y, radius, duration, damage, color, tick_interval=0.5):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.damage = damage
        self.color = color
        self.tick_interval = tick_interval
        self.elapsed = 0.0
        self.tick_timer = 0.0
        self.expired = False

    def update(self, dt):
        self.elapsed += dt
        self.tick_timer += dt
        if self.elapsed >= self.duration:
            self.expired = True

    def should_tick(self):
        if self.tick_timer >= self.tick_interval:
            self.tick_timer = 0.0
            return True
        return False

    def contains_point(self, px, py):
        return math.hypot(px - self.x, py - self.y) < self.radius

    def draw(self, screen, camera):
        alpha = int(100 * max(0, 1 - self.elapsed / self.duration))
        size = self.radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (self.radius, self.radius), self.radius)
        pygame.draw.circle(surf, (*self.color[:3], min(255, alpha + 40)),
                           (self.radius, self.radius), self.radius, 2)
        world_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 0, 0)
        screen_pos = camera.apply(world_rect)
        screen.blit(surf, (screen_pos.x, screen_pos.y))


class Boss(Enemy):
    """Base boss class with configurable attacks and phases."""

    def __init__(self, x, y, config):
        super().__init__(x, y, hp=config["hp"], speed=config["speed"],
                         size=config["size"], color=config["color"],
                         sprite_name=config.get("sprite_name"), contact_damage=config["damage"],
                         is_elite=False)
        self.config = config
        self.boss_index = config["index"]
        self._base_hp = config["hp"]
        self.attack_timer = 0.0
        self.phase_timer = 0.0

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)
        self.phase_timer += dt
        self.attack_timer += dt
        attacks = self._do_attacks(dt, player_rect)
        move_attacks = self._do_movement(dt, player_rect)
        self._anim.update(dt)
        if self.flash_timer > 0:
            self.image = self._flash_frames[self._anim.current]
        else:
            self.image = self._normal_frames[self._anim.current]
        if move_attacks:
            if attacks:
                attacks.extend(move_attacks)
            else:
                attacks = move_attacks
        return attacks

    def draw(self, screen, camera):
        # L1 程序动画：低频大振幅（沉重感）+ 脚底阴影联动
        t = pygame.time.get_ticks() / 1000.0
        params = resolve_params("boss")
        frame = compute_walk_frame(self.image, t, id(self), self.vx, params)
        draw_shadowed_sprite_offset(screen, camera, frame.surface, self.rect,
                                    dy=frame.bob,
                                    shadow_scale=1.35 * frame.shadow_scale,
                                    shadow_alpha=125)

    def _do_attacks(self, dt, player_rect):
        return []

    def _do_movement(self, dt, player_rect):
        self._move_toward(player_rect.centerx, player_rect.centery, dt)

    def draw_hp_bar_bg(self, screen, font, camera):
        """Draw HP bar above boss in world space."""
        bar_w = self.rect.width + 20
        bar_h = 8
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.top - 14
        screen_pos = camera.apply(pygame.Rect(bar_x, bar_y, 0, 0))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (40, 40, 40), (screen_pos.x, screen_pos.y, bar_w, bar_h))
        if hp_ratio > 0:
            color = (255, 50, 50) if hp_ratio < 0.3 else (255, 200, 50)
            pygame.draw.rect(screen, color, (screen_pos.x, screen_pos.y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(screen, (255, 255, 255), (screen_pos.x, screen_pos.y, bar_w, bar_h), 1)


class CorpseKing(Boss):
    """Boss 1 - Slow brute that charges, leaves poison, and summons minions."""

    def __init__(self, x, y):
        config = {
            "index": 0, "name": "尸王", "hp": CORPSE_KING_HP, "damage": CORPSE_KING_DAMAGE,
            "size": CORPSE_KING_SIZE, "color": CORPSE_KING_COLOR, "speed": CORPSE_KING_SPEED,
            "attack_interval": CORPSE_KING_ATTACK_INTERVAL, "spawn_time": BOSS_1_TIME,
            "sprite_name": "boss_corpse_king",
        }
        super().__init__(x, y, config)
        self.charging = False
        self.charge_target = (0, 0)
        self.charge_speed = CORPSE_KING_SPEED * 3
        self.summon_timer = 0.0
        self.summon_interval = 5.0

    def _do_movement(self, dt, player_rect):
        if self.charging:
            dx = self.charge_target[0] - self.rect.centerx
            dy = self.charge_target[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 20:
                self.charging = False
                self.speed = CORPSE_KING_SPEED
                return [{"type": "aoe", "x": self.rect.centerx, "y": self.rect.centery,
                         "radius": 45, "duration": CORPSE_KING_POISON_DURATION,
                         "damage": CORPSE_KING_POISON_DAMAGE, "color": (60, 180, 40)}]
            self.rect.x += (dx / dist) * self.charge_speed * dt
            self.rect.y += (dy / dist) * self.charge_speed * dt
        else:
            self._move_toward(player_rect.centerx, player_rect.centery, dt)
        return []

    def _do_attacks(self, dt, player_rect):
        attacks = []
        self.summon_timer += dt

        if self.attack_timer >= self.config["attack_interval"] and not self.charging:
            self.attack_timer = 0.0
            if random.random() < 0.6:
                self.charging = True
                self.speed = self.charge_speed
                self.charge_target = (player_rect.centerx, player_rect.centery)
            else:
                attacks.append({"type": "summon", "enemy_type": "basic", "count": CORPSE_KING_MINION_COUNT,
                                "x": self.rect.centerx, "y": self.rect.centery, "tier": 0})

        if self.summon_timer >= self.summon_interval and not self.charging:
            self.summon_timer = 0.0
            attacks.append({"type": "summon", "enemy_type": "basic", "count": CORPSE_KING_MINION_COUNT,
                            "x": self.rect.centerx, "y": self.rect.centery, "tier": 0})

        return attacks


class ShadowMage(Boss):
    """Boss 2 - Teleports and fires shadow bolts in spreads."""

    def __init__(self, x, y):
        config = {
            "index": 1, "name": "暗影巫师", "hp": SHADOW_MAGE_HP, "damage": SHADOW_MAGE_DAMAGE,
            "size": SHADOW_MAGE_SIZE, "color": SHADOW_MAGE_COLOR, "speed": SHADOW_MAGE_SPEED,
            "attack_interval": SHADOW_MAGE_ATTACK_INTERVAL, "spawn_time": BOSS_2_TIME,
            "sprite_name": "boss_shadow_mage",
        }
        super().__init__(x, y, config)
        self.teleport_timer = 0.0
        self.summon_timer = 0.0
        self.summon_interval = 6.0

    def _do_movement(self, dt, player_rect):
        self.teleport_timer += dt
        if self.teleport_timer >= SHADOW_MAGE_TELEPORT_INTERVAL:
            self.teleport_timer = 0.0
            angle = random.uniform(0, math.pi * 2)
            dist = random.randint(200, 400)
            self.rect.centerx = int(player_rect.centerx + math.cos(angle) * dist)
            self.rect.centery = int(player_rect.centery + math.sin(angle) * dist)
            self.rect.centerx = max(50, min(MAP_WIDTH - 50, self.rect.centerx))
            self.rect.centery = max(50, min(MAP_HEIGHT - 50, self.rect.centery))
        else:
            self._move_toward(player_rect.centerx, player_rect.centery, dt)

    def _do_attacks(self, dt, player_rect):
        attacks = []
        self.summon_timer += dt

        if self.attack_timer >= self.config["attack_interval"]:
            self.attack_timer = 0.0
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            base_angle = math.atan2(dy, dx)
            spread = 0.8
            for i in range(SHADOW_MAGE_BOLT_COUNT):
                a = base_angle + (i - (SHADOW_MAGE_BOLT_COUNT - 1) / 2) * spread / SHADOW_MAGE_BOLT_COUNT
                tx = self.rect.centerx + math.cos(a) * 400
                ty = self.rect.centery + math.sin(a) * 400
                attacks.append({"type": "projectile", "x": self.rect.centerx, "y": self.rect.centery,
                                "tx": tx, "ty": ty, "speed": 300, "damage": SHADOW_MAGE_BOLT_DAMAGE,
                                "color": (150, 50, 220), "radius": 5})

        if self.summon_timer >= self.summon_interval:
            self.summon_timer = 0.0
            attacks.append({"type": "summon", "enemy_type": "shadow", "count": 2,
                            "x": self.rect.centerx, "y": self.rect.centery, "tier": 0})

        return attacks


class IronColossus(Boss):
    """Boss 3 - Heavy armored boss with shockwaves, armor, and homing fist."""

    def __init__(self, x, y):
        config = {
            "index": 2, "name": "钢铁巨像", "hp": IRON_COLOSSUS_HP, "damage": IRON_COLOSSUS_DAMAGE,
            "size": IRON_COLOSSUS_SIZE, "color": IRON_COLOSSUS_COLOR, "speed": IRON_COLOSSUS_SPEED,
            "attack_interval": IRON_COLOSSUS_ATTACK_INTERVAL, "spawn_time": BOSS_3_TIME,
            "sprite_name": "boss_iron_colossus",
        }
        super().__init__(x, y, config)
        self.armor_active = False
        self.armor_timer = 0.0
        self.fist_out = False

    def take_damage(self, damage):
        if self.armor_active:
            damage *= IRON_COLOSSUS_ARMOR_REDUCTION
        return super().take_damage(damage)

    def _do_movement(self, dt, player_rect):
        self._move_toward(player_rect.centerx, player_rect.centery, dt)
        if self.armor_active:
            self.armor_timer -= dt
            if self.armor_timer <= 0:
                self.armor_active = False

    def _do_attacks(self, dt, player_rect):
        attacks = []
        if self.attack_timer >= self.config["attack_interval"]:
            self.attack_timer = 0.0
            r = random.random()
            if r < 0.35:
                attacks.append({"type": "shockwave", "x": self.rect.centerx, "y": self.rect.centery,
                                "damage": IRON_COLOSSUS_POUND_DAMAGE, "speed": 300, "duration": 0.8})
            elif r < 0.65:
                self.armor_active = True
                self.armor_timer = IRON_COLOSSUS_ARMOR_DURATION
            else:
                if not self.fist_out:
                    attacks.append({"type": "boomerang", "x": self.rect.centerx, "y": self.rect.centery,
                                    "tx": player_rect.centerx, "ty": player_rect.centery,
                                    "sender_rect": self.rect.copy(), "damage": IRON_COLOSSUS_FIST_DAMAGE,
                                    "color": IRON_COLOSSUS_COLOR, "radius": IRON_COLOSSUS_FIST_RADIUS})
        return attacks

    def draw(self, screen, camera):
        super().draw(screen, camera)
        if self.armor_active:
            pos = camera.apply(self.rect)
            pygame.draw.rect(screen, (200, 220, 255), pos, 3)


class VoidLord(Boss):
    """Boss 4 - Final boss with rifts, gravity wells, barrage, and enrage."""

    def __init__(self, x, y):
        config = {
            "index": 3, "name": "虚空之主", "hp": VOID_LORD_HP, "damage": VOID_LORD_DAMAGE,
            "size": VOID_LORD_SIZE, "color": VOID_LORD_COLOR, "speed": VOID_LORD_SPEED,
            "attack_interval": VOID_LORD_ATTACK_INTERVAL, "spawn_time": BOSS_4_TIME,
            "sprite_name": "boss_void_lord",
        }
        super().__init__(x, y, config)
        self.enraged = False
        self.voidling_timer = 0.0
        self.gravity_active = False
        self.gravity_timer = 0.0

    def _do_movement(self, dt, player_rect):
        self._move_toward(player_rect.centerx, player_rect.centery, dt)
        if self.gravity_active:
            self.gravity_timer -= dt
            if self.gravity_timer <= 0:
                self.gravity_active = False

    def _do_attacks(self, dt, player_rect):
        attacks = []
        hp_ratio = self.hp / self.max_hp

        if hp_ratio < VOID_LORD_ENRAGE_THRESHOLD and not self.enraged:
            self.enraged = True
            self.attack_interval *= 0.7

        if self.enraged:
            self.voidling_timer += dt
            if self.voidling_timer >= 3.0:
                self.voidling_timer = 0.0
                attacks.append({"type": "summon", "enemy_type": "voidling", "count": 1,
                                "x": self.rect.centerx, "y": self.rect.centery, "tier": 0})

        if self.attack_timer >= self.config["attack_interval"]:
            self.attack_timer = 0.0
            r = random.random()
            if r < 0.4:
                for _ in range(3):
                    rx = player_rect.centerx + random.randint(-200, 200)
                    ry = player_rect.centery + random.randint(-200, 200)
                    rx = max(50, min(MAP_WIDTH - 50, rx))
                    ry = max(50, min(MAP_HEIGHT - 50, ry))
                    attacks.append({"type": "aoe", "x": rx, "y": ry,
                                    "radius": VOID_LORD_VOID_RIFT_RADIUS,
                                    "duration": VOID_LORD_VOID_RIFT_DURATION,
                                    "damage": VOID_LORD_VOID_RIFT_DAMAGE,
                                    "color": (180, 0, 200)})
            elif r < 0.7:
                self.gravity_active = True
                self.gravity_timer = 3.0
                attacks.append({"type": "gravity", "x": self.rect.centerx, "y": self.rect.centery,
                                "radius": 300, "strength": VOID_LORD_GRAVITY_STRENGTH, "duration": 3.0})
            else:
                for i in range(VOID_LORD_BARRAGE_COUNT):
                    angle = (math.pi * 2 / VOID_LORD_BARRAGE_COUNT) * i
                    tx = self.rect.centerx + math.cos(angle) * 300
                    ty = self.rect.centery + math.sin(angle) * 300
                    attacks.append({"type": "projectile", "x": self.rect.centerx, "y": self.rect.centery,
                                    "tx": tx, "ty": ty, "speed": 180, "damage": VOID_LORD_BARRAGE_DAMAGE,
                                    "color": (200, 100, 255), "radius": 5})

        return attacks

    def draw(self, screen, camera):
        super().draw(screen, camera)
        if self.gravity_active:
            pos = camera.apply(self.rect)
            cx, cy = pos.centerx, pos.centery
            pygame.draw.circle(screen, (180, 0, 200, 60), (cx, cy), 50, 3)


BOSS_CLASSES = [CorpseKing, ShadowMage, IronColossus, VoidLord]
BOSS_CONFIGS = [
    {
        "index": 0, "name": "尸王", "hp": CORPSE_KING_HP, "damage": CORPSE_KING_DAMAGE,
        "size": CORPSE_KING_SIZE, "color": CORPSE_KING_COLOR, "speed": CORPSE_KING_SPEED,
        "spawn_time": BOSS_1_TIME, "cls": CorpseKing, "sprite_name": "boss_corpse_king",
    },
    {
        "index": 1, "name": "暗影巫师", "hp": SHADOW_MAGE_HP, "damage": SHADOW_MAGE_DAMAGE,
        "size": SHADOW_MAGE_SIZE, "color": SHADOW_MAGE_COLOR, "speed": SHADOW_MAGE_SPEED,
        "spawn_time": BOSS_2_TIME, "cls": ShadowMage, "sprite_name": "boss_shadow_mage",
    },
    {
        "index": 2, "name": "钢铁巨像", "hp": IRON_COLOSSUS_HP, "damage": IRON_COLOSSUS_DAMAGE,
        "size": IRON_COLOSSUS_SIZE, "color": IRON_COLOSSUS_COLOR, "speed": IRON_COLOSSUS_SPEED,
        "spawn_time": BOSS_3_TIME, "cls": IronColossus, "sprite_name": "boss_iron_colossus",
    },
    {
        "index": 3, "name": "虚空之主", "hp": VOID_LORD_HP, "damage": VOID_LORD_DAMAGE,
        "size": VOID_LORD_SIZE, "color": VOID_LORD_COLOR, "speed": VOID_LORD_SPEED,
        "spawn_time": BOSS_4_TIME, "cls": VoidLord, "sprite_name": "boss_void_lord",
    },
]
