"""测试游戏模式"""
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, GOLD, GREEN, RED, BLUE,
    SPAWN_INTERVAL, ENEMY_SIZE, ENEMY_HP, ENEMY_SPEED, MAX_ENEMIES,
    ELITE_SIZE, ELITE_SPEED, ELITE_HP, ELITE_HP_MULT, ELITE_DAMAGE_MULT,
    DIFFICULTY_INTERVAL, DIFFICULTY_MAX_TIER, HP_BONUS_PER_TIER, DAMAGE_BONUS_PER_TIER,
    GROWTH_INTERVAL, SPAWN_RATE_CAP,
    PLAYER_MAX_HP, PLAYER_INVINCIBLE_TIME,
    MAP_WIDTH, MAP_HEIGHT, XP_BASE, XP_GROWTH,
    BOSS_WARNING_DURATION, MAP_TRANSITION_DURATION,
    SHADOW_MAGE_SHADOW_HP, SHADOW_MAGE_SHADOW_DAMAGE,
    VOID_LORD_VOIDLING_HP, VOID_LORD_VOIDLING_DAMAGE,
    GAME_DURATION_SECONDS,
)
from entities import Player, Enemy, Charger, Ranger, Exploder, Bullet, EnemyBullet
from entities import Particle, DamageNumber, Explosion, TrapManager
from entities import HealthPack, ShieldPickup
from entities.boss import Boss, BossProjectile, AreaEffect, BOSS_CLASSES, BOSS_CONFIGS, BoomerangFist
from effects import OrbitalBladeManager, ChainLightning
from systems import Camera, AudioManager, load_high_score, save_high_score
from systems.map_manager import MapManager, MAP_CONFIGS
from skills import SKILL_POOL, apply_skill
from ui import (
    draw_hud, draw_skill_bar, draw_game_over_screen, draw_skill_selection,
    draw_test_mode_panel, get_test_skill_rects, get_test_enemy_rects,
    get_test_auto_spawn_rect, get_test_control_rects, get_test_debug_rect,
    get_font, draw_pause_menu
)
from ui.boss_hud import draw_boss_hp_bar
from ui.render_helpers import draw_shadowed_sprite
from game.state import GameState
from game.test_mode import TestModeHandler
from i18n import t


class TestGame:
    """测试游戏模式主类"""

    def __init__(self):
        pygame.init()
        pygame.key.stop_text_input()
        pygame.event.set_blocked(pygame.TEXTINPUT)
        pygame.event.set_blocked(pygame.TEXTEDITING)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(t("window_caption_test"))
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

        self._enemy_types = ["basic", "charger", "ranger", "exploder", "elite"]

    def _init_game(self):
        """初始化游戏实体"""
        self.game_state = self._create_game_state()
        self.test_handler = TestModeHandler()
        self.player = Player()
        self.camera = Camera()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.orbs = pygame.sprite.Group()
        self.drops = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.damage_numbers = []
        self.explosions = []
        self.blade_mgr = OrbitalBladeManager()
        self.chain_lightning = ChainLightning()
        self.trap_mgr = TrapManager()
        self.fps_smooth = 60.0
        self.bosses = pygame.sprite.Group()
        self.boss_projectiles = pygame.sprite.Group()
        self.area_effects = []
        self.map_manager = MapManager()
        self.warning_flash_alpha = 0
        self.warning_flash_dir = 1

        # 测试模式初始值
        self.game_state.test_custom_speed = ENEMY_SPEED
        self.game_state.test_xp_multiplier = 1.0
        self.game_state.test_custom_hp = PLAYER_MAX_HP
        self.game_state.test_custom_max_hp = PLAYER_MAX_HP
        self.game_state.test_custom_damage = 1  # 自定义敌人伤害
        self.debug_stats_enabled = False  # 调试数值显示开关
        self.enemy_panel_expanded = False  # 敌人生成面板是否展开
        self.boss_panel_expanded = False  # Boss测试面板是否展开
        self.active_input_field = None  # 当前激活的输入框 (None, "hp", "damage", "speed")
        self.custom_enemy_type = 0  # 自定义敌人类型索引 (0-4)

    def _create_game_state(self):
        """创建游戏状态"""
        state = GameState()
        state.menu = False
        state.test_mode = True
        return state

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
            self._render()

            pygame.display.flip()

        # 始终返回 True（返回主菜单），只有 QUIT 才退出程序
        return True

    def _handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # 文本输入（输入框激活时）
            if self.active_input_field is not None:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.active_input_field = None
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_input_field == "hp":
                            self.game_state.test_custom_hp = max(1, self.game_state.test_custom_hp // 10)
                        elif self.active_input_field == "damage":
                            self.game_state.test_custom_damage = max(1, self.game_state.test_custom_damage // 10)
                        elif self.active_input_field == "speed":
                            self.game_state.test_custom_speed = max(10, self.game_state.test_custom_speed // 10)
                    elif event.key == pygame.K_MINUS:
                        pass  # 忽略负号
                    else:
                        char = event.unicode
                        if char.isdigit():
                            value = int(char)
                            if self.active_input_field == "hp":
                                self.game_state.test_custom_hp = min(99999, self.game_state.test_custom_hp * 10 + value)
                            elif self.active_input_field == "damage":
                                self.game_state.test_custom_damage = min(99999, self.game_state.test_custom_damage * 10 + value)
                            elif self.active_input_field == "speed":
                                self.game_state.test_custom_speed = min(9999, self.game_state.test_custom_speed * 10 + value)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 点击其他地方取消输入
                    all_rects = get_test_control_rects(SCREEN_WIDTH, SCREEN_HEIGHT, self.enemy_panel_expanded)
                    enemy_rects = all_rects["custom_enemy"]
                    input_rects = ["hp_input", "damage_input", "speed_input"]
                    clicked_input = False
                    for field in input_rects:
                        if field in enemy_rects and enemy_rects[field].collidepoint(event.pos):
                            clicked_input = True
                            break
                    if not clicked_input:
                        self.active_input_field = None
                continue

            # 游戏结束
            if self.game_over:
                # ESC 返回主菜单（优雅退出游戏循环，main 会重建开始界面）
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
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
                continue

            # 技能选择
            if self.game_state.paused and self.game_state.chosen_skills:
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
                continue

            # 测试模式鼠标点击处理
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_test_mode_click(event.pos)

            # ESC 暂停菜单
            if self.game_state.escaped:
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
                        return
                continue

            # 按键处理
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state.escaped = True
                if event.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    def _handle_test_mode_click(self, pos):
        """处理测试模式面板点击"""
        all_rects = get_test_control_rects(SCREEN_WIDTH, SCREEN_HEIGHT, self.enemy_panel_expanded, self.boss_panel_expanded)
        player_rects = all_rects["player"]
        enemy_rects = all_rects["custom_enemy"]

        # 玩家控制按钮
        if player_rects["hp_minus"].collidepoint(pos):
            self.game_state.test_custom_hp = max(1, self.game_state.test_custom_hp - 1)
        elif player_rects["hp_plus"].collidepoint(pos):
            self.game_state.test_custom_hp += 1
        elif player_rects["hp_apply"].collidepoint(pos):
            self.game_state.player_hp = max(1, min(self.game_state.test_custom_hp, self.game_state.test_custom_max_hp))
        elif player_rects["max_hp_minus"].collidepoint(pos):
            self.game_state.test_custom_max_hp = max(1, self.game_state.test_custom_max_hp - 1)
        elif player_rects["max_hp_plus"].collidepoint(pos):
            self.game_state.test_custom_max_hp += 1
        elif player_rects["max_hp_apply"].collidepoint(pos):
            self.game_state.stats["max_hp"] = self.game_state.test_custom_max_hp
            self.game_state.player_hp = min(self.game_state.player_hp, self.game_state.test_custom_max_hp)
        elif player_rects["xp_minus"].collidepoint(pos):
            self.game_state.test_xp_multiplier = max(0, self.game_state.test_xp_multiplier - 0.5)
        elif player_rects["xp_plus"].collidepoint(pos):
            self.game_state.test_xp_multiplier = min(10, self.game_state.test_xp_multiplier + 0.5)
        elif player_rects["xp_apply"].collidepoint(pos):
            self.game_state.test_xp_multiplier = 0
        elif player_rects["full_hp"].collidepoint(pos):
            self.game_state.player_hp = self.game_state.stats.get("max_hp", PLAYER_MAX_HP)
        elif player_rects["add_xp_100"].collidepoint(pos):
            self.game_state.experience += 100
        elif "add_xp_500" in player_rects and player_rects["add_xp_500"].collidepoint(pos):
            self.game_state.experience += 500

        # 敌人生成面板折叠/展开按钮
        elif all_rects["enemy_toggle"].collidepoint(pos):
            self.enemy_panel_expanded = not self.enemy_panel_expanded
            return  # 重新获取rects

        # Boss测试面板折叠/展开按钮
        elif all_rects["boss_toggle"].collidepoint(pos):
            self.boss_panel_expanded = not self.boss_panel_expanded
            return  # 重新获取rects

        # 重新获取更新后的rects
        if self.enemy_panel_expanded:
            all_rects = get_test_control_rects(SCREEN_WIDTH, SCREEN_HEIGHT, self.enemy_panel_expanded, self.boss_panel_expanded)
            enemy_rects = all_rects["custom_enemy"]

        # 自定义敌人类型选择
        for i in range(5):
            if enemy_rects[f"type_{i}"].collidepoint(pos):
                self.custom_enemy_type = i
                return

        # 自定义敌人生成（HP、伤害、速度）
        if enemy_rects["hp_minus"].collidepoint(pos):
            self.game_state.test_custom_hp = max(1, self.game_state.test_custom_hp - 1)
        elif enemy_rects["hp_plus"].collidepoint(pos):
            self.game_state.test_custom_hp += 1
        elif enemy_rects["hp_input"].collidepoint(pos):
            self.active_input_field = "hp"
        elif enemy_rects["damage_minus"].collidepoint(pos):
            self.game_state.test_custom_damage = max(1, self.game_state.test_custom_damage - 1)
        elif enemy_rects["damage_plus"].collidepoint(pos):
            self.game_state.test_custom_damage += 1
        elif enemy_rects["damage_input"].collidepoint(pos):
            self.active_input_field = "damage"
        elif enemy_rects["speed_minus"].collidepoint(pos):
            self.game_state.test_custom_speed = max(10, self.game_state.test_custom_speed - 10)
        elif enemy_rects["speed_plus"].collidepoint(pos):
            self.game_state.test_custom_speed += 10
        elif enemy_rects["speed_input"].collidepoint(pos):
            self.active_input_field = "speed"
        elif enemy_rects["spawn"].collidepoint(pos):
            enemy_types = ["basic", "charger", "ranger", "exploder", "elite"]
            self.test_handler.spawn_custom_enemy_with_type(
                self.enemies, self.player,
                enemy_types[self.custom_enemy_type],
                self.game_state.test_custom_hp, self.game_state.test_custom_speed, self.game_state.test_custom_damage)

        # 技能面板点击
        skill_rects = get_test_skill_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
        for i, skill in enumerate(SKILL_POOL):
            if skill_rects[i].collidepoint(pos):
                self.test_handler.handle_skill_click(skill, self.game_state.stats, self.player, self.blade_mgr)
                self.game_state.acquired_skills.append(skill["name"])
                break

        # 敌人生成点击（仅在展开时）
        if self.enemy_panel_expanded:
            enemy_btn_rects = get_test_enemy_rects(SCREEN_WIDTH, SCREEN_HEIGHT, expanded=True)
            for i, enemy_rect in enumerate(enemy_btn_rects):
                if enemy_rect.collidepoint(pos) and i < len(self._enemy_types):
                    self.test_handler.spawn_enemy_near_player(self._enemy_types[i], self.enemies, self.player)
                    break

        # 自动生成开关
        auto_rect = get_test_auto_spawn_rect(SCREEN_WIDTH, SCREEN_HEIGHT, expanded=self.enemy_panel_expanded)
        if auto_rect.collidepoint(pos):
            self.test_handler.toggle_auto_spawn()
            self.game_state.test_auto_spawn = self.test_handler.auto_spawn

        # Boss测试按钮（仅在展开时）
        if self.boss_panel_expanded:
            from ui.test_panel import get_test_boss_rects, get_test_boss_toggle_rect
            from entities.boss import BOSS_CONFIGS
            boss_toggle_rect = get_test_boss_toggle_rect(SCREEN_WIDTH, SCREEN_HEIGHT, self.enemy_panel_expanded)
            boss_rects = get_test_boss_rects(SCREEN_WIDTH, SCREEN_HEIGHT, boss_panel_expanded=True, enemy_panel_expanded=self.enemy_panel_expanded)
            for i, rect in enumerate(boss_rects):
                # 计算实际位置（紧跟在折叠按钮下方）
                rect.y = boss_toggle_rect.bottom + 5 + i * 33
                if rect.collidepoint(pos):
                    if i < len(BOSS_CONFIGS):
                        # 生成Boss
                        boss = self.test_handler.spawn_boss_near_player(i, self.player)
                        if boss:
                            self.enemies.add(boss)
                            self.bosses.add(boss)
                            self.game_state.boss_active = True
                    else:
                        # 清屏按钮
                        for enemy in list(self.enemies):
                            if not isinstance(enemy, Boss):
                                enemy.kill()
                    return

        # 调试数值显示开关
        debug_rect = get_test_debug_rect(SCREEN_WIDTH, SCREEN_HEIGHT)
        if debug_rect.collidepoint(pos):
            self.debug_stats_enabled = not self.debug_stats_enabled

    def _apply_skill(self, skill):
        """应用技能"""
        apply_skill(self.game_state.stats, skill)
        self.game_state.apply_skill_update(skill, self.player, self.blade_mgr)
        self.game_state.chosen_skills = None
        self.game_state.paused = False

    def _restart(self):
        """重新开始游戏"""
        self._init_game()
        self.high_score = load_high_score()
        self.new_record = False
        self.game_over = False

    def _get_pause_menu_rects(self):
        """获取暂停菜单按钮区域"""
        resume_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 50)
        quit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 70, 200, 50)
        return resume_rect, quit_rect

    def _update(self, dt):
        """更新游戏逻辑"""
        if self.game_over:
            return

        # ESC 暂停或技能选择时跳过游戏逻辑
        if self.game_state.escaped or self.game_state.paused:
            return

        self.game_state.elapsed_time += dt
        if self.game_state.invincible_timer > 0:
            self.game_state.invincible_timer -= dt

        self.game_state.difficulty_level = int(self.game_state.elapsed_time / DIFFICULTY_INTERVAL)
        time_factor = min(self.game_state.elapsed_time / 30, SPAWN_RATE_CAP)
        current_spawn_interval = SPAWN_INTERVAL / (1 + time_factor * 0.3 + (time_factor * 0.15) ** 2)

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

        # 生成敌人（测试模式下受 auto_spawn 控制，预警期间暂停）
        if not self.game_state.boss_warning_active:
            self.game_state.spawn_timer += dt
            while self.game_state.spawn_timer >= current_spawn_interval:
                self.game_state.spawn_timer -= current_spawn_interval
                if len(self.enemies) < MAX_ENEMIES and self.test_handler.should_spawn_enemies(True):
                    self.enemies.add(self._spawn_enemy())

        # 自动射击
        self._update_shooting(dt)

        # 更新实体
        self.enemies.update(dt, self.player.rect)
        self.bullets.update(dt)
        self.enemy_bullets.update(dt)
        self.boss_projectiles.update(dt)

        # Boss更新
        self._update_bosses(dt)

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
        damage_bonus = tier * DAMAGE_BONUS_PER_TIER

        if enemy_type_override:
            enemy_type = enemy_type_override
        else:
            enemy_unlock = {"basic": 0, "charger": 1, "ranger": 2, "exploder": 3}
            enemy_weights = {"basic": 1.0, "charger": 0.4, "ranger": 0.35, "exploder": 0.2}

            available = [(t, w) for t, w in enemy_weights.items() if enemy_unlock[t] <= tier]
            if not available:
                available = [("basic", 1.0)]
            types, weights = zip(*available)
            enemy_type = random.choices(types, weights=weights, k=1)[0]

        if enemy_type == "charger":
            return Charger(x, y, hp=50 + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "ranger":
            return Ranger(x, y, hp=30 + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "exploder":
            return Exploder(x, y, hp=20 + hp_bonus, damage=0, explosion_damage=(1 + damage_bonus) * 2)
        elif enemy_type == "shadow":
            return Enemy(x, y, hp=SHADOW_MAGE_SHADOW_HP, speed=ENEMY_SPEED,
                         size=ENEMY_SIZE, color=(100, 0, 150), contact_damage=SHADOW_MAGE_SHADOW_DAMAGE)
        elif enemy_type == "voidling":
            return Enemy(x, y, hp=VOID_LORD_VOIDLING_HP, speed=ENEMY_SPEED * 1.2,
                         size=ENEMY_SIZE, color=(180, 0, 200), contact_damage=VOID_LORD_VOIDLING_DAMAGE)

        if self.game_state.elapsed_time >= 120 and random.random() < 0.05:
            return Enemy(x, y, hp=ELITE_HP + hp_bonus, speed=ELITE_SPEED,
                        size=ELITE_SIZE, color=BLUE, is_elite=True, sprite_name="elite")
        return Enemy(x, y, hp=ENEMY_HP + hp_bonus, contact_damage=1 + damage_bonus)

    def _get_current_enemy_stats(self):
        """获取当前游戏时间下各敌人的数值（线性+上限）"""
        tier = min(int(self.game_state.elapsed_time / GROWTH_INTERVAL), DIFFICULTY_MAX_TIER)
        hp_bonus = tier * HP_BONUS_PER_TIER
        damage_bonus = tier * DAMAGE_BONUS_PER_TIER

        return {
            "basic": {
                "hp": ENEMY_HP + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "charger": {
                "hp": 50 + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "ranger": {
                "hp": 30 + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "exploder": {
                "hp": 20 + hp_bonus,
                "damage": 0,
                "explosion_damage": (1 + damage_bonus) * 2
            },
            "elite": {
                "hp": int((ELITE_HP + hp_bonus) * ELITE_HP_MULT),
                "damage": int((1 + damage_bonus) * ELITE_DAMAGE_MULT),
                "explosion_damage": 0
            }
        }

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
                    self.bullets.add(Bullet(self.player.rect.centerx, self.player.rect.centery, (tx, ty), bullet_speed_mult))
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
        """检查敌人死亡"""
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

    def _check_collisions(self):
        """碰撞检测"""
        # 子弹碰撞敌人
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, False, False)
        for bullet, hit_enemies in hits.items():
            bullet.kill()
            for enemy in hit_enemies:
                self._damage_enemy(bullet, enemy)
                break

        # 子弹碰撞Boss
        for bullet in list(self.bullets):
            for boss in self.bosses:
                if bullet.rect.colliderect(boss.rect):
                    self._damage_enemy(bullet, boss)
                    bullet.kill()
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
        """伤害敌人"""
        dmg = self.game_state.stats["bullet_damage"]
        # 急速子弹速度达上限后的伤害加成（独立于火力增强）
        dmg *= self.game_state.stats.get("bullet_speed_damage_mult", 1.0)
        is_crit = random.random() < self.game_state.stats["crit_chance"]
        if is_crit:
            dmg *= self.game_state.stats["crit_multiplier"]
            dx = enemy.rect.centerx - self.player.rect.centerx
            dy = enemy.rect.centery - self.player.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                enemy.rect.x += (dx / dist) * 12
                enemy.rect.y += (dy / dist) * 12

        dead = enemy.take_damage(dmg)
        self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), self.dmg_font))

        if dead:
            self._kill_enemy(enemy)
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

        if enemy.is_elite:
            base_xp = 3
        elif isinstance(enemy, Exploder):
            self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, enemy.explosion_damage))
            base_xp = 1
        else:
            base_xp = 1

        greedy_count = self.game_state.stats.get("greedy_count", 0)
        greedy_mult = 1.0 + 0.15 * greedy_count
        xp_gained = base_xp * greedy_mult * self.game_state.test_xp_multiplier

        self.audio.play_enemy_death()
        self.game_state.score += 1
        self.game_state.experience += xp_gained
        self._maybe_drop_item(enemy)
        enemy.kill()

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

    def _get_random_skills(self, count):
        """随机获取技能"""
        from skills import get_random_skills as original_get_random_skills
        return original_get_random_skills(count, self.game_state.stats)

    def _trigger_game_over(self, is_victory):
        """统一进入结算：置 game_over 并保存最高分。"""
        self.game_state.game_over = True
        self.game_over = True
        self.is_victory = is_victory
        self.new_record = save_high_score(self.game_state.score)
        if self.new_record:
            self.high_score = self.game_state.score

    def _check_game_end(self):
        """检查游戏结束：死亡，或存活满 GAME_DURATION_SECONDS 胜利。"""
        if self.game_state.player_hp <= 0:
            self._trigger_game_over(False)
        elif self.game_state.elapsed_time >= GAME_DURATION_SECONDS:
            self._trigger_game_over(True)

    def _render(self):
        """渲染"""
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
        for orb in self.orbs:
            self.screen.blit(orb.image, self.camera.apply(orb.rect))
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

        # 爆炸和伤害数字
        for exp in self.explosions:
            exp.draw(self.screen, self.camera)
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

        # Boss血条
        if self.game_state.boss_active:
            for boss in self.bosses:
                draw_boss_hp_bar(self.screen, self.font, boss)
                break

        # 测试模式面板
        if not self.game_state.paused and not self.game_state.game_over and not self.game_state.escaped:
            enemy_stats = self._get_current_enemy_stats()
            draw_test_mode_panel(
                self.screen, self.font, mouse_pos, self.game_state.test_auto_spawn,
                self.game_state.player_hp, self.game_state.stats.get("max_hp", PLAYER_MAX_HP),
                self.game_state.test_xp_multiplier,
                self.game_state.test_custom_hp, self.game_state.test_custom_speed,
                self.game_state.test_custom_damage,
                self.debug_stats_enabled, enemy_stats,
                self.enemy_panel_expanded, self.boss_panel_expanded,
                self.active_input_field, self.custom_enemy_type
            )

        # 地图过渡
        if self.map_manager.transition_active:
            self._render_map_transition()

        # ESC 暂停菜单
        if self.game_state.escaped:
            resume_rect, quit_rect = self._get_pause_menu_rects()
            draw_pause_menu(self.screen, self.big_font, self.font, mouse_pos)

        # 技能选择
        if self.game_state.paused and self.game_state.chosen_skills:
            from ui.skill_select import build_card_rects
            draw_skill_selection(self.screen, self.big_font, self.font, self.game_state.chosen_skills,
                               mouse_pos, self.game_state.acquired_skills, self.game_state.stats)

        # 游戏结束
        if self.game_state.game_over:
            draw_game_over_screen(self.screen, self.big_font, self.font,
                                 self.game_state.elapsed_time, self.game_state.score,
                                 self.game_state.level, self.high_score, self.new_record, self.is_victory)

        # FPS
        fps_color = GREEN if self.fps_smooth >= 55 else (RED if self.fps_smooth < 30 else GOLD)
        fps_text = self.font.render(f"{self.fps_smooth:.0f}", True, fps_color)
        self.screen.blit(fps_text, (self.screen.get_width() - fps_text.get_width() - 8, 8))

        # 标题栏
        player_dps = self.game_state.stats["bullet_damage"] * self.game_state.stats["bullet_count"] / self.game_state.stats["fire_interval"]
        time_str = f"{self.game_state.elapsed_time:.0f}s"
        bc = self.game_state.stats["bullet_count"]
        map_name = self.map_manager.map_data["name"]
        title = f"[测试] 击杀:{self.game_state.score} | DPS:{player_dps:.0f} | {time_str} | {map_name} | 新星:{self.game_state.stats.get('has_blades', 0)}"
        pygame.display.set_caption(title)

    # --- Boss System (mirrored from NormalGame) ---

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
            for enemy in list(self.enemies):
                if not isinstance(enemy, Boss):
                    self._kill_enemy(enemy)

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
                pass

    def _kill_boss(self, boss):
        for _ in range(30):
            self.particles.add(Particle(boss.rect.centerx, boss.rect.centery,
                                        boss.config.get("color", (255, 50, 50))))
        self.camera.shake(0.5, 15)
        greedy_count = self.game_state.stats.get("greedy_count", 0)
        greedy_mult = 1.0 + 0.15 * greedy_count
        self.game_state.experience += int(20 * greedy_mult * self.game_state.test_xp_multiplier)
        self.game_state.score += 50
        boss.kill()
        self.bosses.remove(boss)
        self.game_state.boss_active = False
        self.game_state.boss_defeated_count += 1
        self._trigger_map_transition()

    def _trigger_map_transition(self):
        next_map = self.game_state.boss_defeated_count
        if next_map < len(MAP_CONFIGS):
            self.map_manager.switch_to_map(next_map)

    def _update_area_effects(self, dt):
        for ae in list(self.area_effects):
            ae.update(dt)
            if ae.expired:
                self.area_effects.remove(ae)
                continue
            if ae.should_tick() and ae.contains_point(self.player.rect.centerx, self.player.rect.centery):
                self._damage_player(ae.damage, 0, 0)

    def _render_boss_warning(self):
        config = getattr(self, '_pending_boss_config', None)
        if not config:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        flash_color = config.get("color", (255, 50, 50))
        alpha = int(self.warning_flash_alpha)
        overlay.fill((*flash_color, min(60, alpha)))
        pygame.draw.rect(overlay, (*flash_color, alpha), (0, 0, SCREEN_WIDTH, 4))
        pygame.draw.rect(overlay, (*flash_color, alpha), (0, SCREEN_HEIGHT - 4, SCREEN_WIDTH, 4))
        pygame.draw.rect(overlay, (*flash_color, alpha), (0, 0, 4, SCREEN_HEIGHT))
        pygame.draw.rect(overlay, (*flash_color, alpha), (SCREEN_WIDTH - 4, 0, 4, SCREEN_HEIGHT))
        self.screen.blit(overlay, (0, 0))
        warn_text = f"!! 警告 : {config['name']} 即将到来 !!"
        text_surf = self.big_font.render(warn_text, True, GOLD)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        shadow_surf = self.big_font.render(warn_text, True, RED)
        self.screen.blit(shadow_surf, text_rect.move(2, 2))
        self.screen.blit(text_surf, text_rect)

    def _render_map_transition(self):
        alpha = int(200 * min(1.0, self.map_manager.transition_timer / MAP_TRANSITION_DURATION))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))
        text = self.map_manager.transition_text
        text_surf = self.big_font.render(text, True, GOLD)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text_surf, text_rect)
