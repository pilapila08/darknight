"""多语言字符串表（起步版）。

中文为默认值；后续补充英文等语言时，在 TRANSLATIONS 中按语言键添加覆盖即可。
用法：
    from i18n import t, set_lang
    set_lang("en")          # 切换语言（当前仅 zh 有完整文案）
    text = t("start_button")  # 查询字符串，未知键回退中文
"""

LANG = "zh"

_STRINGS = {
    # --- 窗口标题 / 版本 ---
    "window_caption": "暗夜求生 Darknight Survival v1.0 | F11 全屏",
    "window_caption_test": "暗夜求生 Darknight Survival v1.0 - 测试模式 | F11 全屏",

    # --- 开始界面 ---
    "start_title": "暗 夜 求 生",
    "start_subtitle": "Darknight Survival",
    "start_help_move": "WASD / 方向键  移动",
    "start_help_auto_fire": "自动瞄准最近敌人开火",
    "start_help_xp": "击杀敌人获取经验  →  升级  →  选择强化",
    "start_weapons_header": "武器系统：",
    "start_weapon_nova": "  暗影新星 — 周期性释放范围冲击波",
    "start_weapon_lightning": "  连锁闪电 — 弹跳打击多个敌人",
    "start_weapon_trap": "  剧毒地雷 — 自动释放毒圈",
    "start_enemy_unlock": "敌人类型会随时间逐渐解锁",
    "start_button": "开 始 游 戏",
    "start_hint": "按 空格键 开始游戏",
    "start_test_mode": "测试模式 (T)",

    # --- 结算界面 ---
    "game_over_victory": "胜利",
    "game_over_defeat": "游戏结束",
    "game_over_time": "存活时间",
    "game_over_kills": "击杀敌人",
    "game_over_level": "达到等级",
    "game_over_high_score": "最高分",
    "game_over_new_record": "★ 新纪录 ★",
    "game_over_restart": "重新开始",
    "game_over_hint": "按 SPACE 或点击按钮",
}

# 各语言覆盖表：{lang: {key: translated_text}}。en 为占位，待本地化后填充。
TRANSLATIONS = {
    "zh": {},
    "en": {
        # TODO(i18n): 英文文案待本地化
    },
}


def set_lang(lang):
    """切换当前语言（如 "zh" / "en"）。"""
    global LANG
    LANG = lang


def get_lang():
    """返回当前语言。"""
    return LANG


def t(key):
    """按当前语言返回字符串；未翻译或未知键回退中文/原键。"""
    text = _STRINGS.get(key)
    if text is None:
        return key
    table = TRANSLATIONS.get(LANG)
    if table:
        return table.get(key, text)
    return text
