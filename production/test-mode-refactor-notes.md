# 测试模式重构说明（DN-ENG-TEST-R1）

> 分支：dev/1.0-hardening（工作区含 R6 重构 / C02 第二批 / BUG-001~005 未提交改动，本次在其上原地重构，**未 commit 未 push**）
> 重构范围：`game/test_game.py`、`game/test_mode.py`、`ui/test_panel.py`、`ui/__init__.py`、`entities/enemy_types.py`（新增统一敌种表）、新增 `tools/verify_test_mode.py`
> 约束遵守：`game/normal_game.py` 未改动；BaseGame 钩子签名未动；game_state 键名 `test_xp_multiplier` 未动（保留镜像）。

## 1. 结构变化（对应七条混乱点 → 六条重构规格）

| # | 混乱点 | 重构后 |
|---|--------|--------|
| 1 | `_handle_test_mode_click` ~130 行巨型 if/elif | 按面板分区拆分为 6 个 `_handle_*_zone_click` 方法（玩家控制 / 自定义敌 / 敌种快速生成 / 技能 / Boss / 调试），点击入口仅做分区路由 |
| 2 | 7 个散落 rect 函数 + test_game:207 方法内延迟 import | `ui/test_panel.py` 新增唯一入口 `build_test_layout(...)` 返回结构化 dict；旧 `get_test_*` 保留为委托兼容别名；test_game 延迟 import 已消灭 |
| 3 | 状态三处存放（handler / game_state / TestGame 实例属性） | 新建 `TestPanelState` dataclass（`game/test_mode.py`），全部面板状态收敛到 `handler.state`；TestGame 只持有 `test_handler` 一个引用。`game_state.test_xp_multiplier` / `test_auto_spawn` 保留为**镜像键**（BaseGame 钩子兼容，勿删），写入统一走 `_set_xp_multiplier` / `_toggle_auto_spawn` |
| 4 | `_enemy_types` 缺 C02 新敌 wraith/warlock | 统一表 `ENEMY_TYPE_DEFS`（7 种）定义在 `entities/enemy_types.py`（类型定义天然归属，规避 ui→game→entities→ui 循环导入）；测试面板 / 快速生成 / 自定义敌种选择全部走该表。wraith/warlock 生成复用 `BaseGame._spawn_enemy`（C02 已实现路径，不重复实现）；Boss 战过滤逻辑不受影响（`_spawn_enemy` override 分支直达构造） |
| 5 | Boss 按钮 y hack + 清屏藏在第 5 个按钮 | Boss 按钮按 `BOSS_CONFIGS` 枚举（4 Boss + 独立"清屏"按钮），位置由 `build_test_layout` 统一计算（`boss_toggle.bottom + 5 + i*33` 移入布局）；点击时 `i < len(BOSS_CONFIGS)` 判定 Boss，否则 `_clear_test_enemies()`；Boss 生成后正确加入 `enemies + bosses` 双组并置 `boss_active` |
| 6 | KEYDOWN.unicode 不可靠 + 魔法字符串 | 改用 `pygame.TEXTINPUT` 事件收集（与 main.py 主菜单一致）；`TestGame._init_extra` 中 `start_text_input()` + `set_allowed(TEXTINPUT)`（BaseGame 构造时 stop+blocked，此处放开）；输入框标识用 `TestInputField.HP/DAMAGE/SPEED` 常量 |
| 7 | handler 生成逻辑高度重复 | `TestModeHandler._build_enemy(...)` 单一生成入口：wraith/warlock 走 `game._spawn_enemy`，其余走定义表 `cls`，自定义数值（hp/speed/damage）构造后统一覆写；exploder 保留旧行为（无接触伤害，爆炸伤害=damage×2） |

## 2. 消灭规模

- `game/test_game.py`：`_handle_test_mode_click` 巨型链 → 6 个分区方法；`_enemy_types` 实例属性删除；`active_input_field/enemy_panel_expanded/boss_panel_expanded/debug_stats_enabled/custom_enemy_type` 等 5 个实例属性删除（全部进 `TestPanelState`）。
- `ui/test_panel.py`：7+ 散落 rect 函数收敛为 `build_test_layout` 单一入口（旧名保留为委托别名，兼容外部调用）。
- `game/test_mode.py`：新增 `TestPanelState` + `_build_enemy` + 输入处理；`spawn_enemy_near_player` / `spawn_custom_enemy_with_type` 增加 `game=None` 参数（向后兼容）。

## 3. 行为修正（明确记录）

- **xp_apply 语义修正（bug→设计确认）**：旧 `xp_apply` 把 `test_xp_multiplier` 清零（与"经验x{value}"显示及 -/+ 实时改值矛盾，且面板按钮文案为"x0禁止"）。按任务要求改为**"应用当前值"语义**：`_set_xp_multiplier(state.xp_multiplier)`（不改变 -/+ 已调整的值）。若需禁止经验，仍可用 xp_- 减到 0。按钮文案由"x0禁止"改为"应用"。`state.py` 注释"设为0可禁止经验获取"仍成立（通过 - 达成）。
- **布局重排（允许）**：技能图标由左下（6×3 行、底部锚定）改为左上 4×4 网格（y 60–236）；敌种快速生成按钮由 1 列 5 个改为 2 列 4 行 7 个；修复了旧布局中**自动生成开关与 Boss 折叠按钮同坐标重叠**（旧 `get_test_auto_spawn_rect(False)` 与 `get_test_boss_toggle_rect(False)` 同为 (15,215)）以及**调试按钮被自定义敌面板背景遮挡**（旧 debug 在 sh-430，被 sh-520 起、高 185 的面板盖住）两个隐藏 UI 缺陷。
- **自定义敌人 exploder**：保持旧行为（contact_damage=0，爆炸伤害=damage×2），测试已断言。

## 4. 验证

新增 `tools/verify_test_mode.py`（无窗口 dummy 驱动，输出 `tools/verify_out_test_r1.txt`），13 条全绿：
1. 结构回归：无方法内延迟 import / 无散落敌种表 / 7 敌种表
2. 布局单一入口：7 敌种 / 4 Boss+清屏 / 16 技能 / Boss 按钮不与技能区重叠
3. ① 敌种快速生成 7 种可 spawn（含 wraith/warlock，断言 Wraith 走 C02 `_spawn_enemy` 路径）
4. ①b 面板点击快速生成 7 种（真实 MOUSEBUTTONDOWN 事件路径）
5. ② 自定义敌人 7 类型可生成，hp/speed/damage 生效
6. ②b 自定义敌种选择 + 生成按钮（点击路径，选 warlock 断言类型）
7. ③ 4 Boss + 独立清屏按钮（Boss 进 enemies+bosses 双组；清屏保留 Boss）
8. ④ 自动生成开关单一源同步（state ↔ game_state 镜像 ↔ `_should_spawn_auto`）
9. ⑤ 技能面板点击 16 技能不崩（含 frost/flame）
10. ⑥ 输入框 TEXTINPUT 收集 + Backspace/ESC/点击外部取消
11. ⑦ 测试面板渲染多状态不崩
12. ⑦b 全帧渲染不崩（含武器管理器 / Boss 预警）
13. 保留功能：玩家控制 -/+/应用/满血/+100/+500 经验

全量回归（`tools/verify_out_test_r1.txt` 合并输出，全部 exit=0 / ALL_PASS）：
- `_smoke_test.py` → SMOKE_ALL_PASS
- `tools/verify_content.py` → CONTENT_VERIFY_ALL_PASS
- `tools/verify_r3.py` → VERIFY_ALL_PASS
- `tools/verify_r5.py` → VERIFY_ALL_PASS
- `tools/verify_fix_bug001.py` → BUG001_FIX_ALL_PASS

## 5. 风险点 / 后续建议

- **风险：布局坐标是硬编码常量**（`build_test_layout` 内）。本次已把散落坐标收敛到单一入口，若后续要适配多分辨率，需把布局改为相对定位/缩放。当前 SCREEN 1280×720 下无重叠（测试断言覆盖关键重叠）。
- **风险：`ui/test_panel.py` 依赖 `entities.enemy_types`**：为打破 ui→game→entities→ui 循环导入，敌种表放在 entities 层（合理归属）。若未来 game.test_mode 再被 ui 直接引用，注意勿引入循环。
- **风险：TEXTINPUT 全局放开**：TestGame 构造后 `set_allowed(TEXTINPUT)` 常开，但仅在输入框激活时消费（`_handle_pre_event` 返回 False 时 TEXTINPUT 事件静默落到其他处理器，类型不匹配不会被误处理）。无功能影响，但如担心事件队列噪音可在激活/取消时动态 allow/block（已留 `TestInputField` 常量为切换做准备）。
- **建议**：下一次可用 `tools/verify_test_mode.py` 作为测试模式回归基线；若扩展敌种/技能，只需改 `ENEMY_TYPE_DEFS` / `SKILL_POOL`，布局会自动按表长度展开（敌种按钮、type_i、技能网格均已按 len 驱动）。

---

# R2 沙盒化（DN-ENG-TEST-R2）

> 根因确认：用户实测"测试模式不能移动 / 加入敌人导致升级"——非移动代码问题，而是升级弹窗冻结：击杀累积经验 → `_check_level_up`（base_game.py:888）无条件触发 → `paused=True` + 3选1 → 游戏冻结（`_update` 顶部 `escaped or paused` 直接 return，移动无效）。

## 改动

1. **升级开关（默认关）**：
   - `TestPanelState.allow_level_up: bool = False`（game/test_mode.py）
   - `TestModeHandler.toggle_level_up()` 切换方法
   - `TestGame._check_level_up()` 覆写：`if not state.allow_level_up: return`（经验照常显示/累积，不弹窗不冻结；开启后走 `super()._check_level_up()` 原逻辑）
2. **重置按钮**：玩家面板新增"重置"→ `self._restart()`（BaseGame 已实现：`_init_game()` 重建 GameState/实体，`_init_extra` 重建 TestModeHandler → `TestPanelState` 自动回默认）。经验/等级/HP/技能/敌怪/Boss/面板状态全部归零。
3. **移动确认**：`_update` 中 `self.player.update(dt, keys)` 仅被 `game_over / escaped / paused` 阻断；升级冻结是唯一 pause 来源，默认关后移动自然恢复。TestGame 无其他 pause 干扰（已核查）。
4. **面板布局**：玩家面板 bg 高 150→200，新增两行：`upgrade_toggle`（升级开/关，y+140）与 `reset`（重置，y+168）；调试按钮从 sh-140 下移到 sh-90 避免与新面板底重叠。全部在 `build_test_layout` player 区，verify 断言按钮互不重叠 + 不与 debug 重叠。

## 新增验证（tools/verify_test_mode.py 共 18 条，全绿）
- SMK-新1：默认 allow_level_up=False → experience=10000 调 `_check_level_up` 后 level==1 / paused=False / chosen_skills=None / 经验保留
- SMK-新2：开启后 → level>1 / paused=True / chosen_skills 3 选 1 / max_hp+1
- SMK-新2b：升级开关按钮点击切换
- SMK-新3：重置按钮（含 Boss/技能/面板展开等非初始状态）→ 全部归零（敌人清空/HP 满/level 1/技能空/test_handler 默认）
- SMK-新3b：重置后 `_update`/`_render` 不崩（run 循环可继续）

## R2 全量回归（tools/verify_out_test_r2.txt）
_smoke_test.py SMOKE_ALL_PASS / verify_content.py CONTENT_VERIFY_ALL_PASS / verify_r3.py VERIFY_ALL_PASS / verify_r5.py VERIFY_ALL_PASS / verify_fix_bug001.py BUG001_FIX_ALL_PASS / verify_test_mode.py TEST_MODE_REFACTOR_ALL_PASS（全部 exit=0）。

## 风险 / 说明
- 升级开关关闭时经验仍累积；开启后 `_check_level_up` 每帧至多升 1 级，会以连升方式追赶积压经验（用户主动开启，符合预期）。
- 重置复用 `_restart`（读取 high_score 存档，只读）；TestGame 无特殊重置钩子需要补充（handler 由 `_init_extra` 重建）。
- 未 commit 未 push；NormalGame / BaseGame 钩子签名未改动。
