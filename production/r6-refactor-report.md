# R6 重构报告：NormalGame / TestGame 公共基类提取

- 迭代：R6（纯重构，行为零变化）
- 负责人：程基岩（engineering-lead）
- 分支：dev/1.0-hardening
- 范围：`game/` 模块（新增 `game/base_game.py`；原地重构 `game/normal_game.py`、`game/test_game.py`）
- 约束遵守：不 commit、不 push；不改数值/玩法/刷怪曲线/技能效果；对外接口兼容（R5 角色系统零回归）

---

## 1. 重构方案说明

### 1.1 问题

R6 之前两个游戏模式类各自维护一份几乎相同的核心循环：

- `game/normal_game.py`：1277 行（`NormalGame`）
- `game/test_game.py`：1216 行（`TestGame`）

两者约 2500 行高度重复：更新管线（`_update`）、渲染（`_render`）、刷怪（`_spawn_enemy`）、Boss 系统（`_check_boss_spawn` / `_update_boss_warning` / `_process_boss_attacks` / `_kill_boss`）、掉落（`_update_drops` / `_maybe_drop_item`）、技能应用（`_update_weapons` / `_apply_skill`）、碰撞（`_check_collisions`）等。任何玩法调整都必须在两处同步修改，是长期回归风险的源头。

### 1.2 目标结构

采用**模板方法模式 + 策略钩子（policy hooks）**：共享核心循环收敛到 `BaseGame`，两个模式类只保留“真正不同”的部分。

```
game/
├── base_game.py      # 新增：BaseGame —— 共享核心循环 + 37 个策略钩子（默认值 = Test 精简行为）
├── normal_game.py    # 重构：NormalGame(BaseGame) —— 打击感/光照/音频/数值面板 + 覆写钩子（约 384 行）
├── test_game.py      # 重构：TestGame(BaseGame)   —— 测试面板/文本输入/经验倍率/自动刷怪 + 覆写钩子（约 346 行）
├── state.py          # 未改动（GameState）
└── test_mode.py      # 未改动（TestModeHandler）
```

外部接口保持不变：

- `main.py`：`from game import NormalGame, TestGame` → `NormalGame(ch).run()` / `TestGame(ch).run()` 不变。
- `_smoke_test.py`：`NormalGame()` + `_init_game()` + `_update()` + `_render()` + `effects` / `_submit_lights` / `lighting` 全部保留。
- `game/__init__.py` 导出不变。

### 1.3 策略钩子（模式差异全部显式化）

BaseGame 内每个 `_xxx` 钩子都对应一处**原代码中真实存在的行为差异**；默认实现 = Test 的精简行为，NormalGame 覆写补全打击感/光照/音频。分组如下（37 个差异钩子 + 若干共享辅助方法）：

| 分组 | 钩子 | Normal 行为 | Test 行为（默认） |
|---|---|---|---|
| 初始化 | `_game_state_test_mode` | `False` | `True` |
| | `_init_extra` | effects/lighting/R4 计时器 | test_handler/orbs/面板状态 |
| 主循环 | `_frame_update` | `audio.update(dt)` | 无 |
| 事件 | `_handle_pre_event` | 无 | 文本输入框吞事件 |
| | `_handle_mode_click_event` | 无 | 测试面板点击 |
| | `_handle_mode_tail_event` | 数值显示开关 | 无 |
| | `_on_apply_skill` | `play_ui_click` | 无 |
| 更新管线 | `_update_juice` | effects + 顿帧冻结 | 无 |
| | `_should_spawn_auto` | 恒 True | `test_handler.should_spawn_enemies(True)` |
| | `_update_endgame_waves` | R4 增援波 + 终局冲锋 | 无 |
| | `_on_weapon_fired` | 枪口火光 | 无 |
| | `_on_lightning_hits` | 静电过载 CD 减免 | 无 |
| | `_on_pickup` | `play_pickup` | 无 |
| 刷怪/数值 | `_enemy_type_hp` | `CHARGER_HP/RANGER_HP/EXPLODER_HP` | `50/30/20`（面板数值） |
| | `_roll_elite` | R4 精英概率斜坡公式 | `≥120s 且 5%` |
| | `_spawn_special_enemy` | shadow/voidling（`sprite_name=None`） | shadow/voidling（默认 `"enemy"`） |
| | `_xp_mult` | `1.0` | `test_xp_multiplier` |
| 战斗反馈 | `_apply_hit_feedback` | 火花/音效/沿弹道击退 | 仅暴击击退 |
| | `_append_damage_number` | 暴击金色 `crit=` 标记 | 无 crit 标记 |
| | `_on_kill_enemy_juice` | 死亡残影 + 精英顿帧震动 | 无 |
| | `_on_exploder_killed` | 爆炸音效 + 震动 | 无 |
| | `_on_elite_killed` | 死亡回响 | 无 |
| | `_on_damage_player` | 受击闪屏 + `play_hurt` | 无 |
| Boss | `_on_boss_warning` | `play_boss_warning` | 无 |
| | `_clear_enemies_for_boss` | 无奖励清除（R4） | 走 `_kill_enemy` 有奖励 |
| | `_process_gravity_attack` / `_update_gravity_pull` | 虚空裂隙引力场 | 无 |
| | `_kill_boss_juice` | 顿帧/白闪/残影/音效 | 无 |
| | `_kill_boss_extra` | 死亡回响 | 无 |
| | `_on_map_transition` | `lighting.set_map` | 无 |
| 渲染 | `_render_mode_entities` | 无 | 经验球 |
| | `_render_world_juice` / `_render_screen_juice` | 世界层打击感 + 光照 | 无 |
| | `_render_mode_overlays` | 数值面板 | 测试面板 |
| | `_render_tail` | 技能→ESC→地图→结算（叠层顺序） | 地图→ESC→技能→结算 |
| | `_render_boss_warning` | 电影黑边/大字横幅 | 简易覆盖层 |
| | `_window_title` | 无前缀 | `[测试]` 前缀 |

> 说明：`_render_tail` 等“顺序不同”的差异也被显式保留，未强行统一叠层顺序（两模式原有叠层次序不同，属可观察行为）。

## 2. 消除行数统计

| 文件 | 行数（重构前） | 行数（重构后） | 变化 |
|---|---|---|---|
| `game/normal_game.py` | 1277 | 384 | −893 |
| `game/test_game.py` | 1216 | 346 | −870 |
| `game/base_game.py` | — | 1278（新增，共享核心） | +1278 |
| **合计** | **2493** | **2008** | **−485（−19.5%）** |

**真正的“重复消除量”**：原两个模式类各有一份几乎相同的核心逻辑；其中 **42 个方法同时存在于两个原类**，现全部收敛到 BaseGame 单份实现，约 **1182 行不再被复制两份**（旧 2× − 新 1×）。两个模式类各只剩 ~300 行“真正不同”的钩子与专属 UI/面板。

## 3. 风险点与验证方式

### 3.1 风险点

1. **钩子插入位置偏差**：差异点（如受击反馈、拾取音效、顿帧、清场奖励策略）一旦插错位置/顺序即改变行为。
2. **随机序列错位**：刷怪/暴击/掉落大量使用 `random`，任何重排都会改变后续整条随机序列。
3. **叠层/事件顺序差异**：`_render` 尾部叠层与 `_handle_events` 分支顺序两模式原本不同，强行统一会改变可观察表现。
4. **接口回归**：R5 角色系统（GameState stats / Player speed/max_hp / meta 写入）刚上线，严禁破坏。

### 3.2 验证方式（全部通过）

| 验证 | 命令 | 结果 |
|---|---|---|
| 冒烟测试 | `venv/Scripts/python.exe _smoke_test.py` | `SMOKE_ALL_PASS` |
| R3 数值验收 | `venv/Scripts/python.exe tools/verify_r3.py` | `VERIFY_ALL_PASS`（写 `tools/verify_out.txt`） |
| R5 角色验收 | `venv/Scripts/python.exe tools/verify_r5.py` | `VERIFY_ALL_PASS`（写 `tools/verify_out_r5.txt`） |
| **行为等价 diff**（新增） | `venv/Scripts/python.exe tools/verify_r6_behavior_diff.py` | `BEHAVIOR_ALL_MATCH`，544 个状态快照全部一致 |

**行为等价 diff 说明**（`tools/verify_r6_behavior_diff.py`）：从 git HEAD 提取原始 `NormalGame`/`TestGame`，与重构后版本分别实例化，喂入**相同随机种子 + 相同事件序列**，逐帧对比全部可观察状态（GameState 字段、玩家 rect/speed/max_hp、敌人/子弹/掉落/Boss/区域效果/陷阱/飘字/武器冷却/地图切换等）。覆盖：初始化、6 个技能连续应用（新星/闪电/地雷/穿透/火力/复苏）、5 个事件（ESC/技能确认/F11）、各 140 帧主循环、Boss 预警→生成→击杀全路径（120 帧）。**Normal 与 Test 两模式共 544 次对比，0 差异。**

## 4. 技术债清单处置（2026-07-31 清单）

| # | 债项 | 处置 |
|---|---|---|
| 1 | NormalGame/TestGame 核心循环高度重复 | ✅ **本迭代解决**：提取 `BaseGame`，共享核心单份化（见 §1/§2） |
| 2 | “暗影新星”保留 `has_blades` 旧字段，兼容代码扩散 7 个文件 | ⏸ **记录延后**：`tools/verify_r3.py` 明确断言 `st["has_blades"] == 1`，删除会破坏 R3 验收；R6 已将 `game/` 内两处引用收敛进 BaseGame（7 文件 → 5 文件：base_game/state/skills/ui/skill_select/verify_r3）。建议单独开“R3 兼容字段清理”任务，同步更新验收脚本 |
| 3 | `GameState.stats` 与 `get_default_stats()` 字典重复定义两遍 | ✅ **审计结论**：现源码中 `stats` 为实例属性、`get_default_stats()` 为唯一构造源（`reset()` 调用），**无字面重复**；疑为该债项在 R3 已部分清理。未改动（避免触碰 R5 数值断言） |
| 4 | `entities/player.py` 反向依赖 `ui/render_helpers.py` | ⏸ **记录延后**：属 `entities/` 层，超出 R6 `game/` 范围；且 `enemy.py` 同样依赖，改动会波及多文件。建议单独任务：把 `draw_ground_shadow` 等下沉到中性模块（如 `systems/`），保持纯函数无副作用即可零风险迁移 |
| 5 | `asset_loader.py` 与 `audio_manager.py` 音频合成职责重叠 | ⏸ **记录延后**：不影响本次核心循环重构；建议单独“音频职责单一化”任务 |
| 6 | README 项目结构过时 | ⏸ 按约定仅记录，不改 README |

## 5. 后续建议

1. 把 `tools/verify_r6_behavior_diff.py` 纳入回归套件（后续任何游戏循环改动可复用做行为等价验证）。
2. 单独排期处理债项 2/4/5（均不阻塞，且需配套更新验收脚本/回归测试）。
3. 若后续新增“第三种模式”，直接继承 `BaseGame` 并按需覆写钩子即可，无需再复制循环。

---

### 附：本次改动文件清单

- 新增：`game/base_game.py`
- 重构：`game/normal_game.py`、`game/test_game.py`
- 新增（验证工具）：`tools/verify_r6_behavior_diff.py`
- 产出报告：`production/r6-refactor-report.md`
