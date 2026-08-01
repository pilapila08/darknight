"""
AudioManager — synthesizes and plays all game audio.
默认用标准库合成所有音效；若 assets/sounds/ 下存在同名 wav 文件则优先加载
（shoot.wav / enemy_death.wav / level_up.wav / hit.wav / explosion.wav /
 pickup.wav / hurt.wav / boss_warning.wav / boss_death.wav / ui_click.wav / music.wav）。
"""
from array import array
import math
import os
import random
import sys
import pygame


SAMPLE_RATE = 22050

# 关键修复（P0）：让 pygame.mixer 的采样率与合成采样率一致。
# mixer 默认 44100Hz，而合成缓冲是 22050Hz；若不一致，Sound(buffer=...) 会被按
# 44100Hz 播放 → 全部程序合成音效/BGM 2 倍速（时长减半、高八度）。
# pre_init 确保随后 pygame.init()/mixer.init() 使用正确采样率（覆盖 main.py 入口）；
# AudioManager.__init__ 内另有兜底对齐（覆盖 _smoke_test.py 等先 init 的入口）。
pygame.mixer.pre_init(SAMPLE_RATE, -16, 2)


def _resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


SOUNDS_DIR = _resource_path(os.path.join("assets", "sounds"))


def _clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))


def _make_sound(samples):
    """Convert float samples (-1..1) to a stereo 16-bit pygame Sound."""
    pcm = array("h")
    for value in samples:
        sample = int(_clamp(value) * 32767)
        pcm.append(sample)
        pcm.append(sample)
    return pygame.mixer.Sound(buffer=pcm)


def _load_external(name):
    """尝试加载外部音效文件，不存在返回 None。"""
    path = os.path.join(SOUNDS_DIR, name + ".wav")
    if os.path.isfile(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None
    path = os.path.join(SOUNDS_DIR, name + ".ogg")
    if os.path.isfile(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None
    return None


def _envelope_at(index, count, attack=0.005, release=None):
    """Linear attack-release envelope value for one sample."""
    attack_n = int(SAMPLE_RATE * attack)
    if release is None:
        release = count / SAMPLE_RATE * 0.3
    release_n = int(SAMPLE_RATE * release)
    amp = 1.0
    if attack_n > 0 and index < attack_n:
        amp = index / attack_n
    if release_n > 0 and index >= count - release_n:
        amp = min(amp, max(0.0, (count - index) / release_n))
    return amp


def _generate_shoot(pitch=1.0):
    """射击音（QOL 升级）：噪声扫频 + 快速衰减包络，质感更接近"枪声"。

    - 主体：白噪声经一阶低通，截止从亮快速扫向闷（模拟枪膛气压瞬态→尾音）
    - 起始：低频瞬态"噗"（150Hz 快速衰减，给击发以重量）
    - 残余：微量扫频正弦（900→120Hz 下滑），保留"枪膛感"
    """
    dur = 0.07
    count = int(SAMPLE_RATE * dur)
    samples = []
    lp = 0.0
    for i in range(count):
        t = i / SAMPLE_RATE
        # 快速指数衰减（主体 ~35ms 内衰减殆尽）
        decay = math.exp(-t * 42)
        # 一阶低通：起始明亮（alpha 高），快速变闷
        cutoff_alpha = 0.22 + 0.62 * math.exp(-t * 95)
        noise = random.uniform(-1, 1)
        lp += cutoff_alpha * (noise - lp)
        value = lp * decay
        # 起始低频瞬态（击发"噗"）
        if t < 0.014:
            thump = math.sin(2 * math.pi * 150 * pitch * t) * (1 - t / 0.014)
            value += thump * 0.6
        # 扫频正弦残余（高→低，枪膛感）
        sweep_freq = 900 * pitch * math.exp(-t * 40) + 120
        value += math.sin(2 * math.pi * sweep_freq * t) * decay * 0.16
        samples.append(value * 0.8)
    return _make_sound(samples)


def _generate_hit(pitch=1.0):
    """命中音（QOL 升级）：增强低频分量，更"肉"更实，与 shoot 区分。

    - 中频噼啪：420Hz 快速下滑正弦（原主体，保留）
    - 低频瞬态：130Hz 快速衰减（受击"肉"感，新增）
    - 噪声：短促爆裂
    """
    dur = 0.06
    count = int(SAMPLE_RATE * dur)
    samples = []
    freq = 420 * pitch
    for i in range(count):
        t = i / SAMPLE_RATE
        env = _envelope_at(i, count, attack=0.001, release=0.05)
        value = math.sin(2 * math.pi * freq * t * (1 - t * 4)) * env * 0.4
        # 低频瞬态（受击"肉"感）
        value += math.sin(2 * math.pi * 130 * pitch * t) * math.exp(-t * 38) * 0.55
        value += random.uniform(-1, 1) * env * 0.3
        samples.append(value * 0.6)
    return _make_sound(samples)


def _generate_death_variants(count=5):
    variants = []
    for _ in range(count):
        freq = random.uniform(130, 180)
        dur = 0.12
        sample_count = int(SAMPLE_RATE * dur)
        samples = []
        for i in range(sample_count):
            t = i / SAMPLE_RATE
            tone_env = _envelope_at(i, sample_count, attack=0.003, release=0.1)
            noise_env = _envelope_at(i, sample_count, attack=0.003, release=0.08)
            value = math.sin(2 * math.pi * freq * t) * tone_env * 0.7
            value += random.uniform(-1, 1) * noise_env * 0.6
            value += math.sin(2 * math.pi * freq * 0.5 * t) * _envelope_at(
                i, sample_count, attack=0.002, release=0.06) * 0.4
            samples.append(value * 0.6)
        variants.append(_make_sound(samples))
    return variants


def _generate_explosion():
    """爆炸（QOL 升级）：增强低频分量。

    - 次低频 sub 30Hz（新增，加重"震感"）
    - 低频轰鸣 55+38Hz（保留）
    - 噪声经一阶低通 → 更"闷"更重的隆隆声
    """
    dur = 0.5
    count = int(SAMPLE_RATE * dur)
    samples = []
    lp = 0.0
    for i in range(count):
        t = i / SAMPLE_RATE
        decay = math.exp(-t * 7)
        value = math.sin(2 * math.pi * 55 * t) * decay * 0.6
        value += math.sin(2 * math.pi * 38 * t) * decay * 0.45
        value += math.sin(2 * math.pi * 30 * t) * decay * 0.4  # 新增 sub
        # 低通噪声隆隆声
        noise = random.uniform(-1, 1)
        lp += 0.18 * (noise - lp)
        value += lp * decay * 0.5
        samples.append(value * 0.6)
    return _make_sound(samples)


def _generate_pickup():
    """拾取（QOL 升级）：两音上行 + 谐波层 + 起音噪声颗粒。

    - 基频 660→990 两音（保留），谐波层 2/3 次泛音加厚（原仅 0.2×2nd）
    - 起音 3ms 噪声颗粒 → 更"颗粒感"，与 level_up 的"宏亮琶音"区分
    """
    notes = [660, 990]
    note_dur = 0.055
    samples = []
    note_count = int(SAMPLE_RATE * note_dur)
    grain_n = int(SAMPLE_RATE * 0.003)
    for freq in notes:
        for i in range(note_count):
            t = i / SAMPLE_RATE
            env = _envelope_at(i, note_count, attack=0.003, release=0.035)
            value = math.sin(2 * math.pi * freq * t) * env
            value += math.sin(2 * math.pi * freq * 2 * t) * env * 0.28
            value += math.sin(2 * math.pi * freq * 3 * t) * env * 0.12
            if i < grain_n:
                value += random.uniform(-1, 1) * 0.25 * (1 - i / grain_n)
            samples.append(value * 0.5)
    return _make_sound(samples)


def _generate_hurt():
    """玩家受击：低沉闷响 + 快速下滑音。"""
    dur = 0.18
    count = int(SAMPLE_RATE * dur)
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        decay = math.exp(-t * 14)
        freq = 220 * (1 - t * 2.5)
        value = math.sin(2 * math.pi * max(40, freq) * t) * decay * 0.9
        value += random.uniform(-1, 1) * decay * 0.4
        samples.append(value * 0.65)
    return _make_sound(samples)


def _generate_boss_warning():
    """Boss警报：两声低沉的警笛。"""
    samples = []
    for _ in range(2):
        dur = 0.4
        count = int(SAMPLE_RATE * dur)
        for i in range(count):
            t = i / SAMPLE_RATE
            env = _envelope_at(i, count, attack=0.02, release=0.15)
            sweep = 160 + 90 * math.sin(math.pi * t / dur)
            value = math.sin(2 * math.pi * sweep * t) * env * 0.7
            value += math.sin(2 * math.pi * sweep * 0.5 * t) * env * 0.45
            samples.append(value * 0.6)
        # 间隔
        samples.extend([0.0] * int(SAMPLE_RATE * 0.12))
    return _make_sound(samples)


def _generate_boss_death():
    """Boss死亡：长爆炸 + 下行音阶。"""
    dur = 0.9
    count = int(SAMPLE_RATE * dur)
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        decay = math.exp(-t * 3.5)
        freq = 200 * (1 - t * 0.7)
        value = math.sin(2 * math.pi * max(30, freq) * t) * decay * 0.7
        value += random.uniform(-1, 1) * decay * 0.55
        value += math.sin(2 * math.pi * 48 * t) * decay * 0.5
        samples.append(value * 0.7)
    return _make_sound(samples)


def _generate_ui_click():
    """UI确认（QOL 升级）：短促高音 + 谐波层 + 起音咔哒。

    - 基频 880Hz + 2/3/4 次泛音加厚（原仅 1.5 倍泛音）
    - 起音 2ms 噪声"咔哒" → 干净但更有实体感
    """
    dur = 0.07
    count = int(SAMPLE_RATE * dur)
    samples = []
    tick_n = int(SAMPLE_RATE * 0.002)
    for i in range(count):
        t = i / SAMPLE_RATE
        env = _envelope_at(i, count, attack=0.002, release=0.05)
        value = math.sin(2 * math.pi * 880 * t) * env
        value += math.sin(2 * math.pi * 1320 * t) * env * 0.3
        value += math.sin(2 * math.pi * 1760 * t) * env * 0.12
        value += math.sin(2 * math.pi * 2640 * t) * env * 0.06
        if i < tick_n:
            value += random.uniform(-1, 1) * 0.2 * (1 - i / tick_n)
        samples.append(value * 0.5)
    return _make_sound(samples)


def _generate_level_up():
    """Rising arpeggio chime: C5-E5-G5-C6"""
    notes = [523, 659, 784, 1047]
    note_dur = 0.08
    samples = []
    note_count = int(SAMPLE_RATE * (note_dur + 0.02))
    for freq in notes:
        for i in range(note_count):
            t = i / SAMPLE_RATE
            env = _envelope_at(i, note_count, attack=0.005, release=0.06)
            value = math.sin(2 * math.pi * freq * t) * env
            value += math.sin(2 * math.pi * freq * 2 * t) * env * 0.15
            value += math.sin(2 * math.pi * freq * 3 * t) * env * 0.05
            samples.append(value * 0.7)
    return _make_sound(samples)


def _generate_music_loop():
    """16秒分层氛围循环：低音脉冲 + 和声垫 + 稀疏琶音旋律。"""
    duration = 16.0
    count = int(SAMPLE_RATE * duration)
    fade_count = int(SAMPLE_RATE * 0.5)

    # A小调进行：Am - F - C - G（每小节4秒）
    chords = [
        (110.0, 130.81, 164.81),   # A2 C3 E3
        (87.31, 110.0, 130.81),    # F2 A2 C3
        (65.41, 82.41, 98.0),      # C2 E2 G2
        (98.0, 123.47, 146.83),    # G2 B2 D3
    ]
    # 琶音音符（每0.5秒一个，来自当前和弦的高八度）
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        bar = int(t / 4.0) % 4
        root, third, fifth = chords[bar]

        # 低音：脉冲式（每秒两次）
        beat = (t * 2.0) % 1.0
        bass_env = math.exp(-beat * 5) * 0.5 + 0.15
        value = math.sin(2 * math.pi * root * t) * bass_env * 0.30

        # 和声垫：缓慢起伏
        lfo = math.sin(2 * math.pi * 0.12 * t) * 0.25 + 0.75
        value += math.sin(2 * math.pi * third * 2 * t) * lfo * 0.075
        value += math.sin(2 * math.pi * fifth * 2 * t) * lfo * 0.06

        # 琶音：每0.5秒触发，随小节循环 根-五-三-五
        step = int(t / 0.5)
        seq = (root * 4, fifth * 4, third * 4, fifth * 4)
        note = seq[step % 4]
        note_t = (t % 0.5)
        pluck = math.exp(-note_t * 6)
        value += math.sin(2 * math.pi * note * t) * pluck * 0.085
        value += math.sin(2 * math.pi * note * 2 * t) * pluck * 0.03

        if i < fade_count:
            value *= i / fade_count
        elif i >= count - fade_count:
            value *= (count - i) / fade_count
        samples.append(value * 0.55)
    return _make_sound(samples)


class AudioManager:
    def __init__(self):
        # 兜底对齐 mixer 采样率（见模块顶部 pre_init 注释）。
        # 若 mixer 已被其它入口以默认 44100Hz 初始化，此处强制重启到 SAMPLE_RATE，
        # 必须在任何 Sound 创建之前执行。
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2)
        current = pygame.mixer.get_init()
        if not current or current[0] != SAMPLE_RATE:
            try:
                pygame.mixer.quit()
                pygame.mixer.init(SAMPLE_RATE, -16, 2)
            except pygame.error:
                # 音频设备不可用时保持原行为（首个 Sound 创建会正常报错）
                pass

        # SFX（外部文件优先，缺失时合成）
        self._shoot = _load_external("shoot") or _generate_shoot()
        self._shoot_variants = [self._shoot,
                                _generate_shoot(0.95), _generate_shoot(1.06)]
        self._death_variants = _load_external("enemy_death")
        if self._death_variants:
            self._death_variants = [self._death_variants]
        else:
            self._death_variants = _generate_death_variants(5)
        self._level_up = _load_external("level_up") or _generate_level_up()
        self._hit_variants = [_load_external("hit") or _generate_hit(p)
                              for p in (0.9, 1.0, 1.12)]
        self._explosion = _load_external("explosion") or _generate_explosion()
        self._pickup = _load_external("pickup") or _generate_pickup()
        self._hurt = _load_external("hurt") or _generate_hurt()
        self._boss_warning = _load_external("boss_warning") or _generate_boss_warning()
        self._boss_death = _load_external("boss_death") or _generate_boss_death()
        self._ui_click = _load_external("ui_click") or _generate_ui_click()

        # Music
        self._music_loop = _load_external("music") or _generate_music_loop()
        self._music_channel = None
        self._music_playing = False

        # Volume
        self._sfx_volume = 0.6
        self._music_volume = 0.4

        # 侧链闪避（大音效时压低BGM）
        self._duck_amount = 0.0
        self._duck_timer = 0.0

        # 高频音效限流
        self._hit_cooldown = 0.0

    # --- SFX ---

    def play_shoot(self):
        s = random.choice(self._shoot_variants)
        s.set_volume(self._sfx_volume * 0.85)
        s.play()

    def play_hit(self):
        if self._hit_cooldown > 0:
            return
        self._hit_cooldown = 0.05
        s = random.choice(self._hit_variants)
        s.set_volume(self._sfx_volume * random.uniform(0.4, 0.55))
        s.play()

    def play_enemy_death(self):
        s = random.choice(self._death_variants)
        s.set_volume(self._sfx_volume * random.uniform(0.85, 1.0))
        s.play()

    def play_level_up(self):
        self._level_up.set_volume(self._sfx_volume)
        self._level_up.play()
        self.duck(0.5, 0.6)

    def play_explosion(self):
        self._explosion.set_volume(self._sfx_volume * 0.9)
        self._explosion.play()
        self.duck(0.35, 0.4)

    def play_pickup(self):
        self._pickup.set_volume(self._sfx_volume * 0.7)
        self._pickup.play()

    def play_hurt(self):
        self._hurt.set_volume(self._sfx_volume)
        self._hurt.play()
        self.duck(0.4, 0.35)

    def play_boss_warning(self):
        self._boss_warning.set_volume(self._sfx_volume)
        self._boss_warning.play()
        self.duck(0.6, 1.2)

    def play_boss_death(self):
        self._boss_death.set_volume(self._sfx_volume)
        self._boss_death.play()
        self.duck(0.7, 1.0)

    def play_ui_click(self):
        self._ui_click.set_volume(self._sfx_volume * 0.8)
        self._ui_click.play()

    # --- 闪避与更新 ---

    def duck(self, amount, duration):
        """短暂压低BGM音量，突出关键音效。"""
        if amount > self._duck_amount:
            self._duck_amount = amount
        self._duck_timer = max(self._duck_timer, duration)

    def update(self, dt):
        if self._hit_cooldown > 0:
            self._hit_cooldown -= dt
        if self._duck_timer > 0:
            self._duck_timer -= dt
            if self._duck_timer <= 0:
                self._duck_amount = 0.0
        else:
            # 平滑恢复
            self._duck_amount = max(0.0, self._duck_amount - 1.5 * dt)
        if self._music_playing:
            vol = self._music_volume * (1.0 - self._duck_amount)
            self._music_loop.set_volume(max(0.0, vol))

    # --- Music ---

    def start_music(self):
        if not self._music_playing:
            self._music_loop.set_volume(self._music_volume)
            self._music_channel = self._music_loop.play(-1)  # loop forever
            self._music_playing = True

    def stop_music(self):
        if self._music_playing and self._music_channel:
            self._music_channel.stop()
            self._music_playing = False

    # --- Volume ---

    def set_music_volume(self, vol):
        """vol: 0.0 - 1.0"""
        self._music_volume = max(0.0, min(1.0, vol))
        self._music_loop.set_volume(self._music_volume)

    def set_sfx_volume(self, vol):
        """vol: 0.0 - 1.0"""
        self._sfx_volume = max(0.0, min(1.0, vol))

    def get_music_volume(self):
        return self._music_volume

    def get_sfx_volume(self):
        return self._sfx_volume
