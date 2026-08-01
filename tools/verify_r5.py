# -*- coding: utf-8 -*-
"""R5 角色解锁验收（对应 playability-pack-v1.md §3.6 五条验收标准）。

用法：python tools/verify_r5.py   （结果写入 tools/verify_out_r5.txt）

覆盖：
1. 三角色可见/解锁条件判定/解锁持久化（写 unlocks 重启保留）
2. 初始数值修正生效（火枪手 12HP/伤害3、坦克 32HP/330/护盾5、游侠 0.45s）
3. 专属被动乘区生效（火力增强×1.5 / 钢铁意志 0.9×0.97 / 急速射击×0.78 / 凌波+3%）
4. 旧存档（仅 high_score）读取不报错，新字段默认初始化
5. 每角色结算后 meta.victories +1、per_character.runs +1
"""
import os
import sys
import json
import tempfile
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
# 隔离真实存档：所有 I/O 落在临时目录
_TMP_ROOT = tempfile.mkdtemp(prefix="darknight_r5_verify_")
os.environ["APPDATA"] = _TMP_ROOT

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    out = open("verify_out_r5.txt", "w", encoding="utf-8")
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

# 需要视频模式：Player() 加载精灵图依赖 convert_alpha
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_MAX_HP, PLAYER_SPEED,
    FIRE_INTERVAL, BULLET_BASE_DAMAGE,
)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
from characters import CHARACTERS
from skills import apply_skill, get_random_skills, SKILL_POOL
from game.state import GameState

import systems.save_data as sd


def _fresh_sd():
    """每个用例独立存档路径，避免串扰真实存档。"""
    sd.SAVE_PATH = os.path.join(tempfile.mkdtemp(prefix="r5_save_"), "souls_save.json")
    sd.LEGACY_SAVE_PATH = sd.SAVE_PATH + ".legacy"
    return sd


def get_skill(name):
    for s in SKILL_POOL:
        if s["name"] == name:
            return s
    return None


# ---------- §3.6-1 角色定义 / 解锁条件 ----------
def v_characters_defined():
    assert set(CHARACTERS.keys()) == {"default", "gunslinger", "vanguard", "wayfarer"}, CHARACTERS.keys()
    for ch, cfg in CHARACTERS.items():
        assert isinstance(cfg.get("stats_delta"), dict), ch
        assert "unlock_condition" in cfg, ch
        assert isinstance(cfg.get("passive"), dict), ch


def v_unlock_conditions():
    g = CHARACTERS["gunslinger"]["unlock_condition"]
    assert g({"total_kills": 499, "best_run_kills": 0}) is False
    assert g({"total_kills": 500, "best_run_kills": 0}) is True          # 累计击杀 500
    assert g({"total_kills": 0, "best_run_kills": 249}) is False
    assert g({"total_kills": 0, "best_run_kills": 250}) is True          # 单局击杀 250
    v = CHARACTERS["vanguard"]["unlock_condition"]
    assert v({"boss_kills": 0, "best_time": 359.0}) is False
    assert v({"boss_kills": 1, "best_time": 0.0}) is True                # 累计 Boss 1
    assert v({"boss_kills": 0, "best_time": 360.0}) is True              # 单局存活 360s
    w = CHARACTERS["wayfarer"]["unlock_condition"]
    assert w({"total_kills": 1999, "best_run_kills": 199}) is False
    assert w({"total_kills": 1999, "best_run_kills": 200}) is True       # 单局击杀 200
    assert w({"total_kills": 2000, "best_run_kills": 0}) is True         # 累计击杀 2000


# ---------- §3.6-2 初始数值修正生效 ----------
def v_stat_overrides():
    gs = GameState("gunslinger")
    assert gs.stats["max_hp"] == 12, gs.stats["max_hp"]
    assert gs.stats["bullet_damage"] == 3, gs.stats["bullet_damage"]
    assert gs.stats["player_speed"] == 400, gs.stats["player_speed"]
    assert abs(gs.stats["fire_interval"] - 0.55) < 1e-6, gs.stats["fire_interval"]
    assert abs(gs.stats["crit_chance"] - 0.10) < 1e-6, gs.stats["crit_chance"]
    assert gs.player_hp == 12

    vg = GameState("vanguard")
    assert vg.stats["max_hp"] == 32, vg.stats["max_hp"]
    assert vg.stats["player_speed"] == 330, vg.stats["player_speed"]
    assert abs(vg.stats["fire_interval"] - 0.65) < 1e-6, vg.stats["fire_interval"]
    assert abs(vg.stats["damage_taken"] - 0.85) < 1e-6, vg.stats["damage_taken"]
    assert vg.player_shield == 5, vg.player_shield
    assert vg.player_max_shield == 15, vg.player_max_shield

    wf = GameState("wayfarer")
    assert wf.stats["max_hp"] == 18, wf.stats["max_hp"]
    assert wf.stats["player_speed"] == 430, wf.stats["player_speed"]
    assert abs(wf.stats["fire_interval"] - 0.45) < 1e-6, wf.stats["fire_interval"]

    # default 不受影响
    d = GameState("default")
    assert d.stats["max_hp"] == PLAYER_MAX_HP == 20
    assert d.stats["bullet_damage"] == BULLET_BASE_DAMAGE == 2
    assert d.player_shield == 0 and d.player_max_shield == 10


def v_player_sync():
    from entities import Player
    p = Player("gunslinger")
    assert p.max_hp == 12 and p.speed == 400, (p.max_hp, p.speed)
    p2 = Player("vanguard")
    assert p2.max_hp == 32 and p2.speed == 330, (p2.max_hp, p2.speed)
    p3 = Player("wayfarer")
    assert p3.max_hp == 18 and p3.speed == 430, (p3.max_hp, p3.speed)
    p4 = Player()
    assert p4.max_hp == PLAYER_MAX_HP and p4.speed == PLAYER_SPEED


# ---------- §3.6-3 专属被动乘区生效 ----------
def v_passive_gunslinger():
    st = GameState("gunslinger").stats
    s = get_skill("火力增强")
    apply_skill(st, s, "gunslinger")
    assert abs(st["bullet_damage"] - (3 + 1 * 1.5)) < 1e-6, st["bullet_damage"]      # 4.5
    apply_skill(st, s, "gunslinger")
    assert abs(st["bullet_damage"] - (3 + 2 * 1.5)) < 1e-6, st["bullet_damage"]      # 6.0
    # character=None 行为不变（R3）
    d = GameState().stats
    apply_skill(d, s)
    assert abs(d["bullet_damage"] - (2 + 1)) < 1e-6, d["bullet_damage"]              # 3


def v_passive_vanguard():
    st = GameState("vanguard").stats
    s = get_skill("钢铁意志")
    apply_skill(st, s, "vanguard")
    expected = 0.85 * 0.9 * 0.97
    assert abs(st["damage_taken"] - expected) < 1e-6, (st["damage_taken"], expected)
    apply_skill(st, s, "vanguard")
    expected2 = expected * 0.9 * 0.97
    assert abs(st["damage_taken"] - expected2) < 1e-6, (st["damage_taken"], expected2)
    # 对照默认 0.9/层
    d = GameState().stats
    apply_skill(d, s)
    assert abs(d["damage_taken"] - 0.9) < 1e-6, d["damage_taken"]


def v_passive_wayfarer():
    st = GameState("wayfarer").stats
    apply_skill(st, get_skill("急速射击"), "wayfarer")
    assert abs(st["fire_interval"] - 0.45 * 0.78) < 1e-6, st["fire_interval"]       # 0.351
    apply_skill(st, get_skill("凌波微步"), "wayfarer")
    assert abs(st["player_speed"] - 430 * 1.25 * 1.03) < 1e-6, st["player_speed"]    # 553.625
    # 急速射击下限 0.18 仍生效
    s2 = GameState("wayfarer").stats
    for _ in range(8):
        apply_skill(s2, get_skill("急速射击"), "wayfarer")
    assert s2["fire_interval"] >= 0.18 - 1e-9, s2["fire_interval"]
    # 对照默认 0.85/层
    d = GameState().stats
    apply_skill(d, get_skill("急速射击"))
    assert abs(d["fire_interval"] - FIRE_INTERVAL * 0.85) < 1e-6, d["fire_interval"]


# ---------- §3.6-4 旧存档兼容读取 ----------
def v_old_save_compat():
    sd_ = _fresh_sd()
    with open(sd_.SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump({"high_score": 123}, f)
    assert sd_.load_high_score() == 123
    meta = sd_.load_meta()
    assert meta["total_kills"] == 0
    assert meta["total_runs"] == 0
    assert meta["best_time"] == 0.0
    assert meta["per_character"]["default"] == {"kills": 0, "runs": 0}
    assert sd_.is_unlocked("default") is True
    assert sd_.is_unlocked("gunslinger") is False
    assert sd_.load_unlocks() == {"gunslinger": False, "vanguard": False, "wayfarer": False}
    # save_high_score 不得覆盖新字段
    sd_.save_high_score(200)
    data = json.load(open(sd_.SAVE_PATH, encoding="utf-8"))
    assert data["high_score"] == 200
    assert "meta" in data and "unlocks" in data and "settings" in data


# ---------- §3.6-5 meta 写入 / 解锁持久化 ----------
def v_meta_write():
    sd_ = _fresh_sd()
    sd_.record_run_result("gunslinger", kills=10, boss_kills=1, score=500,
                          elapsed=100.0, victory=True)
    meta = sd_.load_meta()
    assert meta["total_kills"] == 10, meta
    assert meta["total_score"] == 500, meta
    assert meta["total_runs"] == 1, meta
    assert meta["victories"] == 1, meta
    assert meta["boss_kills"] == 1, meta
    assert meta["best_time"] == 100.0, meta
    assert meta["best_run_kills"] == 10, meta
    pc = meta["per_character"]["gunslinger"]
    assert pc["kills"] == 10 and pc["runs"] == 1, pc
    # 击杀 1 Boss → 坦克自动解锁（写 unlocks，重启保留）
    assert sd_.is_unlocked("vanguard") is True
    assert sd_.is_unlocked("gunslinger") is False   # 累计 500 未达
    # 重启保留：等价于新进程重新读文件（is_unlocked 每次读盘）
    saved_path = sd.SAVE_PATH
    data = json.load(open(saved_path, encoding="utf-8"))
    assert data["unlocks"]["vanguard"] is True
    assert sd.is_unlocked("vanguard") is True


def v_run_result_victory_per_character():
    sd_ = _fresh_sd()
    for ch in ("default", "gunslinger", "vanguard", "wayfarer"):
        sd_.record_run_result(ch, kills=300, boss_kills=4, score=1200,
                              elapsed=600.0, victory=True)
    meta = sd_.load_meta()
    assert meta["victories"] == 4, meta["victories"]
    assert meta["total_runs"] == 4, meta["total_runs"]
    assert meta["best_time"] == 600.0, meta["best_time"]
    for ch in ("default", "gunslinger", "vanguard", "wayfarer"):
        pc = meta["per_character"][ch]
        assert pc["runs"] == 1, (ch, pc)
        assert pc["kills"] == 300, (ch, pc)
    # 全解锁（Boss 4、单局 300 击杀）
    for ch in ("gunslinger", "vanguard", "wayfarer"):
        assert sd_.is_unlocked(ch) is True, ch


def v_save_meta_incremental():
    sd_ = _fresh_sd()
    sd_.save_meta({"total_kills": 5, "per_character": {"wayfarer": {"kills": 3, "runs": 1}}})
    sd_.save_meta({"total_kills": 7})
    meta = sd_.load_meta()
    assert meta["total_kills"] == 7, meta["total_kills"]
    assert meta["per_character"]["wayfarer"] == {"kills": 3, "runs": 1}


# ---------- 回归：R3 行为不破坏 ----------
def v_r3_no_regression():
    st = GameState().stats
    apply_skill(st, get_skill("暗影新星"))
    assert st["blade_damage"] == 12
    assert st["nova_cooldown"] == 3.8
    st2 = GameState().stats
    apply_skill(st2, get_skill("连锁闪电"))
    assert st2["lightning_chains"] == 5 and st2["lightning_damage"] == 7
    st3 = GameState().stats
    apply_skill(st3, get_skill("剧毒地雷"))
    assert st3["trap_damage"] == 4 and st3["trap_interval"] == 2.0
    for _ in range(30):
        sk = get_random_skills(3, GameState().stats)
        assert len({s["name"] for s in sk}) == 3
    assert len(SKILL_POOL) == 14


# ---------- UI：角色选择层可绘制 ----------
def v_character_select_draw():
    from ui.character_select import (
        draw_character_select, build_character_select_layout,
        handle_character_select_input,
    )
    from ui.drawables import get_font
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    meta = {"total_kills": 100, "victories": 2, "high_score": 500, "total_runs": 3,
            "best_run_kills": 60}
    unlocks = {"gunslinger": True, "vanguard": False, "wayfarer": False}
    card_rects, start_btn, back_btn = build_character_select_layout(SCREEN_WIDTH, SCREEN_HEIGHT)
    assert len(card_rects) == 4
    draw_character_select(screen, get_font(48), get_font(24), get_font(14),
                          "gunslinger", meta, unlocks, card_rects, start_btn, back_btn)
    # 输入：点击锁定角色不选中；点击已解锁角色选中；开始返回 start
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": card_rects["vanguard"].center, "button": 1})
    assert handle_character_select_input(ev, card_rects, start_btn, back_btn, "default", unlocks) is None
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": card_rects["gunslinger"].center, "button": 1})
    assert handle_character_select_input(ev, card_rects, start_btn, back_btn, "default", unlocks) == "select:gunslinger"
    ev = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
    assert handle_character_select_input(ev, card_rects, start_btn, back_btn, "gunslinger", unlocks) == "start"
    ev = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    assert handle_character_select_input(ev, card_rects, start_btn, back_btn, "gunslinger", unlocks) == "back"


checks = [
    ("R5 四角色定义齐全", v_characters_defined),
    ("R5 解锁条件判定（火枪手/坦克/游侠）", v_unlock_conditions),
    ("R5 初始数值覆盖生效（火枪手/坦克/游侠）", v_stat_overrides),
    ("R5 Player 同步 speed/max_hp", v_player_sync),
    ("R5 被动·火药专家 火力增强×1.5", v_passive_gunslinger),
    ("R5 被动·钢铁壁垒 0.9×0.97/层", v_passive_vanguard),
    ("R5 被动·疾风连射×0.78 + 灵动+3%/层", v_passive_wayfarer),
    ("R5 旧存档兼容读取（仅 high_score）", v_old_save_compat),
    ("R5 meta 写入 + 解锁持久化", v_meta_write),
    ("R5 四角色结算 victories/runs 记录", v_run_result_victory_per_character),
    ("R5 save_meta 增量写", v_save_meta_incremental),
    ("R5 回归·R3 行为不破坏（池14/三选一）", v_r3_no_regression),
    ("R5 角色选择 UI 绘制与输入", v_character_select_draw),
]


def _main():
    for name, fn in checks:
        check(name, fn)
    print()
    if FAILED:
        print("VERIFY_FAIL:", ", ".join(FAILED))
        rc = 1
    else:
        print("VERIFY_ALL_PASS")
        rc = 0
    out.close()
    return rc


if __name__ == "__main__":
    sys.exit(_main())
out.close()
