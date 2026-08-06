"""正常游戏模式（R6：继承 BaseGame，仅保留正常模式专属策略钩子与 UI）"""
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, BLUE,
    CHARGER_HP, RANGER_HP, EXPLODER_HP,
    WRATH_HP, WARLOCK_HP,
    ELITE_SIZE, ELITE_SPEED, ELITE_HP, ELITE_HP_MULT, ELITE_DAMAGE_MULT,
    ELITE_CHANCE, ELITE_CHANCE_RAMP_PER_BOSS, ELITE_CHANCE_RAMP_PER_MIN, ELITE_CHANCE_MAX,
    ELITE_ACTIVATION, FINAL_SURGE_ELITE_BONUS, GAME_DURATION_SECONDS,
    STATIC_OVERLOAD_CD_REDUCTION,
    BOSS_REINFORCE_DELAY, BOSS_REINFORCE_INTERVAL,
    BOSS_REINFORCE_BASIC_COUNT, BOSS_REINFORCE_CHARGER_COUNT,
    FINAL_SURGE_WAVE_INTERVAL, FINAL_SURGE_WAVE_COUNT,
    MAP_WIDTH, MAP_HEIGHT, ENEMY_SIZE, ENEMY_SPEED,
    SHADOW_MAGE_SHADOW_HP, SHADOW_MAGE_SHADOW_DAMAGE,
    VOID_LORD_VOIDLING_HP, VOID_LORD_VOIDLING_DAMAGE,
    VOID_LORD_VOID_RIFT_DAMAGE, VOID_LORD_VOID_RIFT_RADIUS,
    VOID_LORD_VOID_RIFT_DURATION, VOID_LORD_GRAVITY_STRENGTH, VOID_LORD_GRAVITY_RADIUS,
    BOSS_WARNING_DURATION,
)
from entities import Enemy, Exploder, Particle, DamageNumber
from entities.boss import Boss, GravityWell
from effects.juice import EffectManager
from systems.lighting import LightingSystem, PLAYER_LIGHT_RADIUS, PLAYER_LIGHT_COLOR
from ui import draw_pause_menu, draw_skill_selection, draw_game_over_screen
from ui.drawables import get_font as ui_get_font
from game.base_game import BaseGame


class NormalGame(BaseGame):
    """正常游戏模式主类"""

    def __init__(self, character="default"):
        super().__init__(character, "window_caption")
        self.debug_stats_enabled = False  # 数值显示开关

    # ------------------------------------------------------------ 初始化钩子

    def _game_state_test_mode(self):
        return False

    def _init_extra(self):
        # 打击感 / 光照 / R4 节奏计时器
        self.effects = EffectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.lighting = LightingSystem()
        self._boss_fight_timer = 0.0     # Boss 战已进行时长（用于 45s 增援波）
        self._last_reinforce_time = 0.0  # 上次增援波时间戳
        self._surge_timer = 0.0          # 终局冲锋包围波计时

    # ------------------------------------------------------------ 主循环钩子

    def _frame_update(self, dt):
        self.audio.update(dt)

    def _on_apply_skill(self):
        self.audio.play_ui_click()

    # ------------------------------------------------------------ 更新管线钩子

    def _update_juice(self, dt):
        self.effects.update(dt)
        if self.effects.consume_hitstop(dt):
            self.camera.update(self.player.rect, dt)
            return True
        return False

    def _update_endgame_waves(self, dt, final_surge):
        # R4 §2.4：Boss 战防卡关增援波（超 45s 后每 15s 一波：4基础+1冲锋，环形入场）
        if self.game_state.boss_active:
            self._boss_fight_timer += dt
            if (self._boss_fight_timer >= BOSS_REINFORCE_DELAY
                    and self._boss_fight_timer - self._last_reinforce_time >= BOSS_REINFORCE_INTERVAL):
                self._last_reinforce_time = self._boss_fight_timer
                self._spawn_reinforcement_wave()
        else:
            self._boss_fight_timer = 0.0
            self._last_reinforce_time = 0.0

        # R4 §2.5：终局冲锋包围波（每 20s 一波 8 只环形入场，防龟缩角落）
        if final_surge:
            self._surge_timer += dt
            if self._surge_timer >= FINAL_SURGE_WAVE_INTERVAL:
                self._surge_timer = 0.0
                for i in range(FINAL_SURGE_WAVE_COUNT):
                    self._spawn_enemy(pos=self._ring_pos(i, FINAL_SURGE_WAVE_COUNT))

    def _on_weapon_fired(self, base_angle, mx, my):
        self.effects.add_muzzle_flash(mx, my, base_angle)

    def _on_lightning_hits(self, lightning_hits):
        # R3 §4.4 C1 静电过载：闪电每次命中使暗影新星当前 CD -0.15s
        if self.game_state.stats.get("static_overload", 0) > 0 and lightning_hits:
            reduction = STATIC_OVERLOAD_CD_REDUCTION * len(lightning_hits)
            self.blade_mgr.cooldown_timer = max(0.0, self.blade_mgr.cooldown_timer - reduction)

    def _on_pickup(self):
        self.audio.play_pickup()

    # ------------------------------------------------------------ 刷怪 / 数值钩子

    def _enemy_type_hp(self, enemy_type):
        return {"charger": CHARGER_HP, "ranger": RANGER_HP, "exploder": EXPLODER_HP,
                "wraith": WRATH_HP, "warlock": WARLOCK_HP}[enemy_type]

    def _roll_elite(self, x, y, tier, hp_bonus, damage_bonus):
        # R4 §2.3 精英概率斜坡：min(0.22 + 0.05×b + 0.01×⌊t/60⌋, 0.45)；终局 +0.10
        elite_chance = min(
            ELITE_CHANCE + ELITE_CHANCE_RAMP_PER_BOSS * self.game_state.boss_defeated_count
            + ELITE_CHANCE_RAMP_PER_MIN * (self.game_state.elapsed_time // 60),
            ELITE_CHANCE_MAX)
        if self.game_state.elapsed_time >= GAME_DURATION_SECONDS - 60:
            elite_chance += FINAL_SURGE_ELITE_BONUS
        # R4 §2.4：Boss 战期间不刷精英（精英+召唤物双重压力过载）
        if (not self.game_state.boss_active
                and self.game_state.elapsed_time >= ELITE_ACTIVATION
                and random.random() < elite_chance):
            elite_hp = int((ELITE_HP + hp_bonus) * ELITE_HP_MULT)
            return Enemy(x, y, hp=elite_hp, speed=ELITE_SPEED,
                         size=ELITE_SIZE, color=BLUE, is_elite=True,
                         sprite_name="elite", contact_damage=int((1 + damage_bonus) * ELITE_DAMAGE_MULT))
        return None

    def _spawn_special_enemy(self, enemy_type, x, y):
        if enemy_type == "shadow":
            return Enemy(x, y, hp=SHADOW_MAGE_SHADOW_HP, speed=ENEMY_SPEED,
                         size=ENEMY_SIZE, color=(100, 0, 150), is_elite=False,
                         sprite_name=None, contact_damage=SHADOW_MAGE_SHADOW_DAMAGE)
        if enemy_type == "voidling":
            return Enemy(x, y, hp=VOID_LORD_VOIDLING_HP, speed=ENEMY_SPEED * 1.2,
                         size=ENEMY_SIZE, color=(180, 0, 200), is_elite=False,
                         sprite_name=None, contact_damage=VOID_LORD_VOIDLING_DAMAGE)
        return None

    # ------------------------------------------------------------ 战斗反馈钩子

    def _apply_hit_feedback(self, enemy, bullet, is_crit):
        # 命中反馈：沿子弹方向的火花 + 击退
        bvx = getattr(bullet, "vx", 0.0)
        bvy = getattr(bullet, "vy", 0.0)
        speed = math.hypot(bvx, bvy)
        if speed > 0:
            nx, ny = bvx / speed, bvy / speed
        else:
            nx, ny = 0.0, -1.0
        if is_crit:
            self.effects.add_sparks(enemy.rect.centerx, enemy.rect.centery,
                                    nx, ny, color=(255, 230, 120), count=7)
            self.effects.trigger_hitstop(0.03)
        else:
            self.effects.add_sparks(enemy.rect.centerx, enemy.rect.centery, nx, ny)
        self.audio.play_hit()
        if not isinstance(enemy, Boss):
            kb = 16 if is_crit else 6
            enemy.rect.x += int(nx * kb)
            enemy.rect.y += int(ny * kb)

    def _append_damage_number(self, enemy, dmg, is_crit):
        self.damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top,
                                                int(dmg), self.dmg_font, crit=is_crit))

    def _on_kill_enemy_juice(self, enemy):
        # 死亡残影；精英额外顿帧+震动
        self.effects.add_death_ghost(enemy.image, enemy.rect.center)
        if enemy.is_elite:
            self.effects.trigger_hitstop(0.05)
            self.camera.shake(0.18, 5)

    def _on_exploder_killed(self, enemy):
        self.audio.play_explosion()
        self.camera.shake(0.2, 7)

    def _on_elite_killed(self, enemy):
        if enemy.is_elite:
            self._trigger_death_echo(enemy.rect.centerx, enemy.rect.centery)

    def _on_damage_player(self, final_damage):
        # 受击反馈：护盾吸收闪蓝，掉血闪红
        if final_damage > 0:
            self.effects.screen_flash((235, 45, 40), 85)
        else:
            self.effects.screen_flash((80, 170, 255), 60)
        self.audio.play_hurt()

    # ------------------------------------------------------------ Boss 钩子

    def _on_boss_warning(self):
        self.audio.play_boss_warning()

    def _process_gravity_attack(self, atk):
        # 虚空裂隙引力场：核心持续伤害 + 引力牵引（玩家被拉向裂隙中心）
        well = GravityWell(atk["x"], atk["y"],
                           atk.get("radius", VOID_LORD_VOID_RIFT_RADIUS),
                           atk.get("duration", VOID_LORD_VOID_RIFT_DURATION),
                           atk.get("damage", VOID_LORD_VOID_RIFT_DAMAGE),
                           atk.get("strength", VOID_LORD_GRAVITY_STRENGTH),
                           atk.get("color", (180, 0, 200)),
                           pull_radius=atk.get("pull_radius", VOID_LORD_GRAVITY_RADIUS))
        self.area_effects.append(well)

    def _update_gravity_pull(self, ae, dt):
        if isinstance(ae, GravityWell):
            dx, dy = ae.pull_vector(self.player.rect.centerx, self.player.rect.centery, dt)
            if dx or dy:
                self.player.rect.x += dx
                self.player.rect.y += dy
                self.player.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))

    def _kill_boss_juice(self, boss):
        # Boss 击杀：长顿帧 + 白屏闪光 + 大残影（强震动在基类统一处理）
        self.effects.trigger_hitstop(0.25)
        self.effects.screen_flash((255, 255, 255), 170)
        self.effects.add_death_ghost(boss.image, boss.rect.center)
        self.audio.play_boss_death()

    def _kill_boss_extra(self, boss):
        self._trigger_death_echo(boss.rect.centerx, boss.rect.centery)

    def _on_map_transition(self, next_map):
        self.lighting.set_map(next_map)

    # ------------------------------------------------------------ R7 演出覆写

    def _on_boss_arrive(self, boss):
        # U1 降临入场：震动+粒子（基类）+ 白闪 + 长顿帧 + Boss 主题光源
        super()._on_boss_arrive(boss)
        self.effects.screen_flash((255, 255, 255), 120)
        self.effects.trigger_hitstop(0.12)
        color = boss.config.get("color", (255, 50, 50))
        self.lighting.add_light(boss.rect.centerx, boss.rect.centery, 220, color, 1.0)

    def _add_projectile_trail(self, bp):
        # S2 暗影弹幕尾迹：每帧少量火花（低开销）
        if random.random() < 0.5:
            self.effects.add_sparks(bp.rect.centerx, bp.rect.centery,
                                    -bp.vx, -bp.vy, color=bp.trail_color, count=1)

    def _on_boss_enrage(self, name):
        # U4 狂暴：全屏红闪（横幅在 boss_hud 绘制，音乐 duck 在基类处理）
        self.effects.screen_flash((255, 60, 40), 90)

    # ------------------------------------------------------------ 渲染钩子

    def _render_world_juice(self):
        # 打击感效果（世界层：残影/火花/枪口火光）+ 暗夜光照
        self.effects.draw_world(self.screen, self.camera)
        self._submit_lights()
        self.lighting.render(self.screen, self.camera)

    def _render_screen_juice(self, hp_ratio):
        # 全屏打击感效果（受击闪光/低血量脉动）
        self.effects.draw_screen(self.screen, hp_ratio)

    def _render_mode_overlays(self, mouse_pos):
        # 数值显示面板
        self._draw_debug_stats_panel(mouse_pos)

    def _render_tail(self, mouse_pos):
        # 技能选择
        if self.game_state.paused and self.game_state.chosen_skills:
            draw_skill_selection(self.screen, self.big_font, self.font, self.game_state.chosen_skills,
                                 mouse_pos, self.game_state.acquired_skills, self.game_state.stats)
        # ESC 暂停菜单
        if self.game_state.escaped:
            draw_pause_menu(self.screen, self.big_font, self.font, mouse_pos)
        # 地图过渡
        if self.map_manager.transition_active:
            self._render_map_transition()
        # 游戏结束
        if self.game_state.game_over:
            draw_game_over_screen(self.screen, self.big_font, self.font,
                                  self.game_state.elapsed_time, self.game_state.score,
                                  self.game_state.level, self.high_score, self.new_record, self.is_victory)

    def _render_boss_warning(self):
        config = getattr(self, '_pending_boss_config', None)
        if not config:
            return
        # 登场仪式：电影黑边 + 大字横幅 + 展开分割线
        progress = 1.0 - self.game_state.boss_warning_timer / BOSS_WARNING_DURATION
        appear = min(1.0, progress / 0.25)          # 前25%时间入场
        flash_color = config.get("color", (255, 50, 50))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # 上下黑边（letterbox）滑入
        bar_h = int(70 * appear)
        if bar_h > 0:
            pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, bar_h))
            pygame.draw.rect(self.screen, (0, 0, 0),
                             (0, SCREEN_HEIGHT - bar_h, SCREEN_WIDTH, bar_h))

        # 背景暗化 + 呼吸色边框
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(110 * appear)))
        alpha = int(self.warning_flash_alpha)
        pygame.draw.rect(overlay, (*flash_color, alpha), (0, 0, SCREEN_WIDTH, 4))
        pygame.draw.rect(overlay, (*flash_color, alpha), (0, SCREEN_HEIGHT - 4, SCREEN_WIDTH, 4))
        pygame.draw.rect(overlay, (*flash_color, alpha), (0, 0, 4, SCREEN_HEIGHT))
        pygame.draw.rect(overlay, (*flash_color, alpha), (SCREEN_WIDTH - 4, 0, 4, SCREEN_HEIGHT))
        self.screen.blit(overlay, (0, 0))

        # 从中心向两侧展开的分割线
        line_w = int(SCREEN_WIDTH * 0.42 * appear)
        glow = tuple(min(255, c + 80) for c in flash_color)
        for dy, sub_w in ((-52, line_w), (52, line_w)):
            pygame.draw.line(self.screen, glow, (cx - sub_w, cy + dy), (cx + sub_w, cy + dy), 2)

        # 横幅文字：警告小字 + Boss名大字
        warn_font = ui_get_font(20)
        warn_text = warn_font.render("——  强大的敌人逼近  ——", True, glow)
        self.screen.blit(warn_text, warn_text.get_rect(center=(cx, cy - 34)))

        name_font = ui_get_font(58, bold=True)
        name_surf = name_font.render(config['name'], True, GOLD)
        shadow_surf = name_font.render(config['name'], True, (120, 20, 20))
        name_rect = name_surf.get_rect(center=(cx, cy + 8))
        self.screen.blit(shadow_surf, name_rect.move(3, 3))
        self.screen.blit(name_surf, name_rect)

    def _window_title(self):
        player_dps = self.game_state.stats["bullet_damage"] * self.game_state.stats["bullet_count"] / self.game_state.stats["fire_interval"]
        time_str = f"{self.game_state.elapsed_time:.0f}s"
        bc = self.game_state.stats["bullet_count"]
        map_name = self.map_manager.map_data["name"]
        return f"击杀:{self.game_state.score} | DPS:{player_dps:.0f} | {time_str} | {map_name} | 新星:{self.game_state.stats.get('has_blades', 0)}"

    # ------------------------------------------------------------ 正常模式专属

    def _handle_mode_tail_event(self, event):
        # 数值显示开关点击检测
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            debug_rect = self._get_debug_stats_rect()
            if debug_rect.collidepoint(event.pos):
                self.debug_stats_enabled = not self.debug_stats_enabled

    def _get_debug_stats_rect(self):
        """获取数值显示开关的点击区域"""
        return pygame.Rect(10, 10, 80, 24)

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
                "wraith": "怨灵",
                "warlock": "唤魔师",
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

    def _submit_lights(self):
        """登记本帧所有光源（玩家/子弹/经验球/爆炸/Boss等）"""
        L = self.lighting
        px, py = self.player.rect.center
        # QOL 调亮：玩家光源半径 330→400（集中常量见 lighting.PLAYER_LIGHT_RADIUS）
        L.add_light(px, py, PLAYER_LIGHT_RADIUS, PLAYER_LIGHT_COLOR)
        for bullet in self.bullets:
            L.add_light(bullet.rect.centerx, bullet.rect.centery, 55, (150, 195, 255), 0.85)
        for eb in self.enemy_bullets:
            L.add_light(eb.rect.centerx, eb.rect.centery, 46, (255, 130, 100), 0.8)
        for bp in self.boss_projectiles:
            L.add_light(bp.rect.centerx, bp.rect.centery, 70, (255, 120, 120), 0.9)
        for drop in self.drops:
            color = (120, 255, 150) if drop.kind == "health" else (110, 200, 255)
            L.add_light(drop.rect.centerx, drop.rect.centery, 52, color, 0.7)
        for exp in self.explosions:
            L.add_light(exp.x, exp.y, 180, (255, 170, 80))
        for boss in self.bosses:
            c = boss.config.get("color", (255, 80, 80))
            glow = tuple(min(255, v + 90) for v in c)
            L.add_light(boss.rect.centerx, boss.rect.centery, 200, glow, 0.75)
        if self.game_state.stats.get("has_traps", 0) > 0:
            for trap in self.trap_mgr.group:
                L.add_light(trap.rect.centerx, trap.rect.centery, 60, (140, 240, 120), 0.5)
