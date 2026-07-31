"""打击感效果系统：顿帧、死亡残影、命中火花、枪口火光、全屏闪光、低血量脉动。"""
import math
import random
import pygame


class _DeathGhost:
    """敌人死亡时的白色残影：放大 + 淡出。"""

    def __init__(self, image, center, duration=0.28):
        mask = pygame.mask.from_surface(image)
        self.base = mask.to_surface(
            setcolor=(255, 255, 255, 255),
            unsetcolor=(0, 0, 0, 0)).convert_alpha()
        self.center = center
        self.duration = duration
        self.timer = duration

    def update(self, dt):
        self.timer -= dt
        return self.timer > 0

    def draw(self, screen, camera):
        t = 1.0 - self.timer / self.duration  # 0 -> 1
        scale = 1.0 + t * 0.55
        alpha = int(210 * (1 - t) ** 1.5)
        w = max(2, int(self.base.get_width() * scale))
        h = max(2, int(self.base.get_height() * scale))
        img = pygame.transform.scale(self.base, (w, h))
        img.set_alpha(alpha)
        rect = img.get_rect(center=self.center)
        screen.blit(img, camera.apply(rect))


class _Spark:
    """命中火花：沿方向飞散的短线条。"""

    def __init__(self, x, y, dir_x, dir_y, color):
        angle = math.atan2(dir_y, dir_x) + random.uniform(-0.9, 0.9)
        speed = random.uniform(180, 420)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.duration = random.uniform(0.12, 0.24)
        self.timer = self.duration

    def update(self, dt):
        self.timer -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= max(0.0, 1 - 6.0 * dt)
        self.vy *= max(0.0, 1 - 6.0 * dt)
        return self.timer > 0

    def draw(self, screen, camera):
        life = max(0.0, self.timer / self.duration)
        length = 3 + 7 * life
        speed = math.hypot(self.vx, self.vy)
        if speed <= 1:
            return
        nx, ny = self.vx / speed, self.vy / speed
        sx = self.x - camera.offset.x
        sy = self.y - camera.offset.y
        end = (sx + nx * length, sy + ny * length)
        color = tuple(min(255, int(c + (255 - c) * life * 0.6)) for c in self.color)
        pygame.draw.line(screen, color, (sx, sy), end, 2)


class _MuzzleFlash:
    """枪口火光：一瞬间的星形亮光。"""

    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.duration = 0.06
        self.timer = self.duration

    def update(self, dt):
        self.timer -= dt
        return self.timer > 0

    def draw(self, screen, camera):
        life = max(0.0, self.timer / self.duration)
        sx = self.x - camera.offset.x
        sy = self.y - camera.offset.y
        r = int(5 + 7 * life)
        surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        c = r * 2
        pygame.draw.circle(surf, (255, 240, 180, int(190 * life)), (c, c), r)
        pygame.draw.circle(surf, (255, 255, 230, int(230 * life)), (c, c), max(1, r // 2))
        # 沿射击方向的光刺
        tip = (c + math.cos(self.angle) * r * 2, c + math.sin(self.angle) * r * 2)
        pygame.draw.line(surf, (255, 235, 170, int(160 * life)), (c, c), tip, 3)
        screen.blit(surf, (sx - c, sy - c), special_flags=pygame.BLEND_RGBA_ADD)


class EffectManager:
    """统一管理所有打击感效果，由游戏主循环驱动。"""

    def __init__(self, screen_width, screen_height):
        self.sw = screen_width
        self.sh = screen_height
        self.ghosts = []
        self.sparks = []
        self.flashes = []
        self.hitstop_timer = 0.0
        # 全屏闪光
        self._flash_alpha = 0.0
        self._flash_color = (255, 255, 255)
        self._flash_surf = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        # 低血量红色脉动（预渲染边缘渐变）
        self._lowhp_surf = self._build_lowhp_overlay()
        self._pulse_t = 0.0

    # --- 触发接口 ---

    def trigger_hitstop(self, duration):
        self.hitstop_timer = max(self.hitstop_timer, duration)

    def consume_hitstop(self, dt):
        """返回 True 表示本帧游戏逻辑应冻结。"""
        if self.hitstop_timer > 0:
            self.hitstop_timer -= dt
            return True
        return False

    def add_death_ghost(self, image, center):
        if len(self.ghosts) < 40:
            self.ghosts.append(_DeathGhost(image, center))

    def add_sparks(self, x, y, dir_x, dir_y, color=(255, 210, 120), count=4):
        for _ in range(count):
            if len(self.sparks) >= 160:
                break
            self.sparks.append(_Spark(x, y, dir_x, dir_y, color))

    def add_muzzle_flash(self, x, y, angle):
        if len(self.flashes) < 12:
            self.flashes.append(_MuzzleFlash(x, y, angle))

    def screen_flash(self, color, alpha):
        if alpha > self._flash_alpha:
            self._flash_alpha = alpha
            self._flash_color = color

    # --- 更新与绘制 ---

    def update(self, dt):
        self._pulse_t += dt
        self.ghosts = [g for g in self.ghosts if g.update(dt)]
        self.sparks = [s for s in self.sparks if s.update(dt)]
        self.flashes = [f for f in self.flashes if f.update(dt)]
        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - 420 * dt)

    def draw_world(self, screen, camera):
        """绘制世界坐标系中的效果（在实体之后、HUD之前调用）。"""
        for g in self.ghosts:
            g.draw(screen, camera)
        for s in self.sparks:
            s.draw(screen, camera)
        for f in self.flashes:
            f.draw(screen, camera)

    def draw_screen(self, screen, hp_ratio=1.0):
        """绘制全屏效果（闪光、低血量脉动）。"""
        if self._flash_alpha > 0:
            self._flash_surf.fill((*self._flash_color, int(self._flash_alpha)))
            screen.blit(self._flash_surf, (0, 0))
        if hp_ratio < 0.3:
            pulse = 0.55 + 0.45 * math.sin(self._pulse_t * 6.0)
            danger = 1.0 - hp_ratio / 0.3
            self._lowhp_surf.set_alpha(int(150 * pulse * danger))
            screen.blit(self._lowhp_surf, (0, 0))

    def _build_lowhp_overlay(self):
        surf = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        edge = 130
        for i in range(edge):
            alpha = int(140 * (1 - i / edge) ** 2)
            color = (200, 20, 25, alpha)
            pygame.draw.line(surf, color, (0, i), (self.sw, i))
            pygame.draw.line(surf, color, (0, self.sh - 1 - i), (self.sw, self.sh - 1 - i))
            pygame.draw.line(surf, color, (i, 0), (i, self.sh))
            pygame.draw.line(surf, color, (self.sw - 1 - i, 0), (self.sw - 1 - i, self.sh))
        return surf
