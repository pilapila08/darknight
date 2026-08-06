import math
import random
import pygame
from entities.enemy import Enemy
from entities.enemy_bullet import EnemyBullet
from settings import (CHARGER_SPEED, CHARGER_HP, CHARGER_DASH_SPEED,
                      CHARGER_DASH_DURATION, CHARGER_DASH_COOLDOWN,
                      CHARGER_COLOR,
                      RANGER_SPEED, RANGER_HP, RANGER_RANGE,
                      RANGER_FIRE_INTERVAL, RANGER_COLOR,
                      EXPLODER_SPEED, EXPLODER_HP, EXPLODER_DAMAGE, EXPLODER_COLOR,
                      MAP_WIDTH, MAP_HEIGHT,
                      WRATH_SPEED, WRATH_HP, WRATH_BLINK_INTERVAL,
                      WRATH_BLINK_DIST_MIN, WRATH_BLINK_DIST_MAX,
                      WRATH_TELEGRAPH, WRATH_LAND_PAUSE, WRATH_COLOR,
                      WARLOCK_SPEED, WARLOCK_HP, WARLOCK_KEEP_DIST,
                      WARLOCK_SUMMON_INTERVAL, WARLOCK_SUMMON_COUNT,
                      WARLOCK_ORB_INTERVAL, WARLOCK_ORB_SPEED, WARLOCK_COLOR,
                      ENEMY_HP, ENEMY_SPEED, ELITE_HP, ELITE_SPEED)


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
    def __init__(self, x, y, hp=None, damage=None, explosion_damage=None):
        hp = hp if hp is not None else EXPLODER_HP
        damage = damage if damage is not None else 0  # 爆炸怪无接触伤害
        super().__init__(x, y, hp=hp, speed=EXPLODER_SPEED, color=EXPLODER_COLOR, sprite_name="exploder")
        self.contact_damage = damage
        # 自爆伤害 = 普通怪接触伤害 × 2
        self.explosion_damage = explosion_damage if explosion_damage is not None else 2


class Wraith(Enemy):
    """怨灵（C02 §2.2）：周期性向玩家闪现（相位型）。

    - 每 1.2s 朝玩家方向瞬移 150–220px；
    - 闪现前 0.4s 在落点生成淡紫残影提示（提示期为实体，可被预判击杀）；
    - 落地后停顿 0.5s 再行动；非闪现期以 60px/s 低速飘向玩家。
    """

    def __init__(self, x, y, hp=None, damage=None):
        hp = hp if hp is not None else WRATH_HP
        damage = damage if damage is not None else 1
        super().__init__(x, y, hp=hp, speed=WRATH_SPEED, color=WRATH_COLOR, sprite_name="wraith")
        self.contact_damage = damage
        self._base_speed = WRATH_SPEED
        self._blink_timer = random.uniform(0, WRATH_BLINK_INTERVAL)
        self._telegraph_timer = 0.0
        self._telegraph_pos = None
        self._land_pause_timer = 0.0

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)

        # 落地停顿
        if self._land_pause_timer > 0:
            self._land_pause_timer -= dt
            return

        # 落点提示期（不移动；提示结束瞬间闪现）
        if self._telegraph_timer > 0:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0 and self._telegraph_pos:
                self.rect.centerx = self._telegraph_pos[0]
                self.rect.centery = self._telegraph_pos[1]
                self._telegraph_pos = None
                self._land_pause_timer = WRATH_LAND_PAUSE
            return

        # 闪现计时
        self._blink_timer -= dt
        if self._blink_timer <= 0:
            self._blink_timer = WRATH_BLINK_INTERVAL
            dist = random.uniform(WRATH_BLINK_DIST_MIN, WRATH_BLINK_DIST_MAX)
            angle = math.atan2(player_rect.centery - self.rect.centery,
                               player_rect.centerx - self.rect.centerx)
            angle += random.uniform(-0.6, 0.6)
            tx = self.rect.centerx + math.cos(angle) * dist
            ty = self.rect.centery + math.sin(angle) * dist
            tx = max(50, min(MAP_WIDTH - 50, tx))
            ty = max(50, min(MAP_HEIGHT - 50, ty))
            self._telegraph_pos = (tx, ty)
            self._telegraph_timer = WRATH_TELEGRAPH
            return

        self._move_toward(player_rect.centerx, player_rect.centery, dt)

    def draw(self, screen, camera):
        # 落点残影提示（淡紫圈，提示期内可见）
        if self._telegraph_timer > 0 and self._telegraph_pos:
            pos = camera.apply(pygame.Rect(self._telegraph_pos[0], self._telegraph_pos[1], 0, 0))
            r = max(10, self.rect.width // 2)
            surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            c = r + 5
            pygame.draw.circle(surf, (150, 110, 255, 80), (c, c), r)
            pygame.draw.circle(surf, (170, 130, 255, 150), (c, c), r, 2)
            screen.blit(surf, (pos.x - c, pos.y - c))
        super().draw(screen, camera)


class Warlock(Enemy):
    """唤魔师（C02 §2.3）：站桩施法者（普通怪里第一个召唤者）。

    - 与玩家保持 240px（过近则后退，只退不进）；
    - 每 2.5s 召唤 1 只 tier0 基础怪（弱化版，防滚雪球）；
    - 每 5s 释放一颗慢速追踪弹（复用 enemy_bullets 通道 + HomingOrb）。
    - 主从绑定：死亡时存活仆从 2s 内消散（无奖励清除，同 R4 Boss 清场规则）。
    """

    def __init__(self, x, y, hp=None, damage=None):
        hp = hp if hp is not None else WARLOCK_HP
        damage = damage if damage is not None else 1
        super().__init__(x, y, hp=hp, speed=WARLOCK_SPEED, color=WARLOCK_COLOR, sprite_name="warlock")
        self.contact_damage = damage
        self._base_speed = WARLOCK_SPEED
        self.summon_timer = 0.0
        self.orb_timer = random.uniform(0, WARLOCK_ORB_INTERVAL)
        self._pending_events = []

    def update(self, dt, player_rect):
        self._update_flash(dt)
        self._update_dot(dt)

        # 保持距离：过近则后退
        dist = math.hypot(player_rect.centerx - self.rect.centerx,
                          player_rect.centery - self.rect.centery)
        if dist < WARLOCK_KEEP_DIST and dist > 1:
            self.rect.x -= (player_rect.centerx - self.rect.centerx) / dist * self.speed * dt
            self.rect.y -= (player_rect.centery - self.rect.centery) / dist * self.speed * dt
        else:
            self._move_toward(player_rect.centerx, player_rect.centery, dt)

        # 召唤
        self.summon_timer += dt
        if self.summon_timer >= WARLOCK_SUMMON_INTERVAL:
            self.summon_timer = 0.0
            for _ in range(WARLOCK_SUMMON_COUNT):
                sx = self.rect.centerx + random.randint(-40, 40)
                sy = self.rect.centery + random.randint(-40, 40)
                self._pending_events.append({
                    "type": "summon", "x": sx, "y": sy, "master_id": id(self)})

        # 追踪弹
        self.orb_timer += dt
        if self.orb_timer >= WARLOCK_ORB_INTERVAL:
            self.orb_timer = 0.0
            self._pending_events.append({
                "type": "orb", "x": self.rect.centerx, "y": self.rect.centery,
                "tx": player_rect.centerx, "ty": player_rect.centery,
                "damage": self.contact_damage})

    def drain_events(self):
        """返回本帧累积的事件（召唤/追踪弹），由游戏层消费。"""
        evs = self._pending_events
        self._pending_events = []
        return evs

    def on_death(self, game):
        """主从绑定：死亡时标记存活仆从 2s 后消散（无奖励清除）。"""
        for e in list(game.enemies):
            if getattr(e, "_master_id", None) == id(self):
                e._disperse_at = game.game_state.elapsed_time + 2.0


class HomingOrb(EnemyBullet):
    """唤魔师追踪弹：慢速弯曲飞向玩家（威胁在"必须躲"）。"""

    def __init__(self, x, y, player_rect, damage=1):
        self.player_rect = player_rect
        super().__init__(x, y, player_rect.centerx, player_rect.centery, damage)
        dx = player_rect.centerx - x
        dy = player_rect.centery - y
        dist = math.hypot(dx, dy)
        self.vx = (dx / dist) * WARLOCK_ORB_SPEED if dist > 0 else 0
        self.vy = (dy / dist) * WARLOCK_ORB_SPEED if dist > 0 else 0
        # 视觉：暗紫慢速球
        size = 18
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.circle(self.image, (150, 50, 220, 70), (c, c), 7)
        pygame.draw.circle(self.image, (200, 120, 255), (c, c), 4)
        pygame.draw.circle(self.image, (235, 220, 255), (c - 1, c - 1), 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = damage

    def update(self, dt):
        # 每帧重新瞄准玩家（弯曲追踪）
        dx = self.player_rect.centerx - self.rect.centerx
        dy = self.player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * WARLOCK_ORB_SPEED
            self.vy = (dy / dist) * WARLOCK_ORB_SPEED
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt


# ================================================================
# 敌人类型统一表（DN-ENG-TEST-R1：单一来源，7 种）
# 测试面板的快速生成 / 自定义敌种选择 / 敌种按钮渲染全部走该表。
# 生成时 wraith/warlock 复用 BaseGame._spawn_enemy（C02 已实现构造路径）。
# ================================================================
ENEMY_TYPE_DEFS = [
    {"key": "basic", "name": "基础", "color": (255, 80, 80), "cls": Enemy,
     "default_hp": ENEMY_HP, "default_speed": ENEMY_SPEED, "elite": False},
    {"key": "charger", "name": "冲锋", "color": (255, 140, 0), "cls": Charger,
     "default_hp": CHARGER_HP, "default_speed": CHARGER_SPEED, "elite": False},
    {"key": "ranger", "name": "射手", "color": (0, 200, 100), "cls": Ranger,
     "default_hp": RANGER_HP, "default_speed": RANGER_SPEED, "elite": False},
    {"key": "exploder", "name": "自爆", "color": (200, 50, 200), "cls": Exploder,
     "default_hp": EXPLODER_HP, "default_speed": EXPLODER_SPEED, "elite": False},
    {"key": "elite", "name": "精英", "color": (50, 150, 255), "cls": Enemy,
     "default_hp": ELITE_HP, "default_speed": ELITE_SPEED, "elite": True},
    {"key": "wraith", "name": "怨灵", "color": (150, 110, 255), "cls": Wraith,
     "default_hp": WRATH_HP, "default_speed": WRATH_SPEED, "elite": False},
    {"key": "warlock", "name": "唤魔师", "color": (200, 120, 255), "cls": Warlock,
     "default_hp": WARLOCK_HP, "default_speed": WARLOCK_SPEED, "elite": False},
]
ENEMY_TYPE_BY_KEY = {d["key"]: d for d in ENEMY_TYPE_DEFS}
