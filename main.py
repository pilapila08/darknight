import sys
import math
import random
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK,
                      SPAWN_INTERVAL, ENEMY_SIZE, ENEMY_HP,
                      ELITE_SIZE, ELITE_SPEED, ELITE_HP,
                      ELITE_CHANCE, ELITE_ACTIVATION,
                      CHARGER_HP, RANGER_HP, EXPLODER_HP,
                      EXPLODER_RADIUS, EXPLODER_DAMAGE,
                      DIFFICULTY_INTERVAL, SPAWN_RATE_FACTOR, HP_BONUS_PER_TIER,
                      FIRE_INTERVAL, MAP_WIDTH, MAP_HEIGHT, XP_PER_ORB, XP_PER_LEVEL,
                      PLAYER_SPEED, PLAYER_MAX_HP, PLAYER_INVINCIBLE_TIME,
                      PICKUP_RANGE, CRIT_MULTIPLIER, REGEN_KILLS, FROSTBITE_SLOW,
                      WHITE, GRAY, DARK_GRAY, GOLD, BLUE, RED, GREEN)
from player import Player
from camera import Camera
from enemy import Enemy
from enemy_types import Charger, Ranger, Exploder
from bullet import Bullet
from enemy_bullet import EnemyBullet
from xp_orb import XpOrb
from particle import Particle
from damage_number import DamageNumber
from explosion import Explosion
from orbital_blade import OrbitalBladeManager
from chain_lightning import ChainLightning
from acid_trap import TrapManager
from skills import get_random_skills, apply_skill
from audio_manager import AudioManager
from save_data import load_high_score, save_high_score


def _get_font(size):
    """Get a font that supports Chinese characters."""
    for name in ("microsoft yahei", "simhei", "simsun", "noto sans cjk sc",
                 "wenquanyi micro hei", "arial unicode ms", "ms gothic"):
        try:
            return pygame.font.SysFont(name, size)
        except Exception:
            continue
    return pygame.font.Font(None, size)


# --- Helpers ---

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
    hp_bonus = difficulty_level * HP_BONUS_PER_TIER
    tier = int(elapsed_time / DIFFICULTY_INTERVAL)

    available = [(t, w) for t, w in _ENEMY_WEIGHTS.items()
                 if _ENEMY_UNLOCK_TIER[t] <= tier]
    if not available:
        available = [("basic", 1.0)]
    types, weights = zip(*available)
    enemy_type = random.choices(types, weights=weights, k=1)[0]

    if enemy_type == "charger":
        return Charger(x, y, hp=CHARGER_HP + hp_bonus)
    elif enemy_type == "ranger":
        return Ranger(x, y, hp=RANGER_HP + hp_bonus)
    elif enemy_type == "exploder":
        return Exploder(x, y, hp=EXPLODER_HP + hp_bonus)

    if elapsed_time >= ELITE_ACTIVATION and random.random() < ELITE_CHANCE:
        return Enemy(x, y, hp=ELITE_HP + hp_bonus, speed=ELITE_SPEED,
                     size=ELITE_SIZE, color=BLUE, is_elite=True, sprite_name="elite")
    return Enemy(x, y, hp=ENEMY_HP + hp_bonus)


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
    """Handle enemy death: particles, orbs, explosions, score."""
    count = max(1, int(random.randint(5, 8) * min(1.0, fps / 55.0)))
    for _ in range(count):
        particles.add(Particle(enemy.rect.centerx, enemy.rect.centery,
                               enemy._base_color))
    if enemy.is_elite:
        orb_count = 3
    elif isinstance(enemy, Exploder):
        explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
        orb_count = 1
    else:
        orb_count = 1
    for _ in range(orb_count):
        orbs.add(XpOrb(enemy.rect.centerx, enemy.rect.centery))
    if audio:
        audio.play_enemy_death()
    return score + 1


def _handle_player_damage(player_hp, damage, invincible_timer, damage_taken):
    """Apply damage with multiplier, return (new_hp, new_invincible, took_damage)."""
    if invincible_timer <= 0:
        return (player_hp - damage * damage_taken, PLAYER_INVINCIBLE_TIME, True)
    return (player_hp, invincible_timer, False)


def _calc_player_dps(stats):
    return stats["bullet_damage"] * stats["bullet_count"] / stats["fire_interval"]


# --- UI ---

def _draw_ui(screen, font, level, experience, xp_to_next, player_hp, player_max_hp):
    sw = screen.get_width()
    bar_width = sw // 2
    bar_height = 14
    bar_x = (sw - bar_width) // 2

    xp_y = 8
    level_text = font.render(f"Lv.{level}", True, WHITE)
    screen.blit(level_text, (bar_x - 60, xp_y - 2))
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, xp_y, bar_width, bar_height))
    fill_width = int(bar_width * (experience / max(1, xp_to_next)))
    if fill_width > 0:
        pygame.draw.rect(screen, GOLD, (bar_x, xp_y, fill_width, bar_height))

    hp_y = xp_y + bar_height + 4
    hp_text = font.render("生命", True, WHITE)
    screen.blit(hp_text, (bar_x - 40, hp_y - 2))
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, hp_y, bar_width, bar_height))
    hp_fill = int(bar_width * (player_hp / player_max_hp))
    if hp_fill > 0:
        hp_color = RED if player_hp <= player_max_hp * 0.3 else GREEN
        pygame.draw.rect(screen, hp_color, (bar_x, hp_y, hp_fill, bar_height))


def _draw_skill_selection(screen, big_font, small_font, skills, mouse_pos):
    sw, sh = screen.get_width(), screen.get_height()
    # Heavier overlay for better contrast
    overlay = pygame.Surface((sw, sh))
    overlay.set_alpha(235)
    overlay.fill((5, 2, 15))
    screen.blit(overlay, (0, 0))

    # Title with decorative lines
    title = big_font.render("选 择 强 化", True, GOLD)
    title_rect = title.get_rect(center=(sw // 2, sh // 7))
    # Decorative lines
    line_w = sw // 5
    line_y = title_rect.centery
    pygame.draw.line(screen, (80, 60, 30), (title_rect.left - line_w - 20, line_y),
                     (title_rect.left - 20, line_y), 2)
    pygame.draw.line(screen, (80, 60, 30), (title_rect.right + 20, line_y),
                     (title_rect.right + line_w + 20, line_y), 2)
    screen.blit(title, title_rect)

    card_w, card_h = 420, 80
    card_x = (sw - card_w) // 2
    start_y = sh // 4 + 20
    gap = 14
    card_rects = []

    for i, skill in enumerate(skills):
        rect = pygame.Rect(card_x, start_y + i * (card_h + gap), card_w, card_h)
        card_rects.append(rect)
        hovered = rect.collidepoint(mouse_pos)

        # Shadow/glow behind card
        shadow = rect.inflate(6, 6)
        pygame.draw.rect(screen, (20, 15, 35), shadow, border_radius=6)

        # Card body
        if hovered:
            bg_color = (45, 35, 70)
            border_color = (255, 230, 100)
            border_w = 3
        else:
            bg_color = (20, 15, 35)
            border_color = (180, 140, 60)
            border_w = 2
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, border_w, border_radius=6)

        # Key hint badge (small circle/square in top-left)
        badge = pygame.Rect(rect.x + 10, rect.y + 10, 26, 26)
        pygame.draw.rect(screen, border_color, badge, border_radius=4)
        key_hint = small_font.render(str(i + 1), True, (10, 5, 20))
        key_rect = key_hint.get_rect(center=badge.center)
        screen.blit(key_hint, key_rect)

        # Skill name
        name = small_font.render(skill["name"], True, GOLD if hovered else WHITE)
        screen.blit(name, (rect.x + 48, rect.y + 12))

        # Description
        desc_color = (210, 200, 225) if hovered else (170, 160, 190)
        desc = small_font.render(skill["desc"], True, desc_color)
        screen.blit(desc, (rect.x + 48, rect.y + 42))
    return card_rects


def _draw_start_screen(screen, big_font, font, small_font):
    sw, sh = screen.get_width(), screen.get_height()
    # Dark overlay
    screen.fill((10, 5, 20))

    # Title
    title = big_font.render("暗 夜 求 生", True, GOLD)
    title_rect = title.get_rect(center=(sw // 2, sh // 6))
    screen.blit(title, title_rect)

    # Subtitle
    sub = font.render("Darknight Survival", True, (150, 130, 180))
    sub_rect = sub.get_rect(center=(sw // 2, sh // 6 + 45))
    screen.blit(sub, sub_rect)

    # Mechanics text
    lines = [
        "WASD / 方向键  移动",
        "自动瞄准最近敌人开火",
        "击杀敌人掉落经验球  →  升级  →  选择强化",
        "",
        "武器系统：",
        "  旋转利刃 — 环绕自身的刀刃",
        "  连锁闪电 — 弹跳打击多个敌人",
        "  剧毒地雷 — 移动时释放毒圈",
        "",
        "敌人类型会随时间逐渐解锁",
    ]
    y = sh // 3 + 20
    for line in lines:
        if line == "":
            y += 8
            continue
        color = GOLD if line.startswith("武器") or line.startswith("敌人") else (200, 200, 210)
        text = small_font.render(line, True, color)
        text_rect = text.get_rect(center=(sw // 2, y))
        screen.blit(text, text_rect)
        y += 22

    # Start button
    btn_w, btn_h = 220, 50
    btn_x = (sw - btn_w) // 2
    btn_y = sh - 100
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, (40, 20, 60), btn_rect)
    pygame.draw.rect(screen, GOLD, btn_rect, 2)
    btn_text = font.render("开 始 游 戏", True, GOLD)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)

    hint = small_font.render("按 SPACE 或点击按钮开始", True, (120, 120, 140))
    hint_rect = hint.get_rect(center=(sw // 2, btn_y + btn_h + 22))
    screen.blit(hint, hint_rect)

    return btn_rect


def _draw_game_over(screen, big_font, font, elapsed_time, score, level, high_score, is_new_record):
    sw, sh = screen.get_width(), screen.get_height()
    overlay = pygame.Surface((sw, sh))
    overlay.set_alpha(220)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    title = big_font.render("游 戏 结 束", True, RED)
    title_rect = title.get_rect(center=(sw // 2, sh // 6))
    screen.blit(title, title_rect)

    y = sh // 3
    gap = sh // 18

    lines = [
        f"存活时间：{elapsed_time:.0f} 秒",
        f"击杀敌人：{score}",
        f"达到等级：Lv.{level}",
        f"历史最高分：{high_score}",
    ]
    for line in lines:
        text = font.render(line, True, WHITE)
        rect = text.get_rect(center=(sw // 2, y))
        screen.blit(text, rect)
        y += gap

    if is_new_record:
        record_text = big_font.render("新 纪 录 ！", True, GOLD)
        record_rect = record_text.get_rect(center=(sw // 2, y))
        screen.blit(record_text, record_rect)
        y += 50

    # Restart button
    btn_w, btn_h = 240, 50
    btn_x = (sw - btn_w) // 2
    btn_y = sh - 120
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, DARK_GRAY, btn_rect)
    pygame.draw.rect(screen, WHITE, btn_rect, 2)
    btn_text = font.render("重 新 开 始", True, WHITE)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)

    hint = font.render("按 SPACE 或点击按钮重新开始", True, GRAY)
    hint_rect = hint.get_rect(center=(sw // 2, btn_y + btn_h + 20))
    screen.blit(hint, hint_rect)

    return btn_rect


# --- Main ---

def main():
    pygame.init()
    pygame.key.stop_text_input()
    pygame.event.set_blocked(pygame.TEXTINPUT)
    pygame.event.set_blocked(pygame.TEXTEDITING)
    screen_w, screen_h = SCREEN_WIDTH, SCREEN_HEIGHT
    fullscreen = False
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("暗夜求生  |  F11 全屏")
    clock = pygame.time.Clock()
    audio = AudioManager()
    audio.start_music()

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

    font = _get_font(24)
    big_font = _get_font(48)
    dmg_font = _get_font(16)

    stats = {
        "fire_interval": FIRE_INTERVAL,
        "bullet_damage": 1,
        "player_speed": PLAYER_SPEED,
        "bullet_count": 1,
        "pickup_range": PICKUP_RANGE,
        "damage_taken": 1.0,
        "has_frostbite": 0,
        "crit_chance": 0.0,
        "crit_multiplier": CRIT_MULTIPLIER,
        "has_regen": 0,
        "regen_kills": 0,
        "has_blades": 0,
        "has_lightning": 0,
        "has_traps": 0,
    }

    spawn_timer = 0.0
    fire_timer = 0.0
    score = 0
    experience = 0
    level = 1
    paused = False
    chosen_skills = None
    elapsed_time = 0.0
    difficulty_level = 0
    player_hp = PLAYER_MAX_HP
    invincible_timer = 1.5  # spawn protection
    menu = True
    game_over = False
    high_score = load_high_score()
    new_record = False

    # FPS tracking
    fps_smooth = 60.0
    fps_display = "60"

    while True:
        dt = clock.tick(FPS) / 1000.0
        fps_raw = 1.0 / dt if dt > 0 else 60.0
        fps_smooth = fps_smooth * 0.95 + fps_raw * 0.05
        fps_display = f"{fps_smooth:.0f}"
        mouse_pos = pygame.mouse.get_pos()

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if menu:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    menu = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    btn_rect = pygame.Rect(
                        (screen.get_width() - 220) // 2, screen.get_height() - 100, 220, 50)
                    if btn_rect.collidepoint(event.pos):
                        menu = False
                continue  # skip rest of events while in menu
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((screen_w, screen_h))
                    screen_w, screen_h = screen.get_size()
                if paused and chosen_skills:
                    idx = -1
                    if event.key == pygame.K_1:
                        idx = 0
                    elif event.key == pygame.K_2:
                        idx = 1
                    elif event.key == pygame.K_3:
                        idx = 2
                    if 0 <= idx < len(chosen_skills):
                        apply_skill(stats, chosen_skills[idx])
                        player.speed = stats["player_speed"]
                        if stats.get("has_blades", 0) > 0:
                            blade_mgr.set_count(stats["bullet_count"] + stats["has_blades"])
                        chosen_skills = None
                        paused = False
            if event.type == pygame.MOUSEBUTTONDOWN and paused and chosen_skills:
                card_rects = _build_card_rects(len(chosen_skills), screen.get_width(), screen.get_height())
                for i, rect in enumerate(card_rects):
                    if rect.collidepoint(event.pos):
                        apply_skill(stats, chosen_skills[i])
                        player.speed = stats["player_speed"]
                        if stats.get("has_blades", 0) > 0:
                            blade_mgr.set_count(stats["bullet_count"] + stats["has_blades"])
                        chosen_skills = None
                        paused = False
                        break
            if game_over:
                do_restart = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    do_restart = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    btn_rect = pygame.Rect(
                        (screen.get_width() - 240) // 2, screen.get_height() - 120, 240, 50)
                    if btn_rect.collidepoint(event.pos):
                        do_restart = True
                if do_restart:
                    # Reset all state
                    player = Player()
                    camera = Camera()
                    enemies.empty()
                    bullets.empty()
                    enemy_bullets.empty()
                    orbs.empty()
                    particles.empty()
                    damage_numbers.clear()
                    explosions.clear()
                    trap_mgr = TrapManager()
                    blade_mgr = OrbitalBladeManager()
                    chain_lightning = ChainLightning()
                    stats = {
                        "fire_interval": FIRE_INTERVAL,
                        "bullet_damage": 1,
                        "player_speed": PLAYER_SPEED,
                        "bullet_count": 1,
                        "pickup_range": PICKUP_RANGE,
                        "damage_taken": 1.0,
                        "has_frostbite": 0,
                        "crit_chance": 0.0,
                        "crit_multiplier": CRIT_MULTIPLIER,
                        "has_regen": 0,
                        "regen_kills": 0,
                        "has_blades": 0,
                        "has_lightning": 0,
                        "has_traps": 0,
                    }
                    spawn_timer = 0.0
                    fire_timer = 0.0
                    score = 0
                    experience = 0
                    level = 1
                    paused = False
                    chosen_skills = None
                    elapsed_time = 0.0
                    difficulty_level = 0
                    player_hp = PLAYER_MAX_HP
                    invincible_timer = 1.5
                    game_over = False
                    new_record = False
                    high_score = load_high_score()

        # --- Update ---
        if not menu and not paused and not game_over:
            elapsed_time += dt
            if invincible_timer > 0:
                invincible_timer -= dt

            difficulty_level = int(elapsed_time / DIFFICULTY_INTERVAL)
            current_spawn_interval = SPAWN_INTERVAL * (SPAWN_RATE_FACTOR ** difficulty_level)

            keys = pygame.key.get_pressed()
            player.update(dt, keys)
            camera.update(player.rect, dt)

            is_moving = keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]

            # --- Spawn ---
            spawn_timer += dt
            while spawn_timer >= current_spawn_interval:
                spawn_timer -= current_spawn_interval
                enemies.add(_spawn_enemy(camera, elapsed_time, difficulty_level))

            # --- Auto-gun ---
            fire_timer += dt
            while fire_timer >= stats["fire_interval"] and enemies:
                fire_timer -= stats["fire_interval"]
                target = _nearest_enemy(player.rect, enemies)
                if target:
                    bullet_count = stats["bullet_count"]
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

            # --- Update all entities ---
            enemies.update(dt, player.rect)
            bullets.update(dt)
            enemy_bullets.update(dt)

            # --- Orbital Blades ---
            if stats.get("has_blades", 0) > 0:
                blade_mgr.update(dt)
                blade_hits = blade_mgr.check_damage(player.rect, enemies, dt, stats)
                for enemy, dmg, dead in blade_hits:
                    damage_numbers.append(DamageNumber(
                        enemy.rect.centerx, enemy.rect.top, int(dmg), dmg_font))
                    if stats.get("has_frostbite", 0) > 0:
                        enemy.apply_frostbite(FROSTBITE_SLOW)
                    if dead:
                        score = _kill_enemy(enemy, particles, orbs, explosions, score, audio, fps_smooth)
                        enemy.kill()

            # --- Chain Lightning ---
            if stats.get("has_lightning", 0) > 0:
                lightning_hits = chain_lightning.update(dt, player.rect, enemies, stats)
                for enemy, dmg, dead in lightning_hits:
                    damage_numbers.append(DamageNumber(
                        enemy.rect.centerx, enemy.rect.top, int(dmg), dmg_font))
                    if dead:
                        score = _kill_enemy(enemy, particles, orbs, explosions, score, audio, fps_smooth)
                        enemy.kill()

            # --- Acid Traps ---
            if stats.get("has_traps", 0) > 0:
                trap_interval = 2.0 * (0.85 ** (stats.get("has_traps", 1) - 1))
                trap_mgr.update(dt, player, is_moving, trap_interval)
                for trap in list(trap_mgr.group):
                    trap.check_enemies(enemies)

            # --- DoT death check ---
            for enemy in list(enemies):
                if enemy.hp <= 0:
                    score = _kill_enemy(enemy, particles, orbs, explosions, score, audio, fps_smooth)
                    enemy.kill()

            # --- Ranger fire ---
            for enemy in list(enemies):
                if isinstance(enemy, Ranger) and enemy.wants_to_fire():
                    enemy_bullets.add(EnemyBullet(
                        enemy.rect.centerx, enemy.rect.centery,
                        player.rect.centerx, player.rect.centery))

            # --- Off-map cleanup ---
            for bullet in list(bullets):
                if not (0 <= bullet.rect.centerx <= MAP_WIDTH and
                        0 <= bullet.rect.centery <= MAP_HEIGHT):
                    bullet.kill()
            for eb in list(enemy_bullets):
                if not (0 <= eb.rect.centerx <= MAP_WIDTH and
                        0 <= eb.rect.centery <= MAP_HEIGHT):
                    eb.kill()

            # --- Player bullets vs enemies ---
            hits = pygame.sprite.groupcollide(bullets, enemies, False, False)
            for bullet, hit_enemies in hits.items():
                bullet.kill()
                for enemy in hit_enemies:
                    dmg = stats["bullet_damage"]
                    is_crit = random.random() < stats["crit_chance"]
                    if is_crit:
                        dmg *= stats["crit_multiplier"]
                        # Knockback: push enemy away from player
                        kx = enemy.rect.centerx - player.rect.centerx
                        ky = enemy.rect.centery - player.rect.centery
                        kdist = math.hypot(kx, ky)
                        if kdist > 0:
                            enemy.rect.x += (kx / kdist) * 12
                            enemy.rect.y += (ky / kdist) * 12

                    dead = enemy.take_damage(dmg)
                    damage_numbers.append(DamageNumber(
                        enemy.rect.centerx, enemy.rect.top, int(dmg), dmg_font))

                    if stats.get("has_frostbite", 0) > 0:
                        enemy.apply_frostbite(FROSTBITE_SLOW)

                    if dead:
                        score = _kill_enemy(enemy, particles, orbs, explosions, score, audio, fps_smooth)
                        enemy.kill()
                        # Regen tracking
                        if stats.get("has_regen", 0) > 0:
                            stats["regen_kills"] += 1
                            if stats["regen_kills"] >= REGEN_KILLS:
                                stats["regen_kills"] -= REGEN_KILLS
                                player_hp = min(PLAYER_MAX_HP, player_hp + 1)
                    break

            # --- Enemy bullets vs player ---
            if invincible_timer <= 0:
                for eb in list(enemy_bullets):
                    if eb.rect.colliderect(player.rect):
                        player_hp, invincible_timer, hit = _handle_player_damage(
                            player_hp, eb.damage, invincible_timer, stats["damage_taken"])
                        if hit:
                            camera.shake(0.12, 5)
                        eb.kill()
                        break

            # --- Enemy contact vs player ---
            if invincible_timer <= 0:
                for enemy in list(enemies):
                    if enemy.rect.colliderect(player.rect) and enemy.contact_damage > 0:
                        player_hp, invincible_timer, hit = _handle_player_damage(
                            player_hp, enemy.contact_damage, invincible_timer, stats["damage_taken"])
                        if hit:
                            camera.shake(0.15, 6)
                        # Knock enemy away so it doesn't sit on the player
                        kx = enemy.rect.centerx - player.rect.centerx
                        ky = enemy.rect.centery - player.rect.centery
                        kdist = math.hypot(kx, ky)
                        if kdist > 0:
                            enemy.rect.x += (kx / kdist) * 30
                            enemy.rect.y += (ky / kdist) * 30
                        break

            # --- Explosions ---
            for exp in explosions:
                exp.update(dt)
                if not exp._applied:
                    player_hit = exp.apply_damage(player, enemies)
                    if player_hit and invincible_timer <= 0:
                        player_hp, invincible_timer, _ = _handle_player_damage(
                            player_hp, exp.damage, invincible_timer, stats["damage_taken"])
                # Check enemies killed by explosion
                for enemy in list(enemies):
                    if enemy.hp <= 0:
                        score = _kill_enemy(enemy, particles, orbs, explosions, score, audio, fps_smooth)
                        enemy.kill()
            explosions = [e for e in explosions if e.alive]

            # --- Orbs ---
            for orb in list(orbs):
                orb.update(dt, player.rect, stats["pickup_range"])
                if orb.rect.colliderect(player.rect):
                    experience += XP_PER_ORB
                    orb.kill()

            # --- Particles & damage numbers ---
            particles.update(dt)
            for dn in damage_numbers[:]:
                dn.update(dt)
                if not dn.alive:
                    damage_numbers.remove(dn)

            # --- Level-up ---
            xp_to_next = level * XP_PER_LEVEL
            if experience >= xp_to_next:
                experience -= xp_to_next
                level += 1
                paused = True
                chosen_skills = get_random_skills(3)
                audio.play_level_up()

            # --- Game over ---
            if player_hp <= 0:
                game_over = True
                new_record = save_high_score(score)
                if new_record:
                    high_score = score

        # --- Draw ---
        if menu:
            _draw_start_screen(screen, big_font, font, font)
            pygame.display.flip()
            continue

        screen.fill(BLACK)
        camera.draw_grid(screen)

        # Traps (drawn under entities)
        if stats.get("has_traps", 0) > 0:
            for trap in trap_mgr.group:
                screen.blit(trap.image, camera.apply(trap.rect))

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

        # Orbital blades
        if stats.get("has_blades", 0) > 0:
            blade_mgr.draw(screen, camera, player.rect)

        # Chain lightning bolts
        if stats.get("has_lightning", 0) > 0:
            chain_lightning.draw(screen, camera)

        # Explosions & damage numbers
        for exp in explosions:
            exp.draw(screen, camera)
        for dn in damage_numbers:
            dn.draw(screen, camera)

        xp_to_next = level * XP_PER_LEVEL
        _draw_ui(screen, font, level, experience, xp_to_next, player_hp, PLAYER_MAX_HP)

        if paused and chosen_skills:
            _draw_skill_selection(screen, big_font, font, chosen_skills, mouse_pos)

        if game_over:
            _draw_game_over(screen, big_font, font, elapsed_time, score, level,
                           high_score, new_record)

        # FPS counter (top-right)
        fps_color = GREEN if fps_smooth >= 55 else (RED if fps_smooth < 30 else GOLD)
        fps_text = font.render(fps_display, True, fps_color)
        screen.blit(fps_text, (screen.get_width() - fps_text.get_width() - 8, 8))

        player_dps = _calc_player_dps(stats)
        time_str = f"{elapsed_time:.0f}s"
        bc = stats["bullet_count"]
        title = f"击杀:{score} | DPS:{player_dps:.0f} | {time_str} | 难度{difficulty_level} | 刀:{bc+1}"
        pygame.display.set_caption(title)
        pygame.display.flip()


def _build_card_rects(count, sw=SCREEN_WIDTH, sh=SCREEN_HEIGHT):
    card_w, card_h = 420, 80
    card_x = (sw - card_w) // 2
    start_y = sh // 4 + 20
    gap = 14
    return [pygame.Rect(card_x, start_y + i * (card_h + gap), card_w, card_h)
            for i in range(count)]


if __name__ == "__main__":
    main()
