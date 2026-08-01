"""存档系统：写入 %APPDATA%/Darknight/（跨平台回退用户主目录）。

- 新路径：<APPDATA 或 ~>/Darknight/souls_save.json
- 旧路径：程序当前目录 souls_save.json（v3.8 及以前）
- 首次运行时若旧存档存在且新路径无存档，则自动迁移一次；
  读取时也兼容旧位置，保证玩家历史最高分不丢失。
- 新路径不可写时回退旧路径，优先保证功能可用。

R5 扩展（design/gdd/playability-pack-v1.md §3.1 schema，向后兼容旧档）：
- 新增 unlocks / meta / settings 字段；旧文件缺字段时按默认值读取，不报错。
- 语义：save_high_score 保留；新增 load_meta() / save_meta(delta)（增量写）；
  record_run_result() 为结算一次性写入（防频繁 I/O）；refresh_unlocks() 依据 meta 自动解锁。
"""
import json
import os

APP_DIR_NAME = "Darknight"
SAVE_FILENAME = "souls_save.json"

# 兼容旧引用：模块级 SAVE_PATH 指向新路径
SAVE_PATH = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"),
                         APP_DIR_NAME, SAVE_FILENAME)

# 旧版本存档位置（程序当前目录）
LEGACY_SAVE_PATH = "souls_save.json"

# 角色 key → 解锁状态（default 恒解锁，不入表）
_UNLOCK_KEYS = ["gunslinger", "vanguard", "wayfarer"]


def _get_save_dir():
    """返回存档目录，确保目录存在（不可写时返回 None）。"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    save_dir = os.path.join(base, APP_DIR_NAME)
    try:
        os.makedirs(save_dir, exist_ok=True)
        return save_dir
    except OSError:
        return None


def _migrate_legacy_save():
    """旧存档存在且新位置无存档时，迁移一次（失败不阻塞）。"""
    if os.path.exists(SAVE_PATH):
        return
    if not os.path.exists(LEGACY_SAVE_PATH):
        return
    save_dir = _get_save_dir()
    if not save_dir:
        return
    try:
        with open(LEGACY_SAVE_PATH, "r") as src, open(SAVE_PATH, "w") as dst:
            dst.write(src.read())
    except OSError:
        pass


def _default_data():
    """R5 完整 schema 默认值。"""
    return {
        "high_score": 0,
        "unlocks": {k: False for k in _UNLOCK_KEYS},
        "meta": {
            "total_kills": 0,
            "total_score": 0,
            "total_runs": 0,
            "best_time": 0.0,
            "boss_kills": 0,
            "victories": 0,
            # 扩展字段：单局击杀纪录（支撑"单局击杀 N"类解锁条件，§3.2-3.4）
            "best_run_kills": 0,
            "per_character": {"default": {"kills": 0, "runs": 0}},
        },
        "settings": {"volume_music": 0.7, "volume_sfx": 0.8},
    }


def _merge_defaults(data):
    """把磁盘数据合并进默认 schema（向后兼容旧档：缺字段按默认值）。"""
    d = _default_data()
    if not isinstance(data, dict):
        return d
    if isinstance(data.get("high_score"), (int, float)):
        d["high_score"] = data["high_score"]
    if isinstance(data.get("unlocks"), dict):
        for k in _UNLOCK_KEYS:
            if k in data["unlocks"]:
                d["unlocks"][k] = bool(data["unlocks"][k])
    m = data.get("meta")
    if isinstance(m, dict):
        for k in d["meta"]:
            if k in m and isinstance(m[k], (int, float, str, bool)) and k != "per_character":
                d["meta"][k] = m[k]
        if isinstance(m.get("per_character"), dict):
            for ch, v in m["per_character"].items():
                if isinstance(v, dict):
                    d["meta"]["per_character"][ch] = {
                        "kills": int(v.get("kills", 0)),
                        "runs": int(v.get("runs", 0)),
                    }
    if isinstance(data.get("settings"), dict):
        for k in d["settings"]:
            if k in data["settings"]:
                d["settings"][k] = data["settings"][k]
    return d


def _load():
    """读取完整存档（含默认合并）；新路径优先，其次旧路径。"""
    _migrate_legacy_save()
    for path in (SAVE_PATH, LEGACY_SAVE_PATH):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return _merge_defaults(data)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            continue
    return _default_data()


def _save(data):
    """全量落盘：新路径优先，不可写时回退旧路径。"""
    try:
        save_dir = _get_save_dir()
        if save_dir:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
    except OSError:
        pass
    try:
        with open(LEGACY_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# ---------- 最高分（保留旧接口，但不再覆盖新字段） ----------

def load_high_score():
    """读取最高分：新路径优先，其次旧路径。"""
    return _load()["high_score"]


def save_high_score(score):
    """保存最高分；仅在超过历史纪录时写入，返回是否为新纪录。

    注意：R5 起改为全量 load-modify-save，避免覆盖 unlocks/meta/settings。
    """
    data = _load()
    if score <= data["high_score"]:
        return False
    data["high_score"] = score
    return _save(data)


# ---------- Meta（R5 统计） ----------

def load_meta():
    """读取 meta 字典（含默认值，返回副本）。"""
    return _load()["meta"]


def save_meta(delta):
    """增量写 meta：delta 为 meta 字段字典（per_character 支持嵌套合并），落盘。"""
    if not isinstance(delta, dict):
        return False
    data = _load()
    meta = data["meta"]
    for k, v in delta.items():
        if k == "per_character" and isinstance(v, dict):
            for ch, pc in v.items():
                if not isinstance(pc, dict):
                    continue
                cur = meta["per_character"].setdefault(ch, {"kills": 0, "runs": 0})
                cur["kills"] = int(pc.get("kills", cur["kills"]))
                cur["runs"] = int(pc.get("runs", cur["runs"]))
        elif k in meta:
            meta[k] = v
    return _save(data)


def record_run_result(character, *, kills=0, boss_kills=0, score=0, elapsed=0.0, victory=False):
    """结算一次性写入（防频繁 I/O）：更新 meta 并刷新解锁。

    - kills/boss_kills：本局击杀数（普通 + Boss）
    - score：本局得分；elapsed：本局存活时间；victory：是否胜利
    """
    data = _load()
    meta = data["meta"]
    meta["total_kills"] += int(kills)
    meta["total_score"] += int(score)
    meta["total_runs"] += 1
    if elapsed > meta["best_time"]:
        meta["best_time"] = float(elapsed)
    if kills > meta["best_run_kills"]:
        meta["best_run_kills"] = int(kills)
    meta["boss_kills"] += int(boss_kills)
    if victory:
        meta["victories"] += 1
    pc = meta["per_character"].setdefault(character, {"kills": 0, "runs": 0})
    pc["kills"] += int(kills)
    pc["runs"] += 1
    _save(data)
    refresh_unlocks()


# ---------- 解锁状态（R5） ----------

def load_unlocks():
    """读取解锁状态字典（返回副本）。"""
    return dict(_load()["unlocks"])


def is_unlocked(character):
    """角色是否已解锁（default 恒 True）。"""
    if character == "default":
        return True
    return bool(_load()["unlocks"].get(character, False))


def unlock_character(character):
    """手动解锁某角色（写 unlocks，重启保留）。"""
    if character == "default" or character not in _UNLOCK_KEYS:
        return False
    data = _load()
    data["unlocks"][character] = True
    return _save(data)


def refresh_unlocks():
    """依据当前 meta 重新评估各角色解锁条件，有变化才落盘。返回最新 unlocks。"""
    from characters import CHARACTERS
    data = _load()
    changed = False
    for ch, cfg in CHARACTERS.items():
        cond = cfg.get("unlock_condition")
        if cond is None:
            continue
        if not data["unlocks"].get(ch, False) and cond(data["meta"]):
            data["unlocks"][ch] = True
            changed = True
    if changed:
        _save(data)
    return data["unlocks"]
