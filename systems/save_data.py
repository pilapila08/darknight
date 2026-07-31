"""最高分存档：写入 %APPDATA%/Darknight/（跨平台回退用户主目录）。

- 新路径：<APPDATA 或 ~>/Darknight/souls_save.json
- 旧路径：程序当前目录 souls_save.json（v3.8 及以前）
- 首次运行时若旧存档存在且新路径无存档，则自动迁移一次；
  读取时也兼容旧位置，保证玩家历史最高分不丢失。
- 新路径不可写时回退旧路径，优先保证功能可用。
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


def _read_score_from(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("high_score", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_high_score():
    """读取最高分：新路径优先，其次旧路径。"""
    _migrate_legacy_save()
    for path in (SAVE_PATH, LEGACY_SAVE_PATH):
        score = _read_score_from(path)
        if score is not None:
            return score
    return 0


def save_high_score(score):
    """保存最高分；仅在超过历史纪录时写入，返回是否为新纪录。"""
    current = load_high_score()
    if score <= current:
        return False
    save_dir = _get_save_dir()
    try:
        if save_dir:
            with open(SAVE_PATH, "w") as f:
                json.dump({"high_score": score}, f)
            return True
    except OSError:
        pass
    # 新路径不可写时回退旧路径
    try:
        with open(LEGACY_SAVE_PATH, "w") as f:
            json.dump({"high_score": score}, f)
        return True
    except OSError:
        return False
