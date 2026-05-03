"""黑暗之夜 - 主程序"""
import sys
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK,
    SPAWN_INTERVAL, ENEMY_SIZE, ENEMY_HP, MAX_ENEMIES,
    ELITE_SIZE, ELITE_SPEED, ELITE_HP,
    ELITE_CHANCE, ELITE_ACTIVATION, ELITE_HP_MULT, ELITE_DAMAGE_MULT,
    CHARGER_HP, RANGER_HP, EXPLODER_HP,
    DIFFICULTY_INTERVAL, SPAWN_RATE_FACTOR, HP_BONUS_PER_TIER, DAMAGE_BONUS_PER_TIER,
    GROWTH_INTERVAL, XP_BONUS_PER_GROWTH, XP_GROWTH_INTERVAL,
    FIRE_INTERVAL, MAP_WIDTH, MAP_HEIGHT, XP_PER_ORB, XP_BASE, XP_DIFF_INCREMENT,
    PLAYER_SPEED, PLAYER_MAX_HP, PLAYER_INVINCIBLE_TIME,
    PICKUP_RANGE, CRIT_MULTIPLIER,
    WHITE, GRAY, DARK_GRAY, GOLD, BLUE, RED, GREEN,
    GAME_DURATION
)

# 游戏实体
from entities import Player, Enemy, Charger, Ranger, Exploder, Bullet, EnemyBullet
from entities import XpOrb, Particle, DamageNumber, Explosion, TrapManager
from effects import OrbitalBladeManager, ChainLightning
from systems import Camera, AudioManager, load_high_score, save_high_score
from skills import get_random_skills, apply_skill, SKILL_POOL

# UI模块
from ui import (
    draw_hud, draw_skill_bar, draw_start_screen,
    draw_game_over_screen, draw_skill_selection,
    draw_test_mode_panel, get_test_skill_rects,
    get_test_enemy_rects, get_test_auto_spawn_rect,
    get_font
)

# 游戏逻辑模块
from game import GameState, TestModeHandler


# ==================== 经验计算函数 ====================

def get_xp_for_level(level):
    """计算升到指定等级需要的累计经验值

    1-30级: 等差数列增长
    30级后: 每级所需经验 × 1.1 (指数增长)
    """
    if level <= 1:
        return 0
    if level == 2:
        return XP_BASE

    total = XP_BASE  # 1→2级需要的经验

    for l in range(3, min(level + 1, 31)):  # 1-30级用等差数列
        block_idx = (l - 2) // 10
        position = (l - 2) % 10
        level_increment = XP_BASE + block_idx * 10 + position * (XP_DIFF_INCREMENT - 3 + block_idx * XP_DIFF_INCREMENT)
        total += level_increment

    # 30级后用指数增长：每级所需经验 × 1.1
    if level > 30:
        # 30级升31级所需经验
        last_needed = get_xp_for_level(30) - get_xp_for_level(29)
        for l in range(31, level + 1):
            last_needed = int(last_needed * 1.1)
            total += last_needed

    return total


def get_level_from_xp(total_xp):
    """根据累计经验值计算当前等级"""
    level = 1
    while get_xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


# ==================== 辅助函数 ====================

_ENEMY_TYPES = ["basic", "charger", "ranger", "exploder"]
_ENEMY_UNLOCK_TIER = {"basic": 0, "charger": 1, "ranger": 2, "exploder": 3}
_ENEMY_WEIGHTS = {"basic": 1.0, "charger": 0.4, "ranger": 0.35, "exploder": 0.2}


def _spawn_pos(camera):
    left = int(camera.offset.x)
    top = int(camera.offset.y)
    side = random.randint(0, 3)
    if side == 0:
        return (random.randint(left, left + SCREEN_WIDTH), top - ENEMY_SIZE)
    elif side == 1:
        return (random.randint(left, left + SCREEN_WIDTH), top + SCREEN_HEIGHT)
    elif side == 2:
        return (left - ENEMY_SIZE, random.randint(top, top + SCREEN_HEIGHT))
    else:
        return (left + SCREEN_WIDTH, random.randint(top, top + SCREEN_HEIGHT))


def _spawn_enemy(camera, elapsed_time, difficulty_level):
    x, y = _spawn_pos(camera)
    # 每50秒触发一次成长，使用等差数列求和：+1, +2, +3... (1+2+...+n = n*(n+1)/2)
    growth_count = int(elapsed_time / GROWTH_INTERVAL)
    total_bonus = growth_count * (growth_count + 1) // 2  # 等差数列求和
    hp_bonus = total_bonus
    damage_bonus = total_bonus
    tier = int(elapsed_time / DIFFICULTY_INTERVAL)

    available = [(t, w) for t, w in _ENEMY_WEIGHTS.items()
                 if _ENEMY_UNLOCK_TIER[t] <= tier]
    if not available:
        available = [("basic", 1.0)]
    types, weights = zip(*available)
    enemy_type = random.choices(types, weights=weights, k=1)[0]

    if enemy_type == "charger":
        return Charger(x, y, hp=CHARGER_HP + hp_bonus, damage=1 + damage_bonus)
    elif enemy_type == "ranger":
        return Ranger(x, y, hp=RANGER_HP + hp_bonus, damage=1 + damage_bonus)
    elif enemy_type == "exploder":
        explosion_dmg = (1 + damage_bonus) * 2  # 自爆伤害 = 普通怪接触伤害 × 2
        return Exploder(x, y, hp=EXPLODER_HP + hp_bonus, damage=0, explosion_damage=explosion_dmg)

    if elapsed_time >= ELITE_ACTIVATION and random.random() < ELITE_CHANCE:
        elite_hp = int((ELITE_HP + hp_bonus) * ELITE_HP_MULT)
        return Enemy(x, y, hp=elite_hp, speed=ELITE_SPEED,
                     size=ELITE_SIZE, color=BLUE, is_elite=True,
                     sprite_name="elite", contact_damage=int((1 + damage_bonus) * ELITE_DAMAGE_MULT))
    return Enemy(x, y, hp=ENEMY_HP + hp_bonus, contact_damage=1 + damage_bonus)


def _nearest_enemy(player_rect, enemies):
    best = None
    best_dist = float("inf")
    for enemy in enemies:
        dist = player_rect.centerx - enemy.rect.centerx
        dist = dist * dist + (player_rect.centery - enemy.rect.centery) ** 2
        if dist < best_dist:
            best_dist = dist
            best = enemy
    return best


def _kill_enemy(enemy, particles, orbs, explosions, score, audio=None, fps=60):
    count = max(1, int(random.randint(5, 8) * min(1.0, fps / 55.0)))
    for _ in range(count):
        particles.add(Particle(enemy.rect.centerx, enemy.rect.centery, enemy._base_color))
    if enemy.is_elite:
        xp_gained = 3
    elif isinstance(enemy, Exploder):
        explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, enemy.explosion_damage))
        xp_gained = 1
    else:
        xp_gained = 1
    if audio:
        audio.play_enemy_death()
    return score + 1, xp_gained


def _handle_player_damage(player_hp, damage, invincible_timer, damage_taken):
    if invincible_timer <= 0:
        return (player_hp - damage * damage_taken, PLAYER_INVINCIBLE_TIME, True)
    return (player_hp, invincible_timer, False)


def _calc_player_dps(stats):
    return stats["bullet_damage"] * stats["bullet_count"] / stats["fire_interval"]


# ==================== 主程序 ====================

def main():
    pygame.init()
    pygame.key.stop_text_input()
    pygame.event.set_blocked(pygame.TEXTINPUT)
    pygame.event.set_blocked(pygame.TEXTEDITING)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("暗夜求生  |  F11 全屏")
    clock = pygame.time.Clock()
    audio = AudioManager()
    audio.start_music()

    # 初始化游戏状态
    game_state = GameState()
    test_handler = TestModeHandler()

    font = get_font(24)
    big_font = get_font(48)
    dmg_font = get_font(16)

    # 实体对象
    player = Player()
    camera = Camera()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    orbs = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    damage_numbers = []
    explosions = []
    blade_mgr = OrbitalBladeManager()
    chain_lightning = ChainLightning()
    trap_mgr = TrapManager()

    fullscreen = False
    high_score = load_high_score()
    new_record = False

    # FPS跟踪
    fps_smooth = 60.0
    fps_display = "60"

    while True:
        dt = clock.tick(FPS) / 1000.0
        fps_raw = 1.0 / dt if dt > 0 else 60.0
        fps_smooth = fps_smooth * 0.95 + fps_raw * 0.05
        fps_display = f"{fps_smooth:.0f}"
        mouse_pos = pygame.mouse.get_pos()

        # ==================== 事件处理 ====================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 菜单状态
            if game_state.menu:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_state.menu = False
                # 测试模式快捷键 T
                if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                    game_state.menu = False
                    game_state.test_mode = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    btn_rect = pygame.Rect(
                        (SCREEN_WIDTH - 220) // 2, SCREEN_HEIGHT - 100, 220, 50)
                    if btn_rect.collidepoint(event.pos):
                        game_state.menu = False
                    # 测试模式按钮
                    test_btn_rect = pygame.Rect(
                        (SCREEN_WIDTH - 220) // 2, SCREEN_HEIGHT - 160, 220, 45)
                    if test_btn_rect.collidepoint(event.pos):
                        game_state.menu = False
                        game_state.test_mode = True
                continue

            # 游戏结束状态
            if game_state.game_over:
                do_restart = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    do_restart = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    btn_rect = pygame.Rect(
                        (SCREEN_WIDTH - 240) // 2, SCREEN_HEIGHT - 120, 240, 50)
                    if btn_rect.collidepoint(event.pos):
                        do_restart = True
                if do_restart:
                    game_state.reset()
                    player = Player()
                    camera = Camera()
                    enemies = pygame.sprite.Group()
                    bullets = pygame.sprite.Group()
                    enemy_bullets = pygame.sprite.Group()
                    orbs = pygame.sprite.Group()
                    particles = pygame.sprite.Group()
                    damage_numbers = []
                    explosions = []
                    trap_mgr = TrapManager()
                    blade_mgr = OrbitalBladeManager()
                    chain_lightning = ChainLightning()
                    high_score = load_high_score()
                    new_record = False
                continue

            # 技能选择
            if game_state.paused and game_state.chosen_skills:
                from ui.skill_select import build_card_rects
                if event.type == pygame.KEYDOWN:
                    idx = -1
                    if event.key == pygame.K_1:
                        idx = 0
                    elif event.key == pygame.K_2:
                        idx = 1
                    elif event.key == pygame.K_3:
                        idx = 2
                    if 0 <= idx < len(game_state.chosen_skills):
                        skill = game_state.chosen_skills[idx]
                        apply_skill(game_state.stats, skill)
                        game_state.apply_skill_update(skill, player, blade_mgr)
                        game_state.chosen_skills = None
                        game_state.paused = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    card_rects = build_card_rects(len(game_state.chosen_skills), SCREEN_WIDTH, SCREEN_HEIGHT)
                    for i, rect in enumerate(card_rects):
                        if rect.collidepoint(event.pos):
                            skill = game_state.chosen_skills[i]
                            apply_skill(game_state.stats, skill)
                            game_state.apply_skill_update(skill, player, blade_mgr)
                            game_state.chosen_skills = None
                            game_state.paused = False
                            break

            # 测试模式点击
            if game_state.test_mode and event.type == pygame.MOUSEBUTTONDOWN:
                # 技能面板点击
                skill_rects = get_test_skill_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
                for i, skill in enumerate(SKILL_POOL):
                    if skill_rects[i].collidepoint(event.pos):
                        test_handler.handle_skill_click(skill, game_state.stats, player, blade_mgr)
                        game_state.acquired_skills.append(skill["name"])
                        break

                # 敌人生成点击
                enemy_rects = get_test_enemy_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
                for i, enemy_rect in enumerate(enemy_rects):
                    if enemy_rect.collidepoint(event.pos) and i < len(_ENEMY_TYPES):
                        test_handler.spawn_enemy_near_player(_ENEMY_TYPES[i], enemies, player)
                        break

                # 自动生成开关
                auto_rect = get_test_auto_spawn_rect(SCREEN_WIDTH, SCREEN_HEIGHT)
                if auto_rect.collidepoint(event.pos):
                    test_handler.toggle_auto_spawn()
                    game_state.test_auto_spawn = test_handler.auto_spawn

            # 常规按键
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        # ==================== 游戏逻辑更新 ====================
        if not game_state.menu and not game_state.paused and not game_state.game_over:
            game_state.elapsed_time += dt
            if game_state.invincible_timer > 0:
                game_state.invincible_timer -= dt

            game_state.difficulty_level = int(game_state.elapsed_time / DIFFICULTY_INTERVAL)
            # 刷新间隔随时间放缓（使用更温和的衰减曲线）
            time_factor = game_state.elapsed_time / 30  # 拉长时间常数
            current_spawn_interval = SPAWN_INTERVAL / (1 + time_factor * 0.5 + (time_factor * 0.3) ** 2)

            keys = pygame.key.get_pressed()
            player.update(dt, keys)
            camera.update(player.rect, dt)

            is_moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d] or keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]

            # 生成敌人（添加上限防止卡顿）
            game_state.spawn_timer += dt
            while game_state.spawn_timer >= current_spawn_interval:
                game_state.spawn_timer -= current_spawn_interval
                if len(enemies) < MAX_ENEMIES and test_handler.should_spawn_enemies(game_state.test_mode):
                    enemies.add(_spawn_enemy(camera, game_state.elapsed_time, game_state.difficulty_level))

            # 自动射击
            game_state.fire_timer += dt
            while game_state.fire_timer >= game_state.stats["fire_interval"] and enemies:
                game_state.fire_timer -= game_state.stats["fire_interval"]
                target = _nearest_enemy(player.rect, enemies)
                if target:
                    bullet_count = game_state.stats["bullet_count"]
                    dx = target.rect.centerx - player.rect.centerx
                    dy = target.rect.centery - player.rect.centery
                    base_angle = math.atan2(dy, dx)
                    spread = 0.26
                    for i in range(bullet_count):
                        offset = spread * (i - (bullet_count - 1) / 2) if bullet_count > 1 else 0
                        angle = base_angle + offset
                        tx = player.rect.centerx + math.cos(angle) * 100
                        ty = player.rect.centery + math.sin(angle) * 100
                        bullets.add(Bullet(player.rect.centerx, player.rect.centery, (tx, ty)))
                audio.play_shoot()

            # 更新实体
            enemies.update(dt, player.rect)
            bullets.update(dt)
            enemy_bullets.update(dt)

            # 武器系统 - 旋转利刃
            if game_state.stats.get("has_blades", 0) > 0:
                blade_mgr.update(dt)
                blade_hits = blade_mgr.check_damage(player.rect, enemies, dt, game_state.stats)
                for enemy, dmg, dead in blade_hits:
                    damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), dmg_font))
                    if dead:
                        score, xp = _kill_enemy(enemy, particles, orbs, explosions, game_state.score, audio, fps_smooth)
                        game_state.score = score
                        game_state.experience += xp
                        enemy.kill()

            # 连锁闪电
            if game_state.stats.get("has_lightning", 0) > 0:
                lightning_hits = chain_lightning.update(dt, player.rect, enemies, game_state.stats)
                for enemy, dmg, dead in lightning_hits:
                    damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), dmg_font))
                    if dead:
                        score, xp = _kill_enemy(enemy, particles, orbs, explosions, game_state.score, audio, fps_smooth)
                        game_state.score = score
                        game_state.experience += xp
                        enemy.kill()

            # 剧毒地雷 - 根据游戏时间自动释放
            if game_state.stats.get("has_traps", 0) > 0:
                trap_interval = game_state.stats.get("trap_interval", 2.0)
                trap_mgr.update(dt, player, trap_interval,
                              trap_damage=game_state.stats.get("trap_damage", 4),
                              radius_mult=game_state.stats.get("trap_radius_mult", 1.0))
                for trap in list(trap_mgr.group):
                    trap.check_enemies(enemies)

            # 持续伤害死亡检查
            for enemy in list(enemies):
                if enemy.hp <= 0:
                    score, xp = _kill_enemy(enemy, particles, orbs, explosions, game_state.score, audio, fps_smooth)
                    game_state.score = score
                    game_state.experience += xp
                    enemy.kill()

            # 射手开火
            for enemy in list(enemies):
                if isinstance(enemy, Ranger) and enemy.wants_to_fire():
                    enemy_bullets.add(EnemyBullet(
                        enemy.rect.centerx, enemy.rect.centery,
                        player.rect.centerx, player.rect.centery))

            # 离屏清理
            for bullet in list(bullets):
                if not (0 <= bullet.rect.centerx <= MAP_WIDTH and 0 <= bullet.rect.centery <= MAP_HEIGHT):
                    bullet.kill()
            for eb in list(enemy_bullets):
                if not (0 <= eb.rect.centerx <= MAP_WIDTH and 0 <= eb.rect.centery <= MAP_HEIGHT):
                    eb.kill()

            # 子弹碰撞
            hits = pygame.sprite.groupcollide(bullets, enemies, False, False)
            for bullet, hit_enemies in hits.items():
                bullet.kill()
                for enemy in hit_enemies:
                    dmg = game_state.stats["bullet_damage"]
                    is_crit = random.random() < game_state.stats["crit_chance"]
                    if is_crit:
                        dmg *= game_state.stats["crit_multiplier"]
                        kx = enemy.rect.centerx - player.rect.centerx
                        ky = enemy.rect.centery - player.rect.centery
                        kdist = math.hypot(kx, ky)
                        if kdist > 0:
                            enemy.rect.x += (kx / kdist) * 12
                            enemy.rect.y += (ky / kdist) * 12

                    dead = enemy.take_damage(dmg)
                    damage_numbers.append(DamageNumber(enemy.rect.centerx, enemy.rect.top, int(dmg), dmg_font))

                    if dead:
                        score, xp = _kill_enemy(enemy, particles, orbs, explosions, game_state.score, audio, fps_smooth)
                        game_state.score = score
                        game_state.experience += xp
                        enemy.kill()
                        # 复苏之风逻辑
                        if game_state.stats.get("regen_kills", 0) > 0:
                            required_kills = game_state.stats["regen_kills"]
                            game_state.stats["regen_kills_progress"] += 1
                            if game_state.stats["regen_kills_progress"] >= required_kills:
                                game_state.stats["regen_kills_progress"] = 0
                                game_state.player_hp = min(game_state.stats["max_hp"], game_state.player_hp + 1)
                    break

            # 敌人子弹碰撞
            if game_state.invincible_timer <= 0:
                for eb in list(enemy_bullets):
                    if eb.rect.colliderect(player.rect):
                        game_state.player_hp, game_state.invincible_timer, _ = _handle_player_damage(
                            game_state.player_hp, eb.damage, game_state.invincible_timer, game_state.stats["damage_taken"])
                        camera.shake(0.12, 5)
                        eb.kill()
                        break

            # 敌人接触
            if game_state.invincible_timer <= 0:
                for enemy in list(enemies):
                    if enemy.rect.colliderect(player.rect) and enemy.contact_damage > 0:
                        game_state.player_hp, game_state.invincible_timer, _ = _handle_player_damage(
                            game_state.player_hp, enemy.contact_damage, game_state.invincible_timer, game_state.stats["damage_taken"])
                        camera.shake(0.15, 6)
                        kx = enemy.rect.centerx - player.rect.centerx
                        ky = enemy.rect.centery - player.rect.centery
                        kdist = math.hypot(kx, ky)
                        if kdist > 0:
                            enemy.rect.x += (kx / kdist) * 30
                            enemy.rect.y += (ky / kdist) * 30
                        break

            # 爆炸
            for exp in explosions:
                exp.update(dt)
                if not exp._applied:
                    player_hit = exp.apply_damage(player, enemies)
                    if player_hit and game_state.invincible_timer <= 0:
                        game_state.player_hp, game_state.invincible_timer, _ = _handle_player_damage(
                            game_state.player_hp, exp.damage, game_state.invincible_timer, game_state.stats["damage_taken"])
                for enemy in list(enemies):
                    if enemy.hp <= 0:
                        score, xp = _kill_enemy(enemy, particles, orbs, explosions, game_state.score, audio, fps_smooth)
                        game_state.score = score
                        game_state.experience += xp
                        enemy.kill()
            explosions = [e for e in explosions if e.alive]

            # 经验球（仅用于视觉和吸引，经验在击杀时直接获得）
            for orb in list(orbs):
                orb.update(dt, player.rect, game_state.stats["pickup_range"])
                if orb.rect.colliderect(player.rect):
                    orb.kill()

            # 粒子和伤害数字
            particles.update(dt)
            for dn in damage_numbers[:]:
                dn.update(dt)
                if not dn.alive:
                    damage_numbers.remove(dn)

            # 升级
            xp_for_current = get_xp_for_level(game_state.level)
            xp_for_next = get_xp_for_level(game_state.level + 1)
            xp_to_next = xp_for_next - xp_for_current
            if game_state.experience >= xp_to_next:
                game_state.experience -= xp_to_next
                game_state.level += 1
                game_state.paused = True
                game_state.chosen_skills = get_random_skills(3)
                # 每次升级增加血量上限和当前血量
                game_state.stats["max_hp"] += 1
                game_state.player_hp = min(game_state.player_hp + 1, game_state.stats["max_hp"])
                player.max_hp = game_state.stats["max_hp"]
                audio.play_level_up()

            # 胜利检查（10分钟到达）
            if game_state.elapsed_time >= GAME_DURATION:
                game_state.game_over = True
                new_record = save_high_score(game_state.score)
                if new_record:
                    high_score = game_state.score
                is_victory = True
            else:
                is_victory = False

            # 死亡检查
            if game_state.player_hp <= 0:
                game_state.game_over = True
                new_record = save_high_score(game_state.score)
                if new_record:
                    high_score = game_state.score
                is_victory = False

        # ==================== 渲染 ====================
        if game_state.menu:
            draw_start_screen(screen, big_font, font, font)
        else:
            screen.fill(BLACK)
            camera.draw_grid(screen)

            # 毒圈
            if game_state.stats.get("has_traps", 0) > 0:
                for trap in trap_mgr.group:
                    screen.blit(trap.image, camera.apply(trap.rect))

            # 实体
            player.draw(screen, camera)
            for enemy in enemies:
                screen.blit(enemy.image, camera.apply(enemy.rect))
            for bullet in bullets:
                screen.blit(bullet.image, camera.apply(bullet.rect))
            for eb in enemy_bullets:
                screen.blit(eb.image, camera.apply(eb.rect))
            for orb in orbs:
                screen.blit(orb.image, camera.apply(orb.rect))
            for particle in particles:
                screen.blit(particle.image, camera.apply(particle.rect))

            # 武器特效
            if game_state.stats.get("has_blades", 0) > 0:
                blade_mgr.draw(screen, camera, player.rect)
            if game_state.stats.get("has_lightning", 0) > 0:
                chain_lightning.draw(screen, camera)

            # 爆炸和伤害数字
            for exp in explosions:
                exp.draw(screen, camera)
            for dn in damage_numbers:
                dn.draw(screen, camera)

            # HUD
            xp_for_current = get_xp_for_level(game_state.level)
            xp_for_next = get_xp_for_level(game_state.level + 1)
            xp_to_next = xp_for_next - xp_for_current
            current_max_hp = game_state.stats.get("max_hp", PLAYER_MAX_HP)
            draw_hud(screen, font, game_state.level, game_state.experience, xp_to_next,
                      game_state.player_hp, current_max_hp, game_state.elapsed_time)
            draw_skill_bar(screen, font, game_state.acquired_skills, mouse_pos, game_state.elapsed_time, game_state.stats)

            # 测试模式面板
            if game_state.test_mode and not game_state.paused and not game_state.game_over:
                draw_test_mode_panel(screen, font, game_state.acquired_skills, mouse_pos, game_state.test_auto_spawn)

            # 技能选择
            if game_state.paused and game_state.chosen_skills:
                draw_skill_selection(screen, big_font, font, game_state.chosen_skills, mouse_pos,
                                    game_state.acquired_skills, game_state.stats)

            # 游戏结束
            if game_state.game_over:
                draw_game_over_screen(screen, big_font, font, game_state.elapsed_time, game_state.score,
                                     game_state.level, high_score, new_record, is_victory)

            # FPS
            fps_color = GREEN if fps_smooth >= 55 else (RED if fps_smooth < 30 else GOLD)
            fps_text = font.render(fps_display, True, fps_color)
            screen.blit(fps_text, (screen.get_width() - fps_text.get_width() - 8, 8))

            # 标题栏
            player_dps = _calc_player_dps(game_state.stats)
            time_str = f"{game_state.elapsed_time:.0f}s"
            bc = game_state.stats["bullet_count"]
            title = f"击杀:{game_state.score} | DPS:{player_dps:.0f} | {time_str} | 难度{game_state.difficulty_level} | 刀:{bc+1}"
            pygame.display.set_caption(title)

        pygame.display.flip()


if __name__ == "__main__":
    main()
