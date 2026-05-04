"""正常游戏模式"""
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, GOLD, GREEN, RED, BLUE,
    SPAWN_INTERVAL, ENEMY_SIZE, ENEMY_HP, ENEMY_SPEED, MAX_ENEMIES,
    ELITE_SIZE, ELITE_SPEED, ELITE_HP,
    ELITE_CHANCE, ELITE_ACTIVATION, ELITE_HP_MULT, ELITE_DAMAGE_MULT,
    CHARGER_HP, RANGER_HP, EXPLODER_HP,
    DIFFICULTY_INTERVAL, HP_BONUS_PER_TIER, DAMAGE_BONUS_PER_TIER,
    GROWTH_INTERVAL, XP_BONUS_PER_GROWTH, XP_GROWTH_INTERVAL,
    MAP_WIDTH, MAP_HEIGHT, XP_BASE, XP_DIFF_INCREMENT,
    PLAYER_MAX_HP, PLAYER_INVINCIBLE_TIME,
    FIRE_INTERVAL, GAME_DURATION
)
from entities import Player, Enemy, Charger, Ranger, Exploder, Bullet, EnemyBullet
from entities import XpOrb, Particle, DamageNumber, Explosion, TrapManager
from effects import OrbitalBladeManager, ChainLightning
from systems import Camera, AudioManager, load_high_score, save_high_score
from skills import get_random_skills, apply_skill
from ui import draw_hud, draw_skill_bar, draw_game_over_screen, draw_skill_selection, draw_pause_menu, get_font
from ui.drawables import get_font as ui_get_font


class NormalGame:
    """正常游戏模式主类"""

    def __init__(self):
        pygame.init()
        pygame.key.stop_text_input()
        pygame.event.set_blocked(pygame.TEXTINPUT)
        pygame.event.set_blocked(pygame.TEXTEDITING)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("暗夜求生  |  F11 全屏")
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()
        self.audio.start_music()

        self.font = get_font(24)
        self.big_font = get_font(48)
        self.dmg_font = get_font(16)

        self.fullscreen = False
        self.high_score = load_high_score()
        self.new_record = False
        self.debug_stats_enabled = False  # 数值显示开关

        self.running = True
        self.game_over = False
        self.is_victory = False

    def _init_game(self):
        """初始化游戏实体"""
        self.game_state = self._create_game_state()
        self.player = Player()
        self.camera = Camera()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.orbs = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.damage_numbers = []
        self.explosions = []
        self.blade_mgr = OrbitalBladeManager()
        self.chain_lightning = ChainLightning()
        self.trap_mgr = TrapManager()
        self.fps_smooth = 60.0

    def _create_game_state(self):
        """创建游戏状态"""
        from game.state import GameState
        state = GameState()
        state.menu = False
        state.test_mode = False
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

            # 游戏结束
            if self.game_over:
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

            # 数值显示开关点击检测
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                debug_rect = self._get_debug_stats_rect()
                if debug_rect.collidepoint(event.pos):
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

    def _get_debug_stats_rect(self):
        """获取数值显示开关的点击区域"""
        return pygame.Rect(10, 10, 80, 24)

    def _get_current_enemy_stats(self):
        """获取当前游戏时间下各敌人的数值"""
        growth_count = int(self.game_state.elapsed_time / GROWTH_INTERVAL)
        total_bonus = growth_count * (growth_count + 1) // 2
        hp_bonus = total_bonus
        damage_bonus = total_bonus

        return {
            "basic": {
                "hp": ENEMY_HP + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "charger": {
                "hp": CHARGER_HP + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "ranger": {
                "hp": RANGER_HP + hp_bonus,
                "damage": 1 + damage_bonus,
                "explosion_damage": 0
            },
            "exploder": {
                "hp": EXPLODER_HP + hp_bonus,
                "damage": 0,
                "explosion_damage": (1 + damage_bonus) * 2
            },
            "elite": {
                "hp": int((ELITE_HP + hp_bonus) * ELITE_HP_MULT),
                "damage": int((1 + damage_bonus) * ELITE_DAMAGE_MULT),
                "explosion_damage": 0
            }
        }

    def _draw_debug_stats_panel(self, mouse_pos):
        """绘制数值显示面板"""
        tiny_font = ui_get_font(11)

        # 数值显示开关
        debug_rect = self._get_debug_stats_rect()
        debug_hovered = debug_rect.collidepoint(mouse_pos)
        debug_color = (80, 200, 80) if self.debug_stats_enabled else (150, 150, 150)

        pygame.draw.rect(self.screen, (30, 30, 40), debug_rect, border_radius=4)
        pygame.draw.rect(self.screen, debug_color, debug_rect, 2 if not debug_hovered else 3, border_radius=4)
        debug_text = "数值 ON" if self.debug_stats_enabled else "数值 OFF"
        text = tiny_font.render(debug_text, True, debug_color)
        text_rect = text.get_rect(center=debug_rect.center)
        self.screen.blit(text, text_rect)

        # 敌人数值显示
        if self.debug_stats_enabled:
            enemy_stats = self._get_current_enemy_stats()
            stats_y = 42
            stats_x = 10
            type_names = {
                "basic": "基础",
                "charger": "冲锋",
                "ranger": "射手",
                "exploder": "自爆",
                "elite": "精英"
            }
            for enemy_type, stats in enemy_stats.items():
                name = type_names.get(enemy_type, enemy_type)
                hp_str = f"{name}: HP{stats['hp']}"
                if enemy_type == "exploder":
                    dmg_str = f" 爆炸{stats['explosion_damage']}"
                elif enemy_type == "ranger":
                    dmg_str = f" 弹{stats['damage']}"
                else:
                    dmg_str = f" 伤{stats['damage']}"
                stat_text = tiny_font.render(hp_str + dmg_str, True, (200, 200, 200))
                self.screen.blit(stat_text, (stats_x, stats_y))
                stats_y += 14

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
        time_factor = self.game_state.elapsed_time / 30
        current_spawn_interval = SPAWN_INTERVAL / (1 + time_factor * 0.5 + (time_factor * 0.3) ** 2)

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)
        self.camera.update(self.player.rect, dt)

        # 生成敌人
        self.game_state.spawn_timer += dt
        while self.game_state.spawn_timer >= current_spawn_interval:
            self.game_state.spawn_timer -= current_spawn_interval
            if len(self.enemies) < MAX_ENEMIES:
                self.enemies.add(self._spawn_enemy())

        # 自动射击
        self._update_shooting(dt)

        # 更新实体
        self.enemies.update(dt, self.player.rect)
        self.bullets.update(dt)
        self.enemy_bullets.update(dt)

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
        self._update_orbs()

        # 粒子和伤害数字
        self.particles.update(dt)
        for dn in self.damage_numbers[:]:
            dn.update(dt)
            if not dn.alive:
                self.damage_numbers.remove(dn)

        # 升级检查
        self._check_level_up()

        # 胜负检查
        self._check_game_end()

    def _spawn_enemy(self):
        """生成敌人"""
        x, y = self._get_spawn_pos()
        growth_count = int(self.game_state.elapsed_time / GROWTH_INTERVAL)
        total_bonus = growth_count * (growth_count + 1) // 2
        hp_bonus = total_bonus
        damage_bonus = total_bonus
        tier = int(self.game_state.elapsed_time / DIFFICULTY_INTERVAL)

        enemy_types = ["basic", "charger", "ranger", "exploder"]
        enemy_unlock = {"basic": 0, "charger": 1, "ranger": 2, "exploder": 3}
        enemy_weights = {"basic": 1.0, "charger": 0.4, "ranger": 0.35, "exploder": 0.2}

        available = [(t, w) for t, w in enemy_weights.items() if enemy_unlock[t] <= tier]
        if not available:
            available = [("basic", 1.0)]
        types, weights = zip(*available)
        enemy_type = random.choices(types, weights=weights, k=1)[0]

        if enemy_type == "charger":
            return Charger(x, y, hp=CHARGER_HP + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "ranger":
            return Ranger(x, y, hp=RANGER_HP + hp_bonus, damage=1 + damage_bonus)
        elif enemy_type == "exploder":
            explosion_dmg = (1 + damage_bonus) * 2
            return Exploder(x, y, hp=EXPLODER_HP + hp_bonus, damage=0, explosion_damage=explosion_dmg)

        if self.game_state.elapsed_time >= ELITE_ACTIVATION and random.random() < ELITE_CHANCE:
            elite_hp = int((ELITE_HP + hp_bonus) * ELITE_HP_MULT)
            return Enemy(x, y, hp=elite_hp, speed=ELITE_SPEED,
                         size=ELITE_SIZE, color=BLUE, is_elite=True,
                         sprite_name="elite", contact_damage=int((1 + damage_bonus) * ELITE_DAMAGE_MULT))
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
        # 旋转利刃
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

    def _check_collisions(self):
        """碰撞检测"""
        # 子弹碰撞敌人
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, False, False)
        for bullet, hit_enemies in hits.items():
            bullet.kill()
            for enemy in hit_enemies:
                self._damage_enemy(bullet, enemy)
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
            # 复苏之风
            if self.game_state.stats.get("regen_kills", 0) > 0:
                required_kills = self.game_state.stats["regen_kills"]
                self.game_state.stats["regen_kills_progress"] += 1
                if self.game_state.stats["regen_kills_progress"] >= required_kills:
                    self.game_state.stats["regen_kills_progress"] = 0
                    regen_hp = self.game_state.stats.get("regen_hp_amount", 1)
                    self.game_state.player_hp = min(self.game_state.stats["max_hp"], self.game_state.player_hp + regen_hp)

    def _kill_enemy(self, enemy):
        """击杀敌人"""
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

        # 经验获取 = 基础经验 × (1 + 时间加成) × 1.25^(贪婪之魂次数)
        time_bonus = 1 + (self.game_state.elapsed_time // XP_GROWTH_INTERVAL) * XP_BONUS_PER_GROWTH
        greedy_count = self.game_state.stats.get("greedy_count", 0)
        greedy_mult = 1.25 ** greedy_count if greedy_count > 0 else 1.0
        xp_gained = base_xp * time_bonus * greedy_mult

        self.audio.play_enemy_death()
        self.game_state.score += 1
        self.game_state.experience += xp_gained
        enemy.kill()

    def _damage_player(self, damage, knockback_x, knockback_y):
        """伤害玩家"""
        if self.game_state.invincible_timer <= 0:
            self.game_state.player_hp -= damage * self.game_state.stats["damage_taken"]
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

    def _update_orbs(self):
        """更新经验球"""
        for orb in list(self.orbs):
            orb.update(1/60, self.player.rect, self.game_state.stats["pickup_range"])
            if orb.rect.colliderect(self.player.rect):
                orb.kill()

    def _check_level_up(self):
        """检查升级"""
        xp_for_current = self._get_xp_for_level(self.game_state.level)
        xp_for_next = self._get_xp_for_level(self.game_state.level + 1)
        xp_to_next = xp_for_next - xp_for_current

        if self.game_state.experience >= xp_to_next:
            self.game_state.experience -= xp_to_next
            self.game_state.level += 1
            self.game_state.paused = True
            self.game_state.chosen_skills = get_random_skills(3)
            self.game_state.stats["max_hp"] += 1
            self.game_state.player_hp = min(self.game_state.player_hp + 1, self.game_state.stats["max_hp"])
            self.player.max_hp = self.game_state.stats["max_hp"]
            self.audio.play_level_up()

    def _get_xp_for_level(self, level):
        """计算升到指定等级需要的累计经验值"""
        if level <= 1:
            return 0
        if level == 2:
            return XP_BASE

        total = XP_BASE
        for l in range(3, min(level + 1, 31)):
            block_idx = (l - 2) // 10
            position = (l - 2) % 10
            level_increment = XP_BASE + block_idx * 10 + position * (XP_DIFF_INCREMENT - 3 + block_idx * XP_DIFF_INCREMENT)
            total += level_increment

        if level > 30:
            last_needed = self._get_xp_for_level(30) - self._get_xp_for_level(29)
            for l in range(31, level + 1):
                last_needed = int(last_needed * 1.1)
                total += last_needed
        return total

    def _check_game_end(self):
        """检查游戏结束"""
        # 胜利（10分钟到达）
        if self.game_state.elapsed_time >= GAME_DURATION:
            self.game_state.game_over = True
            self.game_over = True
            self.new_record = save_high_score(self.game_state.score)
            if self.new_record:
                self.high_score = self.game_state.score
            self.is_victory = True
        # 死亡
        elif self.game_state.player_hp <= 0:
            self.game_state.game_over = True
            self.game_over = True
            self.new_record = save_high_score(self.game_state.score)
            if self.new_record:
                self.high_score = self.game_state.score
            self.is_victory = False

    def _render(self):
        """渲染"""
        self.screen.fill(BLACK)
        self.camera.draw_grid(self.screen)

        # 陷阱
        if self.game_state.stats.get("has_traps", 0) > 0:
            for trap in self.trap_mgr.group:
                self.screen.blit(trap.image, self.camera.apply(trap.rect))

        # 实体
        self.player.draw(self.screen, self.camera)
        for enemy in self.enemies:
            self.screen.blit(enemy.image, self.camera.apply(enemy.rect))
        for bullet in self.bullets:
            self.screen.blit(bullet.image, self.camera.apply(bullet.rect))
        for eb in self.enemy_bullets:
            self.screen.blit(eb.image, self.camera.apply(eb.rect))
        for orb in self.orbs:
            self.screen.blit(orb.image, self.camera.apply(orb.rect))
        for particle in self.particles:
            self.screen.blit(particle.image, self.camera.apply(particle.rect))

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

        # HUD
        xp_for_current = self._get_xp_for_level(self.game_state.level)
        xp_for_next = self._get_xp_for_level(self.game_state.level + 1)
        xp_to_next = xp_for_next - xp_for_current
        current_max_hp = self.game_state.stats.get("max_hp", PLAYER_MAX_HP)
        draw_hud(self.screen, self.font, self.game_state.level, self.game_state.experience, xp_to_next,
                 self.game_state.player_hp, current_max_hp, self.game_state.elapsed_time)
        draw_skill_bar(self.screen, self.font, self.game_state.acquired_skills,
                      pygame.mouse.get_pos(), self.game_state.elapsed_time, self.game_state.stats)

        # 数值显示面板
        self._draw_debug_stats_panel(pygame.mouse.get_pos())

        # 技能选择
        if self.game_state.paused and self.game_state.chosen_skills:
            draw_skill_selection(self.screen, self.big_font, self.font, self.game_state.chosen_skills,
                               pygame.mouse.get_pos(), self.game_state.acquired_skills, self.game_state.stats)

        # ESC 暂停菜单
        if self.game_state.escaped:
            draw_pause_menu(self.screen, self.big_font, self.font, pygame.mouse.get_pos())

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
        title = f"击杀:{self.game_state.score} | DPS:{player_dps:.0f} | {time_str} | 难度{self.game_state.difficulty_level} | 刀:{bc+1}"
        pygame.display.set_caption(title)
