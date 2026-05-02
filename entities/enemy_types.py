import math
import pygame
from entities.enemy import Enemy
from settings import (CHARGER_SPEED, CHARGER_HP, CHARGER_DASH_SPEED,
                      CHARGER_DASH_DURATION, CHARGER_DASH_COOLDOWN,
                      CHARGER_COLOR,
                      RANGER_SPEED, RANGER_HP, RANGER_RANGE,
                      RANGER_FIRE_INTERVAL, RANGER_COLOR,
                      EXPLODER_SPEED, EXPLODER_HP, EXPLODER_COLOR)


class Charger(Enemy):
    def __init__(self, x, y, hp=None, damage=None):
        hp = hp if hp is not None else CHARGER_HP
        damage = damage if damage is not None else 1
        super().__init__(x, y, hp=hp, speed=CHARGER_SPEED, color=CHARGER_COLOR, sprite_name="charger")
        self.contact_damage = damage
        self._base_speed = CHARGER_SPEED
        self._dash_cooldown = CHARGER_DASH_COOLDOWN
        self._dash_duration = 0.0
        self._dash_target = (0, 0)
        self._is_dashing = False

    def _begin_dash(self, player_rect):
        self._is_dashing = True
        self._dash_duration = CHARGER_DASH_DURATION
        self._dash_target = (player_rect.centerx, player_rect.centery)
        self.speed = CHARGER_DASH_SPEED
        self.contact_damage = self.contact_damage + 1

    def _end_dash(self):
        self._is_dashing = False
        self.speed = self._base_speed
        self.contact_damage = self.contact_damage - 1
        self._dash_cooldown = CHARGER_DASH_COOLDOWN

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)

        if self._is_dashing:
            self._dash_duration -= dt
            if self._dash_duration <= 0:
                self._end_dash()
            else:
                self._move_toward(self._dash_target[0], self._dash_target[1], dt)
        else:
            self._dash_cooldown -= dt
            if self._dash_cooldown <= 0:
                self._begin_dash(player_rect)
            self._move_toward(player_rect.centerx, player_rect.centery, dt)


class Ranger(Enemy):
    def __init__(self, x, y, hp=None, damage=None):
        hp = hp if hp is not None else RANGER_HP
        damage = damage if damage is not None else 1
        super().__init__(x, y, hp=hp, speed=RANGER_SPEED, color=RANGER_COLOR, sprite_name="ranger")
        self.contact_damage = damage
        self._fire_timer = 0.0

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)

        dist = math.hypot(player_rect.centerx - self.rect.centerx,
                          player_rect.centery - self.rect.centery)
        if dist > RANGER_RANGE:
            self._move_toward(player_rect.centerx, player_rect.centery, dt)

        self._fire_timer += dt

    def wants_to_fire(self):
        if self._fire_timer >= RANGER_FIRE_INTERVAL:
            self._fire_timer -= RANGER_FIRE_INTERVAL
            return True
        return False


class Exploder(Enemy):
    def __init__(self, x, y, hp=None, damage=None):
        hp = hp if hp is not None else EXPLODER_HP
        damage = damage if damage is not None else 1
        super().__init__(x, y, hp=hp, speed=EXPLODER_SPEED, color=EXPLODER_COLOR, sprite_name="exploder")
        self.contact_damage = damage
