"""测试游戏模式（R6：继承 BaseGame；DN-ENG-TEST-R1：测试面板结构化重构）。

结构变化：
- 状态单一源：全部面板状态收敛到 TestGame.test_handler.state（TestPanelState），
  TestGame 不再散落实例属性；game_state.test_xp_multiplier / test_auto_spawn 保留镜像。
- 布局集中：点击与渲染共用 ui.test_panel.build_test_layout 单一布局结果。
- 点击分发：按面板分区组织（玩家控制 / 自定义敌 / 敌种快速生成 / 技能 / Boss / 调试）。
- 敌人类型：统一 ENEMY_TYPE_DEFS（7 种，含 wraith/warlock）。
- 输入：TEXTINPUT 事件收集（与主菜单一致），输入框标识用 TestInputField 常量。
"""
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, RED, BLUE,
    ENEMY_SIZE, ENEMY_SPEED, PLAYER_MAX_HP,
    ELITE_SIZE, ELITE_SPEED, ELITE_HP,
    SHADOW_MAGE_SHADOW_HP, SHADOW_MAGE_SHADOW_DAMAGE,
    VOID_LORD_VOIDLING_HP, VOID_LORD_VOIDLING_DAMAGE,
)
from entities import Enemy
from entities.boss import Boss, BOSS_CONFIGS
from skills import SKILL_POOL
from ui import (
    draw_game_over_screen, draw_skill_selection,
    draw_test_mode_panel, build_test_layout, draw_pause_menu
)
from game.base_game import BaseGame
from game.test_mode import TestModeHandler, TestInputField, ENEMY_TYPE_DEFS


class TestGame(BaseGame):
    """测试游戏模式主类"""

    def __init__(self, character="default"):
        super().__init__(character, "window_caption_test")

    # ------------------------------------------------------------ 初始化钩子

    def _game_state_test_mode(self):
        return True

    def _init_extra(self):
        # 状态单一源：TestGame 只持有 handler 一个引用
        self.test_handler = TestModeHandler()
        # 镜像键（BaseGame 钩子/旧代码兼容，勿删；写入统一走 _set_xp_multiplier / toggle）
        self.game_state.test_xp_multiplier = self.test_handler.state.xp_multiplier
        self.game_state.test_auto_spawn = self.test_handler.state.auto_spawn

        self.orbs = pygame.sprite.Group()

        # 输入框使用 TEXTINPUT 事件（与主菜单一致）；BaseGame 构造时已 stop+blocked，此处放开
        pygame.key.start_text_input()
        pygame.event.set_allowed(pygame.TEXTINPUT)

    # ------------------------------------------------------------ 事件钩子

    def _handle_pre_event(self, event):
        """文本输入（输入框激活时吞掉所有事件；TEXTINPUT 收集与主菜单一致）"""
        state = self.test_handler.state
        if state.active_input_field is None:
            return False
        if event.type == pygame.TEXTINPUT:
            self.test_handler.apply_text_input(event.text)
            return True
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.test_handler.deactivate_input()
            elif event.key == pygame.K_BACKSPACE:
                self.test_handler.backspace_input()
            # K_MINUS 等忽略
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 点击输入框外取消输入（并吞掉事件，避免误触下方按钮）
            layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT,
                                       state.enemy_panel_expanded, state.boss_panel_expanded)
            input_rects = [layout["custom_enemy"][k]
                           for k in ("hp_input", "damage_input", "speed_input")]
            if not any(r.collidepoint(event.pos) for r in input_rects):
                self.test_handler.deactivate_input()
            return True
        return True

    def _handle_mode_click_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_test_mode_click(event.pos)

    def _handle_test_mode_click(self, pos):
        """处理测试模式面板点击（按面板分区分发，rect 全部来自单一布局）"""
        state = self.test_handler.state
        layout = build_test_layout(SCREEN_WIDTH, SCREEN_HEIGHT,
                                   state.enemy_panel_expanded, state.boss_panel_expanded)

        # 玩家控制区
        if self._handle_player_zone_click(pos, layout):
            return
        # 面板折叠/展开
        if layout["enemy_toggle"].collidepoint(pos):
            self.test_handler.toggle_enemy_panel()
            return
        if layout["boss_toggle"].collidepoint(pos):
            self.test_handler.toggle_boss_panel()
            return
        # 自定义敌生成区
        if self._handle_custom_enemy_zone_click(pos, layout):
            return
        # 技能区
        if self._handle_skill_zone_click(pos, layout):
            return
        # 敌种快速生成区（展开时）
        if self._handle_quick_spawn_click(pos, layout):
            return
        # 自动生成开关
        if layout["auto_spawn"].collidepoint(pos):
            self._toggle_auto_spawn()
            return
        # Boss 区（展开时）
        if self._handle_boss_zone_click(pos, layout):
            return
        # 调试区
        if layout["debug_stats"].collidepoint(pos):
            self.test_handler.toggle_debug_stats()

    # ---------------- 分区点击处理 ----------------

    def _handle_player_zone_click(self, pos, layout):
        state = self.test_handler.state
        r = layout["player"]
        if r["hp_minus"].collidepoint(pos):
            state.custom_hp = max(1, state.custom_hp - 1)
        elif r["hp_plus"].collidepoint(pos):
            state.custom_hp += 1
        elif r["hp_apply"].collidepoint(pos):
            self.game_state.player_hp = max(1, min(state.custom_hp, state.custom_max_hp))
        elif r["max_hp_minus"].collidepoint(pos):
            state.custom_max_hp = max(1, state.custom_max_hp - 1)
        elif r["max_hp_plus"].collidepoint(pos):
            state.custom_max_hp += 1
        elif r["max_hp_apply"].collidepoint(pos):
            self.game_state.stats["max_hp"] = state.custom_max_hp
            self.game_state.player_hp = min(self.game_state.player_hp, state.custom_max_hp)
        elif r["xp_minus"].collidepoint(pos):
            self._set_xp_multiplier(max(0.0, state.xp_multiplier - 0.5))
        elif r["xp_plus"].collidepoint(pos):
            self._set_xp_multiplier(min(10.0, state.xp_multiplier + 0.5))
        elif r["xp_apply"].collidepoint(pos):
            # BUG 修正：旧逻辑把倍率清零；改为"应用当前值"语义（+/- 已实时改值，此处确认提交）
            self._set_xp_multiplier(state.xp_multiplier)
        elif r["full_hp"].collidepoint(pos):
            self.game_state.player_hp = self.game_state.stats.get("max_hp", PLAYER_MAX_HP)
        elif r["add_xp_100"].collidepoint(pos):
            self.game_state.experience += 100
        elif r["add_xp_500"].collidepoint(pos):
            self.game_state.experience += 500
        elif r["upgrade_toggle"].collidepoint(pos):
            self.test_handler.toggle_level_up()
        elif r["reset"].collidepoint(pos):
            # 重置：复用 BaseGame._restart（重开当前局，重建 GameState/实体/test_handler）
            self._restart()
        else:
            return False
        return True

    def _handle_custom_enemy_zone_click(self, pos, layout):
        state = self.test_handler.state
        r = layout["custom_enemy"]
        for i, definition in enumerate(ENEMY_TYPE_DEFS):
            if r[f"type_{i}"].collidepoint(pos):
                self.test_handler.set_custom_enemy_type(i)
                return True
        if r["hp_minus"].collidepoint(pos):
            state.custom_hp = max(1, state.custom_hp - 1)
        elif r["hp_plus"].collidepoint(pos):
            state.custom_hp += 1
        elif r["hp_input"].collidepoint(pos):
            self.test_handler.activate_input(TestInputField.HP)
        elif r["damage_minus"].collidepoint(pos):
            state.custom_damage = max(1, state.custom_damage - 1)
        elif r["damage_plus"].collidepoint(pos):
            state.custom_damage += 1
        elif r["damage_input"].collidepoint(pos):
            self.test_handler.activate_input(TestInputField.DAMAGE)
        elif r["speed_minus"].collidepoint(pos):
            state.custom_speed = max(10, state.custom_speed - 10)
        elif r["speed_plus"].collidepoint(pos):
            state.custom_speed += 10
        elif r["speed_input"].collidepoint(pos):
            self.test_handler.activate_input(TestInputField.SPEED)
        elif r["spawn"].collidepoint(pos):
            definition = ENEMY_TYPE_DEFS[state.custom_enemy_type]
            self.test_handler.spawn_custom_enemy_with_type(
                self.enemies, self.player, definition["key"],
                state.custom_hp, state.custom_speed, state.custom_damage, game=self)
        else:
            return False
        return True

    def _handle_skill_zone_click(self, pos, layout):
        for i, rect in enumerate(layout["skill"]):
            if rect.collidepoint(pos):
                skill = SKILL_POOL[i]
                self.test_handler.handle_skill_click(
                    skill, self.game_state.stats, self.player, self.blade_mgr,
                    character=self.game_state.character)
                self.game_state.acquired_skills.append(skill["name"])
                return True
        return False

    def _handle_quick_spawn_click(self, pos, layout):
        if not self.test_handler.state.enemy_panel_expanded:
            return False
        for i, rect in enumerate(layout["enemy"]):
            if rect.collidepoint(pos) and i < len(ENEMY_TYPE_DEFS):
                self.test_handler.spawn_enemy_near_player(
                    ENEMY_TYPE_DEFS[i]["key"], self.enemies, self.player, game=self)
                return True
        return False

    def _handle_boss_zone_click(self, pos, layout):
        if not self.test_handler.state.boss_panel_expanded:
            return False
        for i, rect in enumerate(layout["boss"]):
            if rect.collidepoint(pos):
                if i < len(BOSS_CONFIGS):
                    boss = self.test_handler.spawn_boss_near_player(i, self.player)
                    if boss:
                        self.enemies.add(boss)
                        self.bosses.add(boss)
                        self.game_state.boss_active = True
                else:
                    self._clear_test_enemies()
                return True
        return False

    # ---------------- 状态同步 ----------------

    def _set_xp_multiplier(self, value):
        """经验倍率单一源：handler.state.xp_multiplier；game_state 镜像同步。"""
        self.test_handler.state.xp_multiplier = value
        self.game_state.test_xp_multiplier = value

    def _toggle_auto_spawn(self):
        """自动生成开关单一源：handler.state.auto_spawn；game_state 镜像同步。"""
        self.test_handler.toggle_auto_spawn()
        self.game_state.test_auto_spawn = self.test_handler.state.auto_spawn

    def _clear_test_enemies(self):
        """清屏：清除所有非 Boss 敌人（保留 Boss）。"""
        for enemy in list(self.enemies):
            if not isinstance(enemy, Boss):
                enemy.kill()

    # ------------------------------------------------------------ 更新管线钩子

    def _check_level_up(self):
        """升级豁免（DN-ENG-TEST-R2）：默认 allow_level_up=False 不升级（经验照常显示，不弹窗不冻结）。

        升级弹窗冻结是用户实测"测试模式不能移动"根因（升级 → paused=True + 3选1）。
        关闭时直接 return；开启后走 BaseGame 原逻辑。
        """
        if not self.test_handler.state.allow_level_up:
            return
        super()._check_level_up()

    def _should_spawn_auto(self):
        # 测试模式下受 auto_spawn 开关控制（单一源）
        return self.test_handler.should_spawn_enemies(True)

    def _xp_mult(self):
        return self.test_handler.state.xp_multiplier

    # ------------------------------------------------------------ 刷怪 / 数值钩子

    def _enemy_type_hp(self, enemy_type):
        return {"charger": 50, "ranger": 30, "exploder": 20,
                "wraith": 3, "warlock": 2}[enemy_type]

    def _roll_elite(self, x, y, tier, hp_bonus, damage_bonus):
        if self.game_state.elapsed_time >= 120 and random.random() < 0.05:
            return Enemy(x, y, hp=ELITE_HP + hp_bonus, speed=ELITE_SPEED,
                         size=ELITE_SIZE, color=BLUE, is_elite=True, sprite_name="elite")
        return None

    def _spawn_special_enemy(self, enemy_type, x, y):
        if enemy_type == "shadow":
            return Enemy(x, y, hp=SHADOW_MAGE_SHADOW_HP, speed=ENEMY_SPEED,
                         size=ENEMY_SIZE, color=(100, 0, 150), contact_damage=SHADOW_MAGE_SHADOW_DAMAGE)
        if enemy_type == "voidling":
            return Enemy(x, y, hp=VOID_LORD_VOIDLING_HP, speed=ENEMY_SPEED * 1.2,
                         size=ENEMY_SIZE, color=(180, 0, 200), contact_damage=VOID_LORD_VOIDLING_DAMAGE)
        return None

    # ------------------------------------------------------------ 战斗反馈钩子

    def _apply_hit_feedback(self, enemy, bullet, is_crit):
        # 仅暴击时朝远离玩家的方向击退
        if is_crit:
            dx = enemy.rect.centerx - self.player.rect.centerx
            dy = enemy.rect.centery - self.player.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                enemy.rect.x += (dx / dist) * 12
                enemy.rect.y += (dy / dist) * 12

    # ------------------------------------------------------------ Boss 钩子

    def _clear_enemies_for_boss(self):
        # 测试模式：清场走 _kill_enemy（保留经验/掉落/复苏之风奖励）
        for enemy in list(self.enemies):
            if not isinstance(enemy, Boss):
                self._kill_enemy(enemy)

    # ------------------------------------------------------------ 渲染钩子

    def _render_mode_entities(self):
        for orb in self.orbs:
            self.screen.blit(orb.image, self.camera.apply(orb.rect))

    def _render_mode_overlays(self, mouse_pos):
        # 测试模式面板
        if not self.game_state.paused and not self.game_state.game_over and not self.game_state.escaped:
            enemy_stats = self._get_current_enemy_stats()
            draw_test_mode_panel(self.screen, self.font, mouse_pos,
                                 self.test_handler.state, enemy_stats)

    def _render_tail(self, mouse_pos):
        # 地图过渡
        if self.map_manager.transition_active:
            self._render_map_transition()
        # ESC 暂停菜单
        if self.game_state.escaped:
            resume_rect, quit_rect = self._get_pause_menu_rects()
            draw_pause_menu(self.screen, self.big_font, self.font, mouse_pos)
        # 技能选择
        if self.game_state.paused and self.game_state.chosen_skills:
            draw_skill_selection(self.screen, self.big_font, self.font, self.game_state.chosen_skills,
                                 mouse_pos, self.game_state.acquired_skills, self.game_state.stats)
        # 游戏结束
        if self.game_state.game_over:
            draw_game_over_screen(self.screen, self.big_font, self.font,
                                  self.game_state.elapsed_time, self.game_state.score,
                                  self.game_state.level, self.high_score, self.new_record, self.is_victory)

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

    def _window_title(self):
        player_dps = self.game_state.stats["bullet_damage"] * self.game_state.stats["bullet_count"] / self.game_state.stats["fire_interval"]
        time_str = f"{self.game_state.elapsed_time:.0f}s"
        bc = self.game_state.stats["bullet_count"]
        map_name = self.map_manager.map_data["name"]
        return f"[测试] 击杀:{self.game_state.score} | DPS:{player_dps:.0f} | {time_str} | {map_name} | 新星:{self.game_state.stats.get('has_blades', 0)}"
