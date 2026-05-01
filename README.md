# 暗夜求生 (Darknight Survival)

类《吸血鬼幸存者》的俯视角自动射击 Roguelite 游戏。在黑夜中生存，击杀敌人，拾取经验，升级强化，挑战最高分。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行游戏
python main.py
```

## 操作说明

| 按键 | 功能 |
|------|------|
| `W` / `↑` | 向上移动 |
| `A` / `←` | 向左移动 |
| `S` / `↓` | 向下移动 |
| `D` / `→` | 向右移动 |
| `SPACE` | 开始游戏 / 重新开始 |
| `1` `2` `3` | 升级时选择对应技能 |
| `F11` | 切换全屏 |
| `ESC` | 退出游戏 |

## 游戏机制

### 核心循环
击败敌人 → 拾取经验球 → 升级 → 三选一强化 → 变强 → 面对更强的敌人

### 武器系统（通过升级逐步解锁）

| 武器 | 效果 | 叠加 |
|------|------|------|
| 自动枪 | 自动瞄准并射击最近敌人 | 弹量、伤害、射速 |
| 旋转利刃 | 环绕自身的刀刃，持续切割 | 刀刃数量 |
| 连锁闪电 | 弹跳打击多个敌人，伤害递减 | 弹跳次数 |
| 剧毒地雷 | 移动时释放毒圈，持续伤害 | 释放频率 |

### 成长技能

| 技能 | 效果 | 叠加 |
|------|------|------|
| 火力增强 | 子弹伤害 +1 | 线性 |
| 急速射击 | 攻击间隔 -15% | 乘法 |
| 凌波微步 | 移动速度 +15% | 乘法 |
| 增加弹量 | 每次射击 +1 发 | 线性 |
| 贪婪之魂 | 拾取范围 +50%，受伤 +10% | 乘法 |
| 冰霜光环 | 击中减速 20% | 一次 |
| 致命节奏 | 暴击率 +10%（2 倍 + 击退） | 线性 |
| 复苏之风 | 每 50 击杀回复 1 HP | 一次 |

### 敌人种类

| 敌人 | 特点 | 解锁时间 |
|------|------|----------|
| 基础怪 | 向你走来 | 0 秒 |
| 冲锋者 | 每隔几秒向你冲刺 | 25 秒 |
| 远程怪 | 保持距离向你射击 | 50 秒 |
| 自爆虫 | 高速冲撞，死亡范围爆炸 | 75 秒 |
| 精英怪 | 更大更硬，金色头冠 | 90 秒 |

### 动态难度
每 25 秒难度提升一级：敌人血量增加，生成速度加快，间隔缩短。

## 自定义素材

### 替换图像
将 `.png` 文件放入 `assets/sprites/`（删除还原默认）：

| 文件名 | 尺寸 | 格式 |
|--------|------|------|
| `player.png` | 96×32 (3帧×32) | PNG，横向 3 帧精灵表 |
| `enemy.png` | 84×28 | 同上 |
| `elite.png` | 120×40 | 同上 |
| `charger.png` | 84×28 | 同上 |
| `ranger.png` | 84×28 | 同上 |
| `exploder.png` | 84×28 | 同上 |

> 精灵表：3 张等宽帧横向排列，程序自动切割并缩放到目标尺寸。

### 替换音效
将 `.wav` 文件放入 `assets/sounds/`（删除还原默认）：

| 文件名 | 说明 |
|--------|------|
| `shoot.wav` | 射击音（~40ms） |
| `death.wav` | 死亡音（~120ms） |

> 无需改代码——`asset_loader.py` 自动检测文件存在性。

## 打包为 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "VampireSurvivors-like" --add-data "assets;assets" --hidden-import=numpy main.py
```

输出：`dist/VampireSurvivors-like.exe`（约 240MB，包含 Python 运行时）。

瘦身建议：在干净的 venv 环境下打包可减至 ~40MB：
```bash
python -m venv venv
venv\Scripts\activate
pip install pygame numpy pyinstaller
pyinstaller --onefile --windowed --name "VampireSurvivors-like" --add-data "assets;assets" main.py
```

## 项目结构

```
souls/
├── main.py              # 入口 + 主循环 + UI
├── settings.py          # 全部常量配置
├── player.py            # 玩家类
├── enemy.py             # 敌人类（HP / 动画 / DoT / 减速）
├── enemy_types.py       # Charger / Ranger / Exploder
├── enemy_bullet.py      # 敌人子弹（Ranger）
├── bullet.py            # 玩家子弹
├── xp_orb.py            # 经验球
├── particle.py          # 死亡粒子
├── damage_number.py     # 浮动伤害数字
├── explosion.py         # AoE 爆炸效果
├── camera.py            # 摄像机 + 震屏
├── orbital_blade.py     # 旋转利刃武器
├── chain_lightning.py   # 连环闪电武器
├── acid_trap.py         # 剧毒地雷武器
├── skills.py            # 11 种升级技能池
├── audio_manager.py     # 音频合成 + 播放
├── animation.py         # 帧动画类
├── asset_loader.py      # 素材加载 + 程序化生成降级
├── save_data.py         # 最高分 JSON 持久化
├── requirements.txt     # Python 依赖
├── assets/
│   ├── sprites/         # 替换 .png 素材（可选）
│   └── sounds/          # 替换 .wav 素材（可选）
└── souls_save.json      # 运行时自动生成
```

## 许可

MIT — 自由使用、修改、分发。
