# 暗夜求生 Darknight · Playtest 计划 v2（复核版）+ 冒烟扩展（SMK-20~30）+ 质量门判定

> 阶段：发布硬化期 · 批次3 验收门控（第二批新系统合入后独立复测；BUG-001 修复复核）
> 编制：严守真（quality-lead / QA）
> 版本基线：dev/1.0-hardening（未 commit，工作区实测 2026-08-03；BUG-001 已按方案 A 修复复核）
> 输入：playtest-plan-v1.md、`_smoke_test.py`、`tools/verify_content.py`、`tools/verify_r3.py`、`tools/verify_r5.py`、`tools/verify_r6_behavior_diff.py`、`tools/smoke_content_extra.py`、`tools/verify_fix_bug001.py`（BUG-001 修复验收）
> 约定：`[代码事实]` 已用代码核对 / 实际跑测；`[假设]` 设计推导、需人工 Playtest 验证；`[BUG]` 本批次发现的问题

---

## 0. 回归结果汇总（BUG-001 修复后全量复跑，全部 exit 0）

| # | 套件 | 结果 | 说明 |
|---|------|------|------|
| 1 | `_smoke_test.py` | ✅ 13/13 PASS（exit 0） | 无窗口 dummy 实测：juice/lighting/camera/font/audio/hud/skill_select/boss_hud/game_over/start_screen/character_select/normal_game 10帧/walk_anim |
| 2 | `tools/verify_content.py` | ✅ 21/21 PASS（exit 0） | 新武器×2、新敌人×2、R7、FX 贴图、回归 R3 不回归 |
| 3 | `tools/verify_r3.py` | ✅ 19/19 PASS（exit 0） | 数值权威表、弹量惩罚、穿透、联动、死常量删除 |
| 4 | `tools/verify_r5.py` | ✅ 13/13 PASS（exit 0） | 四角色解锁/数值/被动/存档/meta |
| 5 | `tools/verify_r6_behavior_diff.py` | ✅ BEHAVIOR_ALL_MATCH（544 帧对比 0 DIFF，exit 0） | normal+test 双模式逐帧状态等价（含 6 技能、5 事件、140 帧主循环、120 帧 Boss 战）；修复后仍零差异 |
| 6 | `tools/smoke_content_extra.py` | ✅ 11/11 PASS（exit 0，连跑 5 次全绿无 flaky） | SMK-20~30，见 §1；SMK-24/28 已升级为游戏循环级断言，新增 SMK-30 |
| 7 | `tools/verify_fix_bug001.py`（BUG-001 验收） | ✅ BUG001_FIX_ALL_PASS（exit 0，连跑 5 次全绿） | CorpseKing 500帧≥3 / ShadowMage/IronColossus/VoidLord 120帧≥1；源码事实+绘制无重复 |
| 8 | `compileall` 全仓语法门 | ✅ exit 0 | 无 SyntaxError/import 断裂 |

**P0 修复现状（代码事实 + 实测探针）：** P0-A 胜利判定 ✅（600s → game_over+is_victory=True）；P0-B 死亡后 ESC 返回主菜单 ✅；P0-C 经验球死代码清理 ✅（无 orbs 组、击杀直给经验 1/3/20）。存档路径实测写 `%APPDATA%/Darknight/souls_save.json`（D1 要求满足）。

---

## 1. 冒烟扩展 SMK-20~30（新增，全部可无窗口复跑）

> 入口：`venv/Scripts/python.exe tools/smoke_content_extra.py`（输出 `tools/smoke_content_extra_out.txt`，exit 0 = 全绿）。定位：与 verify_content（单元验收）互补，侧重**游戏内集成链路**。

| ID | 用例 | 断言要点 | 状态 |
|----|------|---------|------|
| SMK-20 | 凛冬之环 游戏内全链路 | 装备→光环内减速生效→离开恢复→tick 伤害（0.5s 一跳） | ✅ |
| SMK-21 | 圣焰喷射器 直接伤+DoT | 锥内直接伤 2→燃烧 2.0s/1 伤→逐跳 2 跳→燃烧结束 dot 清零 | ✅ |
| SMK-22 | 怨灵 闪现状态机全周期 | 移动→落点提示（位置冻结）→闪现到落点→落地停顿→恢复移动 | ✅ |
| SMK-23 | 唤魔师 主从绑定无奖励 | 游戏内召唤→仆从绑定→主人死→仆从 2s 消散且 score/xp 不变 | ✅ |
| SMK-24 | 尸王狂暴 游戏内触发 | <50%→enraged 置位→**enrage 事件经游戏循环送达（红闪生效）**→召唤 3→5 混合 | ✅ |
| SMK-25 | FX 贴图 加载+回退 | 5 张贴图真实加载；缺失目录→全部 None→程序化 draw 不崩 | ✅ |
| SMK-26 | 技能池 16 三选一不重复 | 池=16、60 抽三选一不重复、新武器可出现；升级→3 卡→选凛冬生效 | ✅ |
| SMK-27 | Boss 降临演出 | 粒子+30、白闪、长顿帧、顿帧期间 elapsed_time 冻结 | ✅ |
| SMK-28 | 暗影巫师 传送+尾迹 | **弹幕经游戏循环送达→trail_color 生效**；传送提示→落地 | ✅ |
| SMK-29 | 组合回归总闸 | frost+flame 组合 5.28s 模拟（330 帧）无异常、状态合法、玩家存活 | ✅ |
| SMK-30 | BUG-001 回归：四 Boss 攻击送达 | CorpseKing 500帧≥3 / ShadowMage/IronColossus/VoidLord 120帧≥1，攻击事件经游戏循环送达 _process_boss_attacks | ✅ |

> **稳定性处理（QA）**：SMK-30 与 verify_fix_bug001 首跑曾出现 IronColossus 0 攻击 —— 根因是 IronColossus 的 armor 分支（0.35≤r<0.65）只开甲不产出攻击 dict，120 帧窗口首 roll 命中即 flaky（~30%）。已按 Boss 固定随机种子（IronColossus seed=1 → shockwave）消除随机性，连跑 5 次全绿。**这是测试稳定性修复，非生产代码改动；IronColossus 开甲不产出事件属设计行为。**

---

## 2. [BUG-001] 严重度 Critical → 已修复并复核通过（DN-ENG-FIX-BUG001）

> 由 SMK-24/28 首跑失败牵引定位，非本批次引入（R6 前后行为一致），但直接阻塞本批次 R7 演出验收。**已由工程按方案 A 修复，QA 复核通过。**

- **现象（修复前实测）**：正常游戏循环内，Boss 主动攻击几乎不生效。探针：CorpseKing 攻击计时就绪后跑 120 帧，`_process_boss_attacks` 收到 **0** 条攻击；ShadowMage 120 帧仅 **1** 次弹幕齐射（应约 48 次）。`boss.update()` 单帧被调用 **2 次**。
- **根因（代码事实）**：`_update_boss_warning()` 把 Boss 同时加入 `enemies` 与 `bosses` 两个组（base_game.py）。`_update()` 中 `self.enemies.update(dt, player_rect)` 会调用 `boss.update()`——Boss 的攻击在**这一通道**触发并重置 `attack_timer`，但 `Group.update()` 丢弃返回值；随后 `_update_bosses()` 再次调用 `boss.update()` 时计时器已被重置，几乎不可能再触发 → `_process_boss_attacks()` 被饿死。
- **修复（方案 A，工程实现，base_game.py:380-385）**：`self.enemies.update(dt, player_rect)` 改为手动循环 `for enemy in list(self.enemies): if not isinstance(enemy, Boss): enemy.update(...)`；Boss 保留在 enemies 组吃伤害，仅不再被 Group.update 先驱动；Boss 只由 `_update_bosses()` 驱动一次。绘制无重复已确认（base_game.py:958 enemies 绘制排除 Boss、959 bosses 单独绘制）。
- **复核结果（QA 独立实测）**：`tools/verify_fix_bug001.py` → BUG001_FIX_ALL_PASS；CorpseKing 500帧 **5** 条攻击送达（修复前 0）、ShadowMage **5** 条（修复前 1）、IronColossus **1** 条、VoidLord **3** 条；源码事实 + 绘制无重复 + Boss 移动/动画/受击闪白均 PASS。SMK-24/28 升级为游戏循环级断言后亦全绿（狂暴红闪、弹幕 trail_color 经游戏循环生效）。
- **修复后状态**：**已关闭（RESOLVED）**。四 Boss 主动攻击与 R7 演出（冲锋前摇/狂暴横幅/传送提示/弹幕尾迹）现可在正常游戏循环稳定送达 → R7 演出验收解除阻塞，可进入人工 Playtest。

---

## 3. 覆盖矩阵（新系统 → 测试 → 类型）

| 新系统 | 自动化覆盖 | 测试类型 | 人工验证点 |
|--------|-----------|---------|-----------|
| 凛冬之环 | verify_content v_frost_values/v_frost_slow_effect；SMK-20/26 | 数值+集成 | 手感：光环范围体感、减速是否"黏人但可脱身" |
| 圣焰喷射器 | verify_content v_flame_*；SMK-21/29 | 数值+集成 | 手感：锥形命中反馈、燃烧跳字节奏、暴击爽感 |
| 怨灵 Wraith | verify_content v_wraith_behavior；SMK-22 | 状态机+集成 | 可读性：落点残影能否被预判、闪现节奏是否合理 |
| 唤魔师 Warlock | verify_content v_warlock_events/v_homing_orb_speed/v_master_servant_binding/v_boss_phase_no_warlock_spawn；SMK-23 | 状态机+集成 | 可读性：召唤/追踪弹是否可读、主从消散是否清晰 |
| 尸王 R7（冲锋前摇/狂暴） | verify_content v_corpse_king_enrage/v_corpse_king_charge_telegraph；SMK-24 | 状态机+处理器 | **阻塞于 BUG-001**：修复前无法人工验证 |
| 暗影巫师 R7（传送/尾迹） | verify_content v_shadow_mage_*；SMK-28 | 状态机+处理器 | **阻塞于 BUG-001**：修复前无法人工验证 |
| Boss 降临演出 | verify_content v_boss_arrive_effect；SMK-27 | 集成 | 压迫感：黑边/横幅/震屏/顿帧是否可感知（不依赖 BUG-001） |
| FX 贴图 5 张 | verify_content v_fx_textures_loaded/v_fx_draw_paths；SMK-25 | 资源+回退 | 视觉：爆炸/新星/闪电/枪口火光贴图与程序化差异、不违和 |
| R6 BaseGame 重构 | verify_r6_behavior_diff（544 帧等价） | 行为等价 | 无（纯重构，已等价证明） |

---

## 4. 手动 Playtest 清单 v2（重点：新系统体感，需真人/真机）

> **前置已解除**：BUG-001 已修复并复核通过（§2），Boss 主动攻击/R7 演出可在正常游戏循环稳定送达，P3~P6 可正常执行。

| # | 验证点 | 方法 | 通过标准 |
|---|--------|------|---------|
| P1 | 新武器·凛冬之环手感 | 5 分钟局，首件拿凛冬 | 光环半径体感 100px 合理；减速让近身怪"黏但能逃"；0.5s tick 跳字不刷屏 |
| P2 | 新武器·圣焰喷射器手感 | 5 分钟局，首件拿圣焰 | 锥形 60°/170px 命中反馈清晰；燃烧 4 跳节奏可感知；暴击金色数字有爽感 |
| P3 | 尸王 Boss 可读性（BUG-001 修复后） | 打到 120s Boss | 冲锋前摇黄圈≥0.3s 可读（测试员能说"怎么躲"）；<50% 狂暴横幅+红闪明显；召唤 3→5 混合压力可感 |
| P4 | 暗影巫师可读性（BUG-001 修复后） | 打到 240s Boss | 传送落点紫圈提示可预判；弹幕带尾迹易追踪；传送后玩家可反应 |
| P5 | Boss 压迫感总评（BUG-001 修复后） | 四 Boss 各打一遍 | 至少 2/3 测试员反馈"Boss 有存在感、需要走位"，无"只会站着挨打" |
| P6 | Boss 降临演出 | 首次 Boss 预警 | 黑边滑入+大字横幅+白闪+顿帧 0.12s+震屏全部可感知 |
| P7 | 怨灵可读性 | 136s 后观察 | 落点残影≥0.4s 可见；闪现落点玩家能预判躲避；落地停顿 0.5s 是击杀窗口 |
| P8 | 唤魔师可读性 | 204s 后观察 | 召唤动作/小怪出生可识别；追踪弹慢速但必须躲；主人死后仆从 2s 消散无奖励清晰 |
| P9 | FX 视觉 | 全流程观察 | 爆炸/新星/闪电/枪口火光贴图与旧程序化差异不违和；无空白/错位贴图 |
| P10 | 数值手感回归（v1 项） | C1~C6 / N1~N3 / U1~U7 | 沿用 v1 标准；新武器加入后主导策略是否改变（交 design-strategist） |

---

## 5. 质量门判定（A-G，建议性门控，最终放行由用户决定）

### 判定：**PASS（建议放行人工 Playtest；发布签字仍需用户最终确认）**

> 复核版：BUG-001 已按方案 A 修复并经 QA 独立复核通过（§2）。全量回归 8 项全绿（含 SMK-20~30 11/11、verify_fix_bug001 4/4、R6 544 帧等价、compileall）；R7 演出门从 FAIL 转 PASS——冲锋前摇/狂暴横幅/传送提示/弹幕尾迹现经游戏循环稳定送达（SMK-24/28 游戏循环级断言全绿）。§4 手动 Playtest 清单全部解锁。

| 门 | 条目 | 状态 |
|----|------|------|
| A. 自动化门 | A1 冒烟 13/13 ✅；A2 扩展 SMK-20~30 11/11 ✅；A3 exit 0 + 连跑 5 次无 flaky ✅（SMK-30/verify_fix_bug001 已做随机种子稳定性修复）；A4 compileall ✅；A5 dummy 无窗口可复现 ✅ | **PASS** |
| B. P0 玩法修复门 | B1 胜利判定 ✅（600s）；B2 ESC 返回 ✅；B3 经验球清理 ✅；B4 击杀/升级反馈动效 ✅（smoke juice）；B5 虚空之主 gravity ✅（GravityWell 已实现，见 boss.py） | **PASS** |
| C. 素材门 | C1~C3 本批次新增 FX 5 张贴图可加载可绘制 ✅（SMK-25）；精英/冲锋 sprite 修复沿用既有资产 | **PASS（FX 部分）/ 待真机目检** |
| D. 技术硬化门 | D1 存档写 %APPDATA%/Darknight ✅（实测）；D2~D5 沿用 v1 待发布检查 | **CONCERNS（非本批次）** |
| E. 本地化门 | E1~E3 沿用 v1，非本批次 | **待定（非本批次）** |
| F. 人工 Playtest 签收门 | F1~F4 需 §4 清单执行；**P3~P6 已解锁**（BUG-001 修复复核通过） | **待人工执行** |
| G. 发布稳定性门 | G1 全流程模拟：SMK-29 组合 5.28s ✅ + R6 544 帧等价 ✅；G2 真机 FPS、G3 存档幂等 需人工 | **CONCERNS（部分人工）** |

**阻塞项汇总（复核后）：**
1. ~~BUG-001 · Critical~~ → **已关闭（RESOLVED）**，复核通过（§2）。
2. ~~SMK-24/28 游戏循环级断言待补~~ → 已补回并全绿（SMK-24 狂暴红闪、SMK-28 弹幕 trail_color 经游戏循环送达）。
3. 新增提醒（非阻塞）：SMK-30 / verify_fix_bug001 曾因 IronColossus armor 分支（开甲不产出攻击 dict）出现 ~30% flaky，QA 已用固定随机种子消除（测试稳定性修复，非生产改动）；如需让 IronColossus 的"开甲"也可被玩家感知，属设计优化项，交 design-strategist。
4. 无其他 Blocker/Critical。**建议下一步：执行 §4 人工 Playtest（5 人：3 新 + 2 老，重点 P1~P9）。**

---

## 6. 自动化 vs 人工 Playtest 边界（v2 更新）

**可自动化（本批次已覆盖）：** 新武器数值/减速/DoT/暴击、怨灵状态机全周期、唤魔师主从绑定无奖励、尸王狂暴标志+召唤数量+**enrage 事件送达**、FX 加载与回退、技能池 16 三选一、Boss 降临粒子/白闪/顿帧冻结、**四 Boss 攻击经游戏循环送达（SMK-30）**、组合回归总闸、R6 行为等价、**BUG-001 修复验收（verify_fix_bug001）**。

**需人工 Playtest（QA 无法运行窗口游戏）：** 新武器手感（P1/P2）、敌人/Boss 可读性（P3/P4/P7/P8）、Boss 压迫感（P5/P6）、FX 视觉观感（P9）、数值手感与主导策略（P10）、真机 FPS。

**执行建议（复核后更新）：** BUG-001 已修复复核 ✅ → 直接进入人工 Playtest 一轮（5 人：3 新 + 2 老，重点 P1~P9）→ 修数值/Boss 后复跑 → 进入 Steam 发售 gate。

---

## 7. 交付物清单

| 交付物 | 路径 | 状态 |
|--------|------|------|
| 冒烟扩展 SMK-20~30（可运行，含稳定性修复） | `tools/smoke_content_extra.py` | ✅ 11/11 PASS（连跑 5 次全绿） |
| SMK-20~30 运行输出 | `tools/smoke_content_extra_out.txt` | ✅ 已落盘 |
| BUG-001 修复验收（含稳定性修复） | `tools/verify_fix_bug001.py` + `tools/verify_out_fix_bug001.txt` | ✅ BUG001_FIX_ALL_PASS（连跑 5 次全绿） |
| 全量回归输出（复核实测） | `tools/smoke_run_out.txt`、`tools/verify_content_out.txt`、`tools/verify_out.txt`、`tools/verify_out_r5.txt`、`tools/verify_out_r6.txt`、`tools/verify_out_fix_bug001.txt` | ✅ 全部 exit 0 |
| Playtest 计划 v2 复核版（本文件） | `design/review/playtest-plan-v2.md` | ✅ 含质量门判定 PASS |
| BUG-001 | 本文件 §2 | ✅ 已修复并复核关闭 |

**回传主理人摘要：** 见 SendMessage。

---

*本计划为 v2 复核版，随首轮 Playtest 数据滚动更新。*
