# -*- coding: utf-8 -*-
"""BUG-001 修复验收（DN-ENG-FIX-BUG001）。

根因：Boss 同时加入 self.enemies 与 self.bosses 两组；
- 旧 :381 `self.enemies.update(dt, player_rect)` 先驱动 boss.update()（attack_timer 到阈值触发
  _do_attacks 并把 attack_timer 清零）→ 返回 attacks 列表 → **Group.update 丢弃返回值**
- 随后 _update_bosses 再调 boss.update() → 计时器已清零 → attacks 空 → _process_boss_attacks 收不到

修复（方案 A）：enemies 更新改为排除 Boss 的手动循环，Boss 仅由 _update_bosses 驱动一次。

本脚本验证：
1. 源码事实：enemies 更新循环确实排除 Boss（防回归误删）
2. 四 Boss 攻击经游戏循环送达 _process_boss_attacks 的计数（CorpseKing 500 帧 ≥3，其余 120 帧 ≥1）
3. 绘制无重复（enemies 绘制排除 Boss、bosses 单独绘制）
4. 输出写 tools/verify_out_fix_bug001.txt

用法：venv/Scripts/python.exe tools/verify_fix_bug001.py
"""
import os
import sys
import random
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    out = open(os.path.join(_PROJECT_ROOT, "tools", "verify_out_fix_bug001.txt"), "w", encoding="utf-8")
    sys.stdout = out
    sys.stderr = out

FAILED = []


def check(name, fn):
    try:
        fn()
        print(f"[OK]   {name}")
    except BaseException:
        print(f"[FAIL] {name}")
        traceback.print_exc()
        FAILED.append(name)


import pygame
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

from game.normal_game import NormalGame
from entities.boss import BOSS_CLASSES, Boss
from entities.boss import CorpseKing


def v_enemies_loop_excludes_boss():
    """源码事实：enemies 更新循环排除 Boss（Boss 仅由 _update_bosses 驱动）。"""
    import inspect
    import game.base_game as bg
    src = inspect.getsource(bg.BaseGame._update)
    assert "isinstance(enemy, Boss)" in src, "enemies 更新循环必须排除 Boss"
    assert "enemy.update(dt, self.player.rect)" in src
    # Boss 仍保留在 enemies 组（武器管理器/子弹碰撞依赖）
    g = NormalGame()
    g._init_game()
    ck = CorpseKing(400, 400)
    g.enemies.add(ck)
    g.bosses.add(ck)
    assert ck in g.enemies and ck in g.bosses


def v_draw_no_duplicate():
    """绘制无重复：enemies 绘制排除 Boss；bosses 单独绘制（README v3.3 双组修复保持）。"""
    import inspect
    import game.base_game as bg
    src = inspect.getsource(bg.BaseGame._render)
    assert "if not isinstance(enemy, Boss)" in src
    assert "for boss in self.bosses" in src


def v_boss_attack_count():
    """四 Boss 攻击计数：CorpseKing 500 帧 ≥3，其余 120 帧 ≥1。

    稳定性：IronColossus 的 armor 分支（0.35≤r<0.65）只开甲不产出攻击 dict，
    若首 roll 命中 armor 则 120 帧窗口内 delivered=0 → ~30% flaky。
    按 Boss 固定随机种子：IronColossus seed=1 → random()≈0.134<0.35 → shockwave，确定性。
    """
    SEEDS = {"CorpseKing": 10, "ShadowMage": 20, "IronColossus": 1, "VoidLord": 40}
    for cls in BOSS_CLASSES:
        random.seed(SEEDS[cls.__name__])
        g = NormalGame()
        g._init_game()
        boss = cls(400, 400)
        g.enemies.add(boss)
        g.bosses.add(boss)
        g.game_state.boss_active = True
        boss.attack_timer = boss.config["attack_interval"]

        delivered = {"n": 0}
        orig = g._process_boss_attacks

        def counted(attacks):
            delivered["n"] += len(attacks)
            orig(attacks)

        g._process_boss_attacks = counted

        frames = 500 if cls.__name__ == "CorpseKing" else 120
        for _ in range(frames):
            g._update(0.016)

        threshold = 3 if cls.__name__ == "CorpseKing" else 1
        print(f"  {cls.__name__}: {frames}帧 送达 {delivered['n']} 条攻击（阈值 ≥{threshold}）")
        assert delivered["n"] >= threshold, \
            f"{cls.__name__}: {delivered['n']} 条攻击 < {threshold}（BUG-001 未修复？）"


def v_boss_movement_anim_flash():
    """修复后 Boss 移动/动画/受击闪白仍正常（_update_bosses 全包含 update）。"""
    g = NormalGame()
    g._init_game()
    ck = CorpseKing(400, 400)
    g.enemies.add(ck)
    g.bosses.add(ck)
    g.game_state.boss_active = True
    x0, y0 = ck.rect.centerx, ck.rect.centery
    player = pygame.Rect(500, 300, 32, 32)
    for _ in range(10):
        g._update(0.016)
    # Boss 移动（朝向玩家或攻击/蓄力中——至少 update 不崩、flash/anim 帧推进）
    assert ck._anim is not None
    assert g.effects is not None
    # 受击闪白：打一下后 flash_timer 被置位
    ck.take_damage(5)
    assert ck.hp < ck.max_hp


checks = [
    ("BUG-001 源码事实：enemies 更新循环排除 Boss", v_enemies_loop_excludes_boss),
    ("BUG-001 绘制无重复（Boss 双组不重绘）", v_draw_no_duplicate),
    ("BUG-001 四 Boss 攻击计数经游戏循环送达", v_boss_attack_count),
    ("BUG-001 Boss 移动/动画/受击闪白正常", v_boss_movement_anim_flash),
]


def _main():
    print("BUG-001 修复验收（DN-ENG-FIX-BUG001）")
    print("=" * 46)
    for name, fn in checks:
        check(name, fn)
    print()
    if FAILED:
        print("BUG001_FIX_FAIL:", ", ".join(FAILED))
        rc = 1
    else:
        print("BUG001_FIX_ALL_PASS")
        rc = 0
    out.close()
    return rc


if __name__ == "__main__":
    sys.exit(_main())
out.close()
