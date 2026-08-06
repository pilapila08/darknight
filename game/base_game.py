"""R6：NormalGame / TestGame 公共基类。

背景：R6 之前 normal_game.py（1277 行）与 test_game.py（1216 行）约 2500 行核心
循环逻辑高度重复（更新 / 绘制 / 刷怪 / Boss / 掉落 / 技能应用等）。本模块将共享
逻辑收敛到 BaseGame，两个模式类只保留各自的策略钩子（policy hooks）与模式专属
代码，行为零变化（重构前后同一场景表现一致）。

设计原则（R6 纯重构）：
- 所有从原类移入的代码逐行保持原样，只在确实存在行为差异的接缝处插入钩子。
- 每个 `_xxx_...` 钩子都是一处文档化的模式差异（Normal 有打击感/光照/音频，
  Test 精简 + 经验倍率/自动刷怪开关/自定义面板等）。
- 对外接口不变：NormalGame / TestGame 的公开方法、构造签名、实例属性保持原样；
  外部只依赖 game.normal_game.NormalGame 与 game.test_game.TestGame。
"""
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GOLD, GREEN, RED, BLUE,
    SPAWN_INTERVAL, ENEMY_SIZE, ENEMY_HP, ENEMY_SPEED, MAX_ENEMIES,
    ELITE_SIZE, ELITE_SPEED, ELITE_HP, ELITE_HP_MULT, ELITE_DAMAGE_MULT,
    DIFFICULTY_INTERVAL, DIFFICULTY_MAX_TIER, HP_BONUS_PER_TIER, DAMAGE_BONUS_PER_TIER,
    DAMAGE_BONUS_MAX, GROWTH_INTERVAL,
    SPAWN_RATE_CAP_BASE, SPAWN_CAP_PER_BOSS,
    BOSS_FIGHT_SPAWN_SLOWDOWN, FINAL_SURGE_INTERVAL_MULT,
    BULLET_PENALTY_THRESHOLD, BULLET_PENALTY_MULT,
    PLAYER_MAX_HP, PLAYER_INVINCIBLE_TIME,
    MAP_WIDTH, MAP_HEIGHT, XP_BASE, XP_GROWTH,
    BOSS_WARNING_DURATION, MAP_TRANSITION_DURATION,
    SHADOW_MAGE_SHADOW_HP, SHADOW_MAGE_SHADOW_DAMAGE,
    VOID_LORD_VOIDLING_HP, VOID_LORD_VOIDLING_DAMAGE,
    GAME_DURATION_SECONDS,
    DEATH_ECHO_RADIUS, DEATH_ECHO_DAMAGE,
    BOSS_REINFORCE_DELAY, BOSS_REINFORCE_INTERVAL,
    BOSS_REINFORCE_BASIC_COUNT, BOSS_REINFORCE_CHARGER_COUNT,
)
from entities import Player, Enemy, Charger, Ranger, Exploder, Bullet, EnemyBullet
from entities import Particle, DamageNumber, Explosion, TrapManager
from entities import HealthPack, ShieldPickup
from entities.enemy_types import Wraith, Warlock, HomingOrb
from entities.frost_aura import FrostAuraManager
from entities.flame_spitter import FlameSpitterManager
from entities.boss import Boss, BossProjectile, AreaEffect, BOSS_CLASSES, BOSS_CONFIGS, BoomerangFist
from effects import OrbitalBladeManager, ChainLightning
from systems import Camera, AudioManager, load_high_score, save_high_score, record_run_result
from systems.map_manager import MapManager, MAP_CONFIGS
from skills import get_random_skills, apply_skill
from ui import draw_hud, draw_skill_bar, draw_game_over_screen, draw_skill_selection, draw_pause_menu, get_font
from ui.boss_hud import draw_boss_hp_bar
from ui.render_helpers import draw_shadowed_sprite
from i18n import t


class BaseGame:
    """正常 / 测试两种游戏模式的公共基类。

    模式差异全部通过策略钩子表达（默认值 = Test 的精简行为）：
    - 打击感/光照/音频等“juice”：Normal 覆写钩子补全，Test 用基类空实现。
    - 测试专属（经验倍率、自动刷怪、自定义敌人面板）：Test 覆写钩子。
    """

    # ---------------------------------------------------------------- 构造

    def __init__(self, character="default", caption_key="window_caption"):
        pygame.init()
        pygame.key.stop_text_input()
        pygame.event.set_blocked(pygame.TEXTINPUT)
        pygame.event.set_blocked(pygame.TEXTEDITING)

        self.character = character
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(t(caption_key))
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()
        self.audio.start_music()

        self.font = get_font(24)
        self.big_font = get_font(48)
        self.dmg_font = get_font(16)

        self.fullscreen = False
        self.high_score = load_high_score()
        self.new_record = False

        self.running = True
        self.game_over = False
        self.is_victory = False

    def _init_game(self):
        """初始化游戏实体（公共部分）；模式专属实体由 _init_extra 补充。"""
        self.game_state = self._create_game_state()
        self.player = Player(self.game_state.character)
        self.camera = Camera()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.drops = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.damage_numbers = []
        self.explosions = []
        self.blade_mgr = OrbitalBladeManager()
        self.chain_lightning = ChainLightning()
        self.trap_mgr = TrapManager()
        # C02 新武器管理器（content-pack-v2.md §1）
        self.frost_mgr = FrostAuraManager()
        self.flame_mgr = FlameSpitterManager()
        self.fps_smooth = 60.0
        self.bosses = pygame.sprite.Group()
        self.boss_projectiles = pygame.sprite.Group()
        self.area_effects = []
        self.map_manager = MapManager()
        self.warning_flash_alpha = 0
        self.warning_flash_dir = 1
        # R5 统计（结算一次性写入 meta，防频繁 I/O）
        self.run_kills = 0               # 本局普通击杀
        self.run_boss_kills = 0          # 本局 Boss 击杀
        # 模式专属字段（Test: test_handler / orbs / 面板状态；Normal: effects / lighting / R4 计时器）
        self._init_extra()

    def _create_game_state(self):
        """创建游戏状态"""
        from game.state import GameState
        state = GameState(self.character)
        state.menu = False
        state.test_mode = self._game_state_test_mode()
        return state

    # ---------------------------------------------------------------- 主循环

    def run(self):
        """运行游戏，返回 True 表示返回菜单，False 表示退出程序"""
        self._init_game()
        self.audio.start_music()

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            fps_raw = 1.0 / dt if dt > 0 else 60.0
            self.fps_smooth = self.fps_smooth * 0.95 + fps_raw * 0.05

            self._handle_events()
            self._update(dt)
            self._frame_update(dt)
            self._render()

            pygame.display.flip()

        # 始终返回 True（返回主菜单），只有 QUIT 才退出程序
        return True

    def _restart(self):
        """重新开始游戏"""
        self._init_game()
        self.high_score = load_high_score()
        self.new_record = False
        self.game_over = False

    # ---------------------------------------------------------------- 事件

    def _handle_events(self):
        """处理事件（公共骨架；模式专属点击/文本输入由钩子插入原顺序位置）"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # 模式前置事件（Test：文本输入框激活时吞掉所有事件）
            if self._handle_pre_event(event):
                continue

            # 游戏结束
            if self.game_over:
                if self._handle_game_over_event(event):
                    return
                continue

            # 技能选择
            if self.game_state.paused and self.game_state.chosen_skills:
                self._handle_skill_select_event(event)
                continue

            # 模式中段点击（Test：测试面板；Normal：无，调试开关在尾部）
            self._handle_mode_click_event(event)

            # ESC 暂停菜单
            if self.game_state.escaped:
                if self._handle_escaped_event(event):
                    return
                continue

            # 按键处理
            if event.type == pygame.KEYDOWN:
                self._handle_common_keydown(event)

            # 模式尾部点击（Normal：数值显示开关）
            self._handle_mode_tail_event(event)

    def _handle_game_over_event(self, event):
        """结算界面事件；返回 True 表示退出事件循环（ESC 返回主菜单）。"""
        # ESC 返回主菜单（优雅退出游戏循环，main 会重建开始界面）
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return True
        do_restart = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            do_restart = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            btn_rect = pygame.Rect(
                (SCREEN_WIDTH - 240) // 2, SCREEN_HEIGHT - 120, 240, 50)
            if btn_rect.collidepoint(event.pos):
                do_restart = True
        if do_restart:
            self._restart()
        return False

    def _handle_skill_select_event(self, event):
        """技能三选一事件"""
        from ui.skill_select import build_card_rects
        if event.type == pygame.KEYDOWN:
            idx = -1
            if event.key == pygame.K_1:
                idx = 0
            elif event.key == pygame.K_2:
                idx = 1
            elif event.key == pygame.K_3:
                idx = 2
            if 0 <= idx < len(self.game_state.chosen_skills):
                self._apply_skill(self.game_state.chosen_skills[idx])
        if event.type == pygame.MOUSEBUTTONDOWN:
            card_rects = build_card_rects(len(self.game_state.chosen_skills), SCREEN_WIDTH, SCREEN_HEIGHT)
            for i, rect in enumerate(card_rects):
                if rect.collidepoint(event.pos):
                    self._apply_skill(self.game_state.chosen_skills[i])
                    break

    def _handle_escaped_event(self, event):
        """ESC 暂停菜单事件；返回 True 表示退出事件循环（点击退出）。"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state.escaped = False
            elif event.key == pygame.K_1:
                self.game_state.escaped = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            resume_rect, quit_rect = self._get_pause_menu_rects()
            if resume_rect.collidepoint(event.pos):
                self.game_state.escaped = False
            elif quit_rect.collidepoint(event.pos):
                self.running = False
                return True
        return False

    def _handle_common_keydown(self, event):
        """公共按键：ESC 暂停 / F11 全屏"""
        if event.key == pygame.K_ESCAPE:
            self.game_state.escaped = True
        if event.key == pygame.K_F11:
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    def _get_pause_menu_rects(self):
        """获取暂停菜单按钮区域"""
        resume_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 50)
        quit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 70, 200, 50)
        return resume_rect, quit_rect

    def _apply_skill(self, skill):
        """应用技能"""
        self._on_apply_skill()
        apply_skill(self.game_state.stats, skill, self.game_state.character)
        self.game_state.apply_skill_update(skill, self.player, self.blade_mgr)
        self.game_state.chosen_skills = None
        self.game_state.paused = False

    # ---------------------------------------------------------------- 数值

    def _get_current_enemy_stats(self):
        """获取当前游戏时间下各敌人的数值（线性+上限；R4：伤害封顶 DAMAGE_BONUS_MAX）"""
        tier = min(int(self.game_state.elapsed_time / GROWTH_INTERVAL), DIFFICULTY_MAX_TIER)
        hp_bonus = tier * HP_BONUS_PER_TIER
        damage_bonus = min(tier * DAMAGE_BONUS_PER_TIER, DAMAGE_BONUS_MAX)

        return {
            "basic": {
                "hp": ENEMY_HP + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "charger": {
                "hp": self._enemy_type_hp("charger") + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "ranger": {
                "hp": self._enemy_type_hp("ranger") + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "exploder": {
                "hp": self._enemy_type_hp("exploder") + hp_bonus,
                "damage": 0,
                "explosion_damage": (1 + damage_bonus) * 2
            },
            "wraith": {
                "hp": self._enemy_type_hp("wraith") + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "warlock": {
                "hp": self._enemy_type_hp("warlock") + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "elite": {
                "hp": int((ELITE_HP + hp_bonus) * ELITE_HP_MULT),
                "damage": int((1 + damage_bonus) * ELITE_DAMAGE_MULT),
                "explosion_damage": 0
            }
        }

    # ---------------------------------------------------------------- 更新

    def _update(self, dt):
        """更新游戏逻辑（公共骨架；模式差异由钩子表达）"""
        if self.game_over:
            return

        # ESC 暂停或技能选择时跳过游戏逻辑
        if self.game_state.escaped or self.game_state.paused:
            return

        # 打击感效果更新；顿帧期间冻结游戏逻辑（保留相机震动）
        if self._update_juice(dt):
            return

        self.game_state.elapsed_time += dt
        if self.game_state.invincible_timer > 0:
            self.game_state.invincible_timer -= dt

        self.game_state.difficulty_level = int(self.game_state.elapsed_time / DIFFICULTY_INTERVAL)
        # R4 §2.3：tf_cap = 5 + 1.5×boss击杀（Boss 击杀=强度里程碑，修复 150s 刷怪封顶平台期）
        tf_cap = SPAWN_RATE_CAP_BASE + SPAWN_CAP_PER_BOSS * self.game_state.boss_defeated_count
        time_factor = min(self.game_state.elapsed_time / 30, tf_cap)
        current_spawn_interval = SPAWN_INTERVAL / (1 + time_factor * 0.3 + (time_factor * 0.15) ** 2)
        # R4 §2.4：Boss 战期间普通刷怪减速（间隔 ×1.5，速率 ×0.67）
        if self.game_state.boss_active:
            current_spawn_interval *= BOSS_FIGHT_SPAWN_SLOWDOWN
        # R4 §2.5：终局冲锋——最后 60s 刷怪加速
        final_surge = self.game_state.elapsed_time >= GAME_DURATION_SECONDS - 60
        if final_surge:
            current_spawn_interval *= FINAL_SURGE_INTERVAL_MULT

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)
        self.camera.update(self.player.rect, dt)

        # 地图更新
        map_effects = self.map_manager.update(dt, self.player.rect, self.enemies)
        for eff in map_effects:
            if eff["type"] == "player_damage":
                self._damage_player(eff["amount"], 0, 0)

        # Boss检查
        self._check_boss_spawn()

        # Boss预警更新
        if self.game_state.boss_warning_active:
            self._update_boss_warning(dt)

        # 生成敌人 (预警期间暂停)
        if not self.game_state.boss_warning_active:
            self.game_state.spawn_timer += dt
            while self.game_state.spawn_timer >= current_spawn_interval:
                self.game_state.spawn_timer -= current_spawn_interval
                if len(self.enemies) < MAX_ENEMIES and self._should_spawn_auto():
                    self.enemies.add(self._spawn_enemy())

        # 自动射击
        self._update_shooting(dt)

        # 更新实体（BUG-001 修复：Boss 在 enemies 与 bosses 双组。
        # Group.update 丢弃返回值 → Boss.update 的 attacks 被丢 → 攻击饿死。
        # 改为手动循环排除 Boss，Boss 仅由 _update_bosses 驱动一次。）
        for enemy in list(self.enemies):
            if not isinstance(enemy, Boss):
                enemy.update(dt, self.player.rect)
        self.bullets.update(dt)
        self.enemy_bullets.update(dt)
        self.boss_projectiles.update(dt)

        # C02：非 Boss 敌人事件（唤魔师召唤/追踪弹）+ 主从绑定消散检查（无奖励清除）
        for enemy in list(self.enemies):
            if getattr(enemy, "_disperse_at", None) is not None and self.game_state.elapsed_time >= enemy._disperse_at:
                enemy.kill()
                continue
            if hasattr(enemy, "drain_events"):
                for ev in enemy.drain_events():
                    self._process_enemy_event(ev)

        # C02 R7 S2：暗影弹幕尾迹粒子（仅带 trail_color 的 Boss 弹幕）
        for bp in self.boss_projectiles:
            if getattr(bp, "trail_color", None):
                self._add_projectile_trail(bp)

        # Boss更新
        self._update_bosses(dt)

        # R4 §2.4/§2.5：Boss 战防卡关增援波 + 终局冲锋包围波（仅正常模式）
        self._update_endgame_waves(dt, final_surge)

        # 武器系统
        self._update_weapons(dt)

        # 陷阱
        self._update_traps(dt)

        # 持续伤害死亡检查
        self._check_enemy_deaths()

        # 射手开火
        self._update_ranger_shooting()

        # 离屏清理
        self._cleanup_offscreen()

        # 碰撞检测
        self._check_collisions()

        # 经验球
        self._update_drops(dt)

        # 区域效果更新
        self._update_area_effects(dt)

        # 粒子和伤害数字
        self.particles.update(dt)
        for dn in self.damage_numbers[:]:
            dn.update(dt)
            if not dn.alive:
                self.damage_numbers.remove(dn)

        # 升级检查
        self._check_level_up()

        # 游戏结束检查
        self._check_game_end()

    def _spawn_enemy(self, enemy_type_override=None, tier_override=None, pos=None):
        """生成敌人（支持boss召唤覆写）"""
        x, y = pos if pos else self._get_spawn_pos()
        tier = tier_override if tier_override is not None else min(
            int(self.game_state.elapsed_time / DIFFICULTY_INTERVAL), DIFFICULTY_MAX_TIER)
        hp_bonus = tier * HP_BONUS_PER_TIER
        damage_bonus = min(tier * DAMAGE_BONUS_PER_TIER, DAMAGE_BONUS_MAX)

        if enemy_type_override:
            enemy_type = enemy_type_override
        else:
            # C02 §2.4：敌种 5→7（怨灵 tier4/136s、唤魔师 tier6/204s）
            enemy_types = ["basic", "charger", "ranger", "exploder", "wraith", "warlock"]
            enemy_unlock = {"basic": 0, "charger": 1, "ranger": 2, "exploder": 3,
                            "wraith": 4, "warlock": 6}
            enemy_weights = {"basic": 1.0, "charger": 0.4, "ranger": 0.35, "exploder": 0.2,
                             "wraith": 0.25, "warlock": 0.18}

            available = [(t, w) for t, w in enemy_weights.items() if enemy_unlock[t] <= tier]
            # Boss 战期间不刷 warlock（召唤 + Boss 召唤双重压力过载，C02 §2.3）；wraith 保留
            if self.game_state.boss_active:
                available = [(t, w) for t, w in available if t != "warlock"]
            if not available:
                available = [("basic", 1.0)]
            types, weights = zip(*available)
            enemy_type = random.choices(types, weights=weights, k=1)[0]

        if enemy_type == "charger":
            return Charger(x, y, hp=self._enemy_type_hp("charger") + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "ranger":
            return Ranger(x, y, hp=self._enemy_type_hp("ranger") + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "exploder":
            explosion_dmg = (1 + damage_bonus) * 2
            return Exploder(x, y, hp=self._enemy_type_hp("exploder") + hp_bonus,
                            damage=0, explosion_damage=explosion_dmg)
        elif enemy_type == "wraith":
            return Wraith(x, y, hp=self._enemy_type_hp("wraith") + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "warlock":
            return Warlock(x, y, hp=self._enemy_type_hp("warlock") + hp_bonus, damage=1 + damage_bonus)

        # Boss 召唤的特殊敌人（shadow / voidling）
        special = self._spawn_special_enemy(enemy_type, x, y)
        if special is not None:
            return special

        # 精英生成策略（模式不同）
        elite = self._roll_elite(x, y, tier, hp_bonus, damage_bonus)
        if elite is not None:
            return elite

        return Enemy(x, y, hp=ENEMY_HP + hp_bonus, contact_damage=1 + damage_bonus)

    def _get_spawn_pos(self):
        """获取生成位置"""
        left = int(self.camera.offset.x)
        top = int(self.camera.offset.y)
        side = random.randint(0, 3)
        if side == 0:
            return (random.randint(left, left + SCREEN_WIDTH), top - ENEMY_SIZE)
        elif side == 1:
            return (random.randint(left, left + SCREEN_WIDTH), top + SCREEN_HEIGHT)
        elif side == 2:
            return (left - ENEMY_SIZE, random.randint(top, top + SCREEN_HEIGHT))
        else:
            return (left + SCREEN_WIDTH, random.randint(top, top + SCREEN_HEIGHT))

    def _process_enemy_event(self, ev):
        """消费非 Boss 敌人事件（C02 §2.4：唤魔师召唤 / 追踪弹）。"""
        ev_type = ev.get("type")
        if ev_type == "summon":
            # 唤魔师召唤 tier0 基础怪（弱化版，防滚雪球）；绑定主从
            minion = self._spawn_enemy(enemy_type_override="basic", tier_override=0,
                                       pos=(ev.get("x"), ev.get("y")))
            if minion is not None:
                minion._master_id = ev.get("master_id")
                self.enemies.add(minion)
        elif ev_type == "orb":
            orb = HomingOrb(ev["x"], ev["y"], self.player.rect, ev.get("damage", 1))
            self.enemy_bullets.add(orb)

    def _ring_pos(self, index, total, dist=420):
        """环形入场位置：以玩家为中心，均匀分布在 dist px 圆环上。"""
        angle = (2 * math.pi / total) * index
        x = self.player.rect.centerx + int(math.cos(angle) * dist)
        y = self.player.rect.centery + int(math.sin(angle) * dist)
        return (max(50, min(MAP_WIDTH - 50, x)), max(50, min(MAP_HEIGHT - 50, y)))

    def _spawn_reinforcement_wave(self):
        """Boss 战增援波：4 基础 + 1 冲锋，环形入场（R4 §2.4）。"""
        total = BOSS_REINFORCE_BASIC_COUNT + BOSS_REINFORCE_CHARGER_COUNT
        for i in range(BOSS_REINFORCE_BASIC_COUNT):
            self._spawn_enemy(enemy_type_override="basic", pos=self._ring_pos(i, total))
        for i in range(BOSS_REINFORCE_CHARGER_COUNT):
            self._spawn_enemy(enemy_type_override="charger",
                              pos=self._ring_pos(BOSS_REINFORCE_BASIC_COUNT + i, total))

    def _nearest_enemy(self):
        """获取最近的敌人"""
        best = None
        best_dist = float("inf")
        for enemy in self.enemies:
            dist = (self.player.rect.centerx - enemy.rect.centerx) ** 2 + \
                   (self.player.rect.centery - enemy.rect.centery) ** 2
            if dist < best_dist:
                best_dist = dist
                best = enemy
        return best

    def _update_shooting(self, dt):
        """更新射击"""
        self.game_state.fire_timer += dt
        while self.game_state.fire_timer >= self.game_state.stats["fire_interval"] and self.enemies:
            self.game_state.fire_timer -= self.game_state.stats["fire_interval"]
            target = self._nearest_enemy()
            if target:
                bullet_count = self.game_state.stats["bullet_count"]
                bullet_speed_mult = self.game_state.stats.get("bullet_speed", 1.0)
                pierce = self.game_state.stats.get("bullet_pierce", 0)
                pierce_dmg_mult = self.game_state.stats.get("bullet_damage_mult", 1.0)
                dx = target.rect.centerx - self.player.rect.centerx
                dy = target.rect.centery - self.player.rect.centery
                base_angle = math.atan2(dy, dx)
                # 敌人占据中间偏左的位置
                enemy_pos = bullet_count // 2  # 奇数弹：中间；偶数弹：中间偏左
                # 子弹数量多时使用更大的spread覆盖360度
                if bullet_count > 21:
                    spread = (2 * math.pi) / bullet_count  # 360度全覆盖
                    enemy_pos = 0  # 敌人方向为扇形起点
                else:
                    spread = 0.26
                for i in range(bullet_count):
                    offset = spread * (i - enemy_pos)
                    angle = base_angle + offset
                    tx = self.player.rect.centerx + math.cos(angle) * 100
                    ty = self.player.rect.centery + math.sin(angle) * 100
                    # R3 §4.2：第 4 发起（含）每发伤害 ×0.55（边际惩罚）
                    per_bullet = BULLET_PENALTY_MULT if i >= BULLET_PENALTY_THRESHOLD else 1.0
                    self.bullets.add(Bullet(self.player.rect.centerx, self.player.rect.centery,
                                            (tx, ty), bullet_speed_mult,
                                            pierce=pierce, damage_mult=pierce_dmg_mult * per_bullet))
                # 枪口火光
                mx = self.player.rect.centerx + math.cos(base_angle) * 24
                my = self.player.rect.centery + math.sin(base_angle) * 24
                self._on_weapon_fired(base_angle, mx, my)
            self.audio.play_shoot()

    def _update_weapons(self, dt):
        """更新武器系统"""
        # 暗影新星
        if self.game_state.stats.get("has_blades", 0) > 0:
            self.blade_mgr.update(dt)
            blade_hits = self.blade_mgr.check_damage(self.player.rect, self.enemies, dt, self.game_state.stats)
            for enemy, dmg, dead in blade_hits:
                self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), self.dmg_font))
                if dead:
                    self._kill_enemy(enemy)

        # 连锁闪电
        if self.game_state.stats.get("has_lightning", 0) > 0:
            lightning_hits = self.chain_lightning.update(dt, self.player.rect, self.enemies, self.game_state.stats)
            for enemy, dmg, dead in lightning_hits:
                self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), self.dmg_font))
                if dead:
                    self._kill_enemy(enemy)
            # R3 §4.4 C1 静电过载：闪电每次命中使暗影新星当前 CD -0.15s
            self._on_lightning_hits(lightning_hits)

        # 凛冬之环（C02 §1.2：贴身减速 AOE）
        if self.game_state.stats.get("has_frost", 0) > 0:
            frost_hits = self.frost_mgr.update(dt, self.player.rect, self.enemies, self.game_state.stats)
            for enemy, dmg, dead in frost_hits:
                self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), self.dmg_font))
                if dead:
                    self._kill_enemy(enemy)

        # 圣焰喷射器（C02 §1.3：短程锥形喷吐 + 燃烧，可暴击）
        if self.game_state.stats.get("has_flame", 0) > 0:
            flame_hits = self.flame_mgr.update(dt, self.player.rect, self.enemies, self.game_state.stats)
            for enemy, dmg, dead in flame_hits:
                self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), self.dmg_font))
                if dead:
                    self._kill_enemy(enemy)

    def _update_traps(self, dt):
        """更新陷阱"""
        if self.game_state.stats.get("has_traps", 0) > 0:
            trap_interval = self.game_state.stats.get("trap_interval", 2.0)
            self.trap_mgr.update(dt, self.player, trap_interval,
                                trap_damage=self.game_state.stats.get("trap_damage", 4),
                                radius_mult=self.game_state.stats.get("trap_radius_mult", 1.0))
            for trap in list(self.trap_mgr.group):
                trap.check_enemies(self.enemies)

    def _check_enemy_deaths(self):
        """检查敌人死亡（持续伤害）"""
        for enemy in list(self.enemies):
            if enemy.hp <= 0:
                self._kill_enemy(enemy)

    def _update_ranger_shooting(self):
        """更新射手射击"""
        for enemy in list(self.enemies):
            if isinstance(enemy, Ranger) and enemy.wants_to_fire():
                self.enemy_bullets.add(EnemyBullet(
                    enemy.rect.centerx, enemy.rect.centery,
                    self.player.rect.centerx, self.player.rect.centery,
                    enemy.contact_damage))  # 传递射手伤害值

    def _cleanup_offscreen(self):
        """清理离屏子弹"""
        for bullet in list(self.bullets):
            if not (0 <= bullet.rect.centerx <= MAP_WIDTH and 0 <= bullet.rect.centery <= MAP_HEIGHT):
                bullet.kill()
        for eb in list(self.enemy_bullets):
            if not (0 <= eb.rect.centerx <= MAP_WIDTH and 0 <= eb.rect.centery <= MAP_HEIGHT):
                eb.kill()

    def _apply_bullet_hit(self, bullet, enemy):
        """对单个敌人结算一次子弹命中；支持穿透（同一目标不重复命中）。"""
        if id(enemy) in bullet._hit_ids:
            return
        bullet._hit_ids.add(id(enemy))
        self._damage_enemy(bullet, enemy)
        if bullet.pierce > 0:
            bullet.pierce -= 1
        else:
            bullet.kill()

    def _check_collisions(self):
        """碰撞检测"""
        # 子弹碰撞敌人（R3 B1：穿透弹可命中多个目标）
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, False, False)
        for bullet, hit_enemies in hits.items():
            for enemy in hit_enemies:
                self._apply_bullet_hit(bullet, enemy)
                if not bullet.alive():
                    break

        # 子弹碰撞Boss
        for bullet in list(self.bullets):
            for boss in self.bosses:
                if bullet.rect.colliderect(boss.rect):
                    self._apply_bullet_hit(bullet, boss)
                    if not bullet.alive():
                        break

        # Boss弹幕碰撞玩家
        if self.game_state.invincible_timer <= 0:
            for bp in list(self.boss_projectiles):
                if bp.rect.colliderect(self.player.rect):
                    self._damage_player(bp.damage, bp.rect.centerx, bp.rect.centery)
                    self.camera.shake(0.15, 6)
                    bp.kill()
                    break

        # 敌人子弹碰撞玩家
        if self.game_state.invincible_timer <= 0:
            for eb in list(self.enemy_bullets):
                if eb.rect.colliderect(self.player.rect):
                    self._damage_player(eb.damage, eb.rect.centerx, eb.rect.centery)
                    self.camera.shake(0.12, 5)
                    eb.kill()
                    break

        # 敌人接触玩家
        if self.game_state.invincible_timer <= 0:
            for enemy in list(self.enemies):
                if enemy.rect.colliderect(self.player.rect) and enemy.contact_damage > 0:
                    self._damage_player(enemy.contact_damage, enemy.rect.centerx, enemy.rect.centery)
                    self.camera.shake(0.15, 6)
                    dx = enemy.rect.centerx - self.player.rect.centerx
                    dy = enemy.rect.centery - self.player.rect.centery
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        enemy.rect.x += (dx / dist) * 30
                        enemy.rect.y += (dy / dist) * 30
                    break

            # Boss接触玩家
            for boss in self.bosses:
                if boss.rect.colliderect(self.player.rect) and boss.contact_damage > 0:
                    self._damage_player(boss.contact_damage, boss.rect.centerx, boss.rect.centery)
                    self.camera.shake(0.25, 10)
                    break

        # 爆炸
        self._check_explosions()

    def _damage_enemy(self, bullet, enemy):
        """伤害敌人（命中反馈由模式钩子 _apply_hit_feedback 表达）"""
        dmg = self.game_state.stats["bullet_damage"]
        # R3：每发子弹伤害倍率（弹量边际惩罚 ×0.55 / 穿透弹 ×0.85）
        dmg *= getattr(bullet, "damage_mult", 1.0)
        # 急速子弹速度达上限后的伤害加成（独立于火力增强）
        dmg *= self.game_state.stats.get("bullet_speed_damage_mult", 1.0)
        is_crit = random.random() < self.game_state.stats["crit_chance"]
        if is_crit:
            dmg *= self.game_state.stats["crit_multiplier"]

        # 命中反馈：火花/击退/音效（模式不同）
        self._apply_hit_feedback(enemy, bullet, is_crit)

        dead = enemy.take_damage(dmg)
        self._append_damage_number(enemy, dmg, is_crit)

        if dead:
            self._kill_enemy(enemy)
            # 复苏之风
            self._apply_kill_regen()

    def _apply_kill_regen(self):
        """复苏之风：击杀后按击杀数回血"""
        if self.game_state.stats.get("regen_kills", 0) > 0:
            required_kills = self.game_state.stats["regen_kills"]
            self.game_state.stats["regen_kills_progress"] += 1
            if self.game_state.stats["regen_kills_progress"] >= required_kills:
                self.game_state.stats["regen_kills_progress"] = 0
                regen_hp = self.game_state.stats.get("regen_hp_amount", 1)
                self.game_state.player_hp = min(self.game_state.stats["max_hp"], self.game_state.player_hp + regen_hp)

    def _kill_enemy(self, enemy):
        """击杀敌人"""
        if isinstance(enemy, Boss):
            self._kill_boss(enemy)
            return

        count = max(1, int(random.randint(5, 8) * min(1.0, self.fps_smooth / 55.0)))
        for _ in range(count):
            self.particles.add(Particle(enemy.rect.centerx, enemy.rect.centery, enemy._base_color))

        # 死亡残影；精英额外顿帧+震动（模式不同）
        self._on_kill_enemy_juice(enemy)

        if enemy.is_elite:
            base_xp = 3
        elif isinstance(enemy, Exploder):
            self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, enemy.explosion_damage))
            self._on_exploder_killed(enemy)
            base_xp = 1
        else:
            base_xp = 1

        greedy_count = self.game_state.stats.get("greedy_count", 0)
        greedy_mult = 1.0 + 0.15 * greedy_count
        xp_gained = base_xp * greedy_mult * self._xp_mult()

        self.audio.play_enemy_death()
        self.game_state.score += 1
        self.game_state.experience += xp_gained
        self.run_kills += 1  # R5：本局普通击杀统计
        self._maybe_drop_item(enemy)
        # R3 §4.4 C2 死亡回响：击杀精英时引爆周围敌人（模式不同）
        self._on_elite_killed(enemy)
        # C02 §2.3 主从绑定：唤魔师死亡 → 其仆从标记消散（无奖励）
        if hasattr(enemy, "on_death"):
            enemy.on_death(self)
        enemy.kill()

    def _trigger_death_echo(self, x, y):
        """死亡回响：击杀精英/Boss 时，对 200px 内敌人造成 12 伤并击退。"""
        if self.game_state.stats.get("death_echo", 0) <= 0:
            return
        for enemy in list(self.enemies):
            if isinstance(enemy, Boss):
                continue
            dist = math.hypot(enemy.rect.centerx - x, enemy.rect.centery - y)
            if dist <= DEATH_ECHO_RADIUS and dist > 0:
                enemy.rect.x += int((enemy.rect.centerx - x) / dist * 40)
                enemy.rect.y += int((enemy.rect.centery - y) / dist * 40)
                dead = enemy.take_damage(DEATH_ECHO_DAMAGE)
                if dead:
                    self._kill_enemy(enemy)

    def _maybe_drop_item(self, enemy):
        hp_ratio = self.game_state.player_hp / max(1, self.game_state.stats["max_hp"])
        tier = min(int(self.game_state.elapsed_time / GROWTH_INTERVAL), DIFFICULTY_MAX_TIER)
        health_chance = 0.025 + (0.075 if hp_ratio <= 0.35 else 0.0)
        shield_chance = 0.018 + tier * 0.006
        if enemy.is_elite:
            health_chance += 0.045
            shield_chance += 0.055
        if self.game_state.player_shield >= self.game_state.player_max_shield * 0.7:
            shield_chance *= 0.35
        roll = random.random()
        if roll < health_chance:
            amount = 5 if enemy.is_elite else 4
            self.drops.add(HealthPack(enemy.rect.centerx, enemy.rect.centery, amount))
        elif roll < health_chance + shield_chance:
            amount = 6 if enemy.is_elite else 4 + tier
            self.drops.add(ShieldPickup(enemy.rect.centerx, enemy.rect.centery, amount))

    def _damage_player(self, damage, knockback_x, knockback_y):
        """伤害玩家"""
        if self.game_state.invincible_timer <= 0:
            final_damage = damage * self.game_state.stats["damage_taken"]
            if self.game_state.player_shield > 0:
                absorbed = min(self.game_state.player_shield, final_damage)
                self.game_state.player_shield -= absorbed
                final_damage -= absorbed
            # 受击反馈（模式不同）
            self._on_damage_player(final_damage)
            self.game_state.player_hp -= final_damage
            self.game_state.invincible_timer = PLAYER_INVINCIBLE_TIME

    def _check_explosions(self):
        """检查爆炸"""
        for exp in self.explosions:
            exp.update(1/60)
            if not exp._applied:
                # 使用圆形碰撞检测
                dx = self.player.rect.centerx - exp.x
                dy = self.player.rect.centery - exp.y
                dist_sq = dx * dx + dy * dy
                if dist_sq <= exp.max_radius * exp.max_radius and self.game_state.invincible_timer <= 0:
                    self._damage_player(exp.damage, 0, 0)
            # 检查敌人死亡
            for enemy in list(self.enemies):
                if enemy.hp <= 0:
                    self._kill_enemy(enemy)
        self.explosions = [e for e in self.explosions if e.alive]

    def _update_drops(self, dt):
        for drop in list(self.drops):
            drop.update(dt, self.player.rect)
            if drop.rect.colliderect(self.player.rect):
                if drop.kind == "health":
                    self.game_state.player_hp = min(
                        self.game_state.stats["max_hp"],
                        self.game_state.player_hp + drop.amount
                    )
                elif drop.kind == "shield":
                    self.game_state.player_shield = min(
                        self.game_state.player_max_shield,
                        self.game_state.player_shield + drop.amount
                    )
                self._on_pickup()
                drop.kill()

    def _check_level_up(self):
        """检查升级"""
        xp_for_current = self._get_xp_for_level(self.game_state.level)
        xp_for_next = self._get_xp_for_level(self.game_state.level + 1)
        xp_to_next = xp_for_next - xp_for_current

        if self.game_state.experience >= xp_to_next:
            self.game_state.experience -= xp_to_next
            self.game_state.level += 1
            self.game_state.paused = True
            self.game_state.chosen_skills = self._get_random_skills(3)
            self.game_state.stats["max_hp"] += 1
            self.game_state.player_hp = min(self.game_state.player_hp + 1, self.game_state.stats["max_hp"])
            self.player.max_hp = self.game_state.stats["max_hp"]
            self.audio.play_level_up()

    def _get_random_skills(self, count):
        """随机获取技能"""
        return get_random_skills(count, self.game_state.stats)

    def _get_xp_for_level(self, level):
        """计算升到指定等级需要的累计经验值 (几何增长，每级×1.1)"""
        if level <= 1:
            return 0
        result = 0
        needed = float(XP_BASE)
        for l in range(2, level + 1):
            result += int(needed)
            needed *= XP_GROWTH
        return result

    def _trigger_game_over(self, is_victory):
        """统一进入结算：置 game_over、保存最高分、写入 meta 统计。"""
        self.game_state.game_over = True
        self.game_over = True
        self.is_victory = is_victory
        self.new_record = save_high_score(self.game_state.score)
        if self.new_record:
            self.high_score = self.game_state.score
        # R5：结算一次性写入 meta（含自动解锁刷新，重启保留）
        record_run_result(
            self.game_state.character,
            kills=self.run_kills,
            boss_kills=self.run_boss_kills,
            score=self.game_state.score,
            elapsed=self.game_state.elapsed_time,
            victory=is_victory,
        )

    def _check_game_end(self):
        """检查游戏结束：死亡，或存活满 GAME_DURATION_SECONDS 胜利。"""
        if self.game_state.player_hp <= 0:
            self._trigger_game_over(False)
        elif self.game_state.elapsed_time >= GAME_DURATION_SECONDS:
            self._trigger_game_over(True)

    # ---------------------------------------------------------------- 渲染

    def _render(self):
        """渲染（公共骨架；模式差异由钩子表达）"""
        mouse_pos = pygame.mouse.get_pos()
        self.map_manager.draw_background(self.screen, self.camera)

        # 陷阱
        if self.game_state.stats.get("has_traps", 0) > 0:
            for trap in self.trap_mgr.group:
                self.screen.blit(trap.image, self.camera.apply(trap.rect))
        for drop in self.drops:
            draw_shadowed_sprite(self.screen, self.camera, drop.image, drop.rect, shadow_scale=0.7, shadow_alpha=70)

        # 实体按脚底位置排序，避免近处角色被远处角色盖住
        world_entities = [(self.player.rect.bottom, "player", self.player)]
        world_entities.extend((enemy.rect.bottom, "enemy", enemy)
                              for enemy in self.enemies if not isinstance(enemy, Boss))
        world_entities.extend((boss.rect.bottom, "boss", boss) for boss in self.bosses)
        for _, kind, entity in sorted(world_entities, key=lambda item: item[0]):
            if kind == "player":
                entity.draw(self.screen, self.camera)
            elif kind == "boss":
                entity.draw(self.screen, self.camera)
                entity.draw_hp_bar_bg(self.screen, self.dmg_font, self.camera)
            else:
                entity.draw(self.screen, self.camera)
        for bullet in self.bullets:
            self.screen.blit(bullet.image, self.camera.apply(bullet.rect))
        for eb in self.enemy_bullets:
            self.screen.blit(eb.image, self.camera.apply(eb.rect))
        for bp in self.boss_projectiles:
            self.screen.blit(bp.image, self.camera.apply(bp.rect))

        # 模式专属实体（测试模式经验球）
        self._render_mode_entities()

        for particle in self.particles:
            self.screen.blit(particle.image, self.camera.apply(particle.rect))

        # 区域效果
        for ae in self.area_effects:
            ae.draw(self.screen, self.camera)

        # 武器特效
        if self.game_state.stats.get("has_blades", 0) > 0:
            self.blade_mgr.draw(self.screen, self.camera, self.player.rect)
        if self.game_state.stats.get("has_lightning", 0) > 0:
            self.chain_lightning.draw(self.screen, self.camera)
        # C02 新武器（凛冬之环光环 / 圣焰火焰粒子）
        if self.game_state.stats.get("has_frost", 0) > 0:
            self.frost_mgr.draw(self.screen, self.camera, self.player.rect, self.game_state.stats)
        if self.game_state.stats.get("has_flame", 0) > 0:
            self.flame_mgr.draw(self.screen, self.camera, self.player.rect, self.game_state.stats)

        # 爆炸
        for exp in self.explosions:
            exp.draw(self.screen, self.camera)

        # 打击感世界层 + 光照（正常模式；测试模式空实现）
        self._render_world_juice()

        # 伤害数字（在光照之上，保证可读性）
        for dn in self.damage_numbers:
            dn.draw(self.screen, self.camera)

        # Boss预警渲染
        if self.game_state.boss_warning_active:
            self._render_boss_warning()

        # HUD
        xp_for_current = self._get_xp_for_level(self.game_state.level)
        xp_for_next = self._get_xp_for_level(self.game_state.level + 1)
        xp_to_next = xp_for_next - xp_for_current
        current_max_hp = self.game_state.stats.get("max_hp", PLAYER_MAX_HP)
        draw_hud(self.screen, self.font, self.game_state.level, self.game_state.experience, xp_to_next,
                 self.game_state.player_hp, current_max_hp, self.game_state.elapsed_time,
                 self.game_state.player_shield, self.game_state.player_max_shield)
        draw_skill_bar(self.screen, self.font, self.game_state.acquired_skills,
                      mouse_pos, self.game_state.elapsed_time, self.game_state.stats)

        # 全屏打击感效果（受击闪光/低血量脉动；测试模式空实现）
        hp_ratio = self.game_state.player_hp / max(1, current_max_hp)
        self._render_screen_juice(hp_ratio)

        # Boss血条
        if self.game_state.boss_active:
            for boss in self.bosses:
                draw_boss_hp_bar(self.screen, self.font, boss)
                break

        # 模式专属覆盖层（正常：数值面板 / 测试：测试面板）
        self._render_mode_overlays(mouse_pos)

        # 尾部覆盖层（技能选择/ESC暂停/地图过渡/结算，顺序模式不同）
        self._render_tail(mouse_pos)

        # FPS
        fps_color = GREEN if self.fps_smooth >= 55 else (RED if self.fps_smooth < 30 else GOLD)
        fps_text = self.font.render(f"{self.fps_smooth:.0f}", True, fps_color)
        self.screen.blit(fps_text, (self.screen.get_width() - fps_text.get_width() - 8, 8))

        # 标题栏
        pygame.display.set_caption(self._window_title())

    def _render_map_transition(self):
        alpha = int(200 * min(1.0, self.map_manager.transition_timer / MAP_TRANSITION_DURATION))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))
        text = self.map_manager.transition_text
        text_surf = self.big_font.render(text, True, GOLD)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text_surf, text_rect)

    # ---------------------------------------------------------------- Boss System

    def _check_boss_spawn(self):
        if self.game_state.boss_active or self.game_state.boss_warning_active:
            return
        if self.game_state.boss_defeated_count >= len(BOSS_CONFIGS):
            return
        next_config = BOSS_CONFIGS[self.game_state.boss_defeated_count]
        if self.game_state.elapsed_time >= next_config["spawn_time"]:
            self._trigger_boss_warning(next_config)

    def _trigger_boss_warning(self, config):
        self.game_state.boss_warning_active = True
        self.game_state.boss_warning_timer = BOSS_WARNING_DURATION
        self._pending_boss_config = config
        self.warning_flash_alpha = 0
        self.warning_flash_dir = 1
        self._boss_clear_done = False
        self._on_boss_warning()

    def _update_boss_warning(self, dt):
        self.game_state.boss_warning_timer -= dt
        self.warning_flash_alpha += 120 * dt * self.warning_flash_dir
        if self.warning_flash_alpha >= 80:
            self.warning_flash_alpha = 80
            self.warning_flash_dir = -1
        elif self.warning_flash_alpha <= 0:
            self.warning_flash_alpha = 0
            self.warning_flash_dir = 1

        if self.game_state.boss_warning_timer <= BOSS_WARNING_DURATION - 1.5 and not self._boss_clear_done:
            self._boss_clear_done = True
            self._clear_enemies_for_boss()

        if self.game_state.boss_warning_timer <= 0:
            self.game_state.boss_warning_active = False
            config = self._pending_boss_config
            angle = random.uniform(0, math.pi * 2)
            dist = random.randint(200, 400)
            bx = self.player.rect.centerx + int(math.cos(angle) * dist)
            by = self.player.rect.centery + int(math.sin(angle) * dist)
            bx = max(50, min(MAP_WIDTH - 50, bx))
            by = max(50, min(MAP_HEIGHT - 50, by))
            boss = config["cls"](bx, by)
            self.enemies.add(boss)
            self.bosses.add(boss)
            self.game_state.boss_active = True
            self._pending_boss_config = None
            # R7 P0 U1 降临入场（震动+粒子；正常模式另加白闪/顿帧/主题光源）
            self._on_boss_arrive(boss)

    def _update_bosses(self, dt):
        for boss in list(self.bosses):
            attacks = boss.update(dt, self.player.rect)
            if attacks:
                self._process_boss_attacks(attacks)
            if boss.hp <= 0:
                self._kill_boss(boss)

    def _process_boss_attacks(self, attacks):
        for atk in attacks:
            atk_type = atk.get("type")
            if atk_type == "projectile":
                bp = BossProjectile(atk["x"], atk["y"], atk["tx"], atk["ty"],
                                    atk.get("speed", 300), atk["damage"],
                                    atk.get("color", (200, 50, 50)),
                                    atk.get("radius", 6))
                # R7 S2 弹幕尾迹（暗影巫师）
                if atk.get("trail"):
                    bp.trail_color = atk["trail"]
                self.boss_projectiles.add(bp)
            elif atk_type == "boomerang":
                bf = BoomerangFist(atk["x"], atk["y"], atk["tx"], atk["ty"],
                                   atk["sender_rect"], atk["damage"],
                                   atk.get("color", (150, 150, 170)),
                                   atk.get("radius", 12))
                self.boss_projectiles.add(bf)
            elif atk_type == "aoe":
                ae = AreaEffect(atk["x"], atk["y"], atk["radius"],
                                atk["duration"], atk["damage"],
                                atk.get("color", (100, 200, 100)))
                self.area_effects.append(ae)
            elif atk_type == "summon":
                for _ in range(atk.get("count", 1)):
                    angle = random.uniform(0, math.pi * 2)
                    dist = random.randint(30, 80)
                    sx = atk.get("x", self.player.rect.centerx) + int(math.cos(angle) * dist)
                    sy = atk.get("y", self.player.rect.centery) + int(math.sin(angle) * dist)
                    sx = max(50, min(MAP_WIDTH - 50, sx))
                    sy = max(50, min(MAP_HEIGHT - 50, sy))
                    self.enemies.add(self._spawn_enemy(enemy_type_override=atk.get("enemy_type", "basic"),
                                                       tier_override=atk.get("tier", 0), pos=(sx, sy)))
            elif atk_type == "shockwave":
                for angle in [0, math.pi / 2, math.pi, math.pi * 3 / 2]:
                    tx = atk["x"] + math.cos(angle) * 200
                    ty = atk["y"] + math.sin(angle) * 200
                    bp = BossProjectile(atk["x"], atk["y"], tx, ty,
                                        atk.get("speed", 300), atk["damage"],
                                        (200, 200, 100), radius=8, lifetime=0.8)
                    self.boss_projectiles.add(bp)
            elif atk_type == "gravity":
                # 虚空裂隙引力场：核心持续伤害 + 引力牵引（仅正常模式）
                self._process_gravity_attack(atk)
            # ---- R7 P0 演出事件（C02 §4.1）----
            elif atk_type == "telegraph_shake":
                # 尸王冲锋前摇震动提示（C1）
                self.camera.shake(0.15, 4)
            elif atk_type == "teleport_telegraph_shake":
                # 暗影巫师传送蓄力震动（S1）
                self.camera.shake(0.12, 4)
            elif atk_type == "teleport_land_shake":
                # 暗影巫师落地小震屏（S1）
                self.camera.shake(0.15, 5)
            elif atk_type == "boss_enrage":
                # 狂暴横幅 + 音乐 duck（U4）
                self.audio.duck(0.6, 1.2)
                self._on_boss_enrage(atk.get("name", ""))

    def _kill_boss(self, boss):
        for _ in range(30):
            self.particles.add(Particle(boss.rect.centerx, boss.rect.centery,
                                        boss.config.get("color", (255, 50, 50))))
        # Boss 击杀：长顿帧 + 白屏闪光 + 大残影 + 强震动（模式不同）
        self._kill_boss_juice(boss)
        self.camera.shake(0.5, 15)
        greedy_count = self.game_state.stats.get("greedy_count", 0)
        greedy_mult = 1.0 + 0.15 * greedy_count
        self.game_state.experience += int(20 * greedy_mult * self._xp_mult())
        self.game_state.score += 50
        # R3 §4.4 C2 死亡回响：击杀 Boss 引爆周围敌人（模式不同）
        self._kill_boss_extra(boss)
        self.run_boss_kills += 1  # R5：本局 Boss 击杀统计
        boss.kill()
        self.bosses.remove(boss)
        self.game_state.boss_active = False
        self.game_state.boss_defeated_count += 1
        self._trigger_map_transition()

    def _trigger_map_transition(self):
        next_map = self.game_state.boss_defeated_count
        if next_map < len(MAP_CONFIGS):
            self.map_manager.switch_to_map(next_map)
            self._on_map_transition(next_map)

    def _update_area_effects(self, dt):
        for ae in list(self.area_effects):
            ae.update(dt)
            if ae.expired:
                self.area_effects.remove(ae)
                continue
            if ae.should_tick() and ae.contains_point(self.player.rect.centerx, self.player.rect.centery):
                self._damage_player(ae.damage, 0, 0)
            # 引力井：对玩家施加向裂隙中心的位移（仅正常模式）
            self._update_gravity_pull(ae, dt)

    # ================================================================
    # 策略钩子（默认实现 = Test 的精简行为；Normal 覆写补全打击感/光照/音频）
    # ================================================================

    # --- 构造 / 初始化 ---

    def _game_state_test_mode(self):
        """GameState.test_mode 值（Normal=False / Test=True）"""
        return False

    def _init_extra(self):
        """_init_game 公共部分之后的模式专属字段"""
        pass

    # --- 主循环 ---

    def _frame_update(self, dt):
        """主循环每帧额外逻辑（Normal: audio.update / Test: 无）"""
        pass

    # --- 事件钩子 ---

    def _handle_pre_event(self, event):
        """事件循环前置钩子；返回 True 表示该事件已被吞掉（Test: 文本输入框）"""
        return False

    def _handle_mode_click_event(self, event):
        """事件循环中段点击钩子（Test: 测试面板；Normal: 无）"""
        pass

    def _handle_mode_tail_event(self, event):
        """事件循环尾部点击钩子（Normal: 数值显示开关；Test: 无）"""
        pass

    def _on_apply_skill(self):
        """应用技能前音效（Normal: play_ui_click / Test: 无）"""
        pass

    # --- 更新管线 ---

    def _update_juice(self, dt):
        """打击感更新；返回 True 表示顿帧冻结（仅更新相机）"""
        return False

    def _should_spawn_auto(self):
        """是否允许自动刷怪（Test: 受 auto_spawn 开关控制 / Normal: 恒 True）"""
        return True

    def _update_endgame_waves(self, dt, final_surge):
        """终局节奏波（Normal: R4 增援 + 冲锋包围 / Test: 无）"""
        pass

    def _on_weapon_fired(self, base_angle, mx, my):
        """开火枪口火光（Normal: add_muzzle_flash / Test: 无）"""
        pass

    def _on_lightning_hits(self, lightning_hits):
        """闪电命中联动（Normal: 静电过载 CD 减免 / Test: 无）"""
        pass

    def _on_pickup(self):
        """拾取音效（Normal: play_pickup / Test: 无）"""
        pass

    # --- 刷怪 / 数值 ---

    def _enemy_type_hp(self, enemy_type):
        """charger/ranger/exploder 基础 HP（Normal 用 settings 常量 / Test 用面板数值）"""
        raise NotImplementedError

    def _roll_elite(self, x, y, tier, hp_bonus, damage_bonus):
        """精英生成策略；返回 Enemy 或 None"""
        return None

    def _spawn_special_enemy(self, enemy_type, x, y):
        """Boss 召唤特殊敌人（shadow/voidling）；返回 Enemy 或 None"""
        return None

    def _xp_mult(self):
        """经验倍率（Normal: 1.0 / Test: test_xp_multiplier）"""
        return 1.0

    # --- 战斗反馈 ---

    def _apply_hit_feedback(self, enemy, bullet, is_crit):
        """子弹命中反馈 + 击退（Normal: 火花/音效/沿弹道击退；Test: 仅暴击击退）"""
        pass

    def _append_damage_number(self, enemy, dmg, is_crit):
        """伤害飘字（Normal: 暴击金色 crit 标记 / Test: 无 crit 标记）"""
        self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), self.dmg_font))

    def _on_kill_enemy_juice(self, enemy):
        """普通击杀残影/精英顿帧震动（Normal / Test: 无）"""
        pass

    def _on_exploder_killed(self, enemy):
        """自爆怪爆炸音效/震动（Normal / Test: 无）"""
        pass

    def _on_elite_killed(self, enemy):
        """精英死亡回响（Normal / Test: 无）"""
        pass

    def _on_damage_player(self, final_damage):
        """玩家受击反馈（Normal: 闪屏 + hurt 音效 / Test: 无）"""
        pass

    # --- Boss ---

    def _on_boss_warning(self):
        """Boss 预警音效（Normal: play_boss_warning / Test: 无）"""
        pass

    def _clear_enemies_for_boss(self):
        """Boss 战前清场（Normal: 无奖励清除 / Test: 走 _kill_enemy 有奖励）"""
        for enemy in list(self.enemies):
            if not isinstance(enemy, Boss):
                enemy.kill()

    def _process_gravity_attack(self, atk):
        """虚空裂隙引力场攻击（Normal / Test: 无）"""
        pass

    def _update_gravity_pull(self, ae, dt):
        """引力井牵引玩家（Normal / Test: 无）"""
        pass

    def _kill_boss_juice(self, boss):
        """Boss 击杀打击感（Normal: 顿帧/白闪/残影/音效 / Test: 无）"""
        pass

    def _kill_boss_extra(self, boss):
        """Boss 击杀额外效果（Normal: 死亡回响 / Test: 无）"""
        pass

    def _on_map_transition(self, next_map):
        """地图切换光照（Normal: lighting.set_map / Test: 无）"""
        pass

    # --- R7 演出（C02 §4 P0）---

    def _on_boss_arrive(self, boss):
        """Boss 降临入场（U1）：全屏震动 + 粒子爆发（两模式均有）；
        Normal 额外补白闪/顿帧/主题光源（覆写钩子）。"""
        self.camera.shake(0.4, 10)
        color = boss.config.get("color", (255, 50, 50))
        for _ in range(30):
            self.particles.add(Particle(boss.rect.centerx, boss.rect.centery, color))

    def _add_projectile_trail(self, bp):
        """Boss 弹幕尾迹粒子（R7 S2；Normal: add_sparks / Test: 无）"""
        pass

    def _on_boss_enrage(self, name):
        """Boss 狂暴反馈（R7 U4；Normal: 全屏闪红 / Test: 无）"""
        pass

    # --- 渲染 ---

    def _render_mode_entities(self):
        """模式专属世界实体（Test: 经验球 / Normal: 无）"""
        pass

    def _render_world_juice(self):
        """世界层打击感 + 光照（Normal / Test: 无）"""
        pass

    def _render_screen_juice(self, hp_ratio):
        """全屏打击感（Normal: effects.draw_screen / Test: 无）"""
        pass

    def _render_mode_overlays(self, mouse_pos):
        """模式专属 HUD 覆盖层（Normal: 数值面板 / Test: 测试面板）"""
        pass

    def _render_tail(self, mouse_pos):
        """尾部覆盖层，顺序模式不同（Normal: 技能→ESC→地图→结算；Test: 地图→ESC→技能→结算）"""
        raise NotImplementedError

    def _render_boss_warning(self):
        """Boss 预警渲染（两种模式实现完全不同，各自覆写）"""
        raise NotImplementedError

    def _window_title(self):
        """窗口标题（Normal / Test 前缀不同）"""
        raise NotImplementedError
