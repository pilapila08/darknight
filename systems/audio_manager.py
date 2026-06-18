"""
AudioManager — synthesizes and plays all game audio.
No external asset files needed; everything is generated with the standard library.
"""
from array import array
import math
import random
import pygame


SAMPLE_RATE = 22050


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


def _generate_shoot():
    dur = 0.04
    count = int(SAMPLE_RATE * dur)
    noise_count = int(SAMPLE_RATE * 0.005)
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        env = _envelope_at(i, count, attack=0.002, release=0.02)
        value = math.sin(2 * math.pi * 800 * t) * env
        value += math.sin(2 * math.pi * 1200 * t) * env * 0.3
        if i < noise_count:
            value += random.uniform(-1, 1) * 0.2 * (1 - i / noise_count)
        samples.append(value * 0.7)
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
    """8-second ambient drone loop."""
    duration = 8.0
    count = int(SAMPLE_RATE * duration)
    fade_count = int(SAMPLE_RATE * 0.5)
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        lfo = math.sin(2 * math.pi * 0.25 * t) * 0.3 + 0.7
        value = math.sin(2 * math.pi * 55 * t) * lfo * 0.25
        value += math.sin(2 * math.pi * 27.5 * t) * 0.15
        value += math.sin(2 * math.pi * 110 * t) * 0.1
        value += math.sin(2 * math.pi * 165 * t) * 0.08
        sweep = math.sin(2 * math.pi * 0.15 * t) * 0.5 + 0.5
        value += math.sin(2 * math.pi * 220 * t) * sweep * 0.06
        if i < fade_count:
            value *= i / fade_count
        elif i >= count - fade_count:
            value *= (count - i) / fade_count
        samples.append(value * 0.5)
    return _make_sound(samples)


class AudioManager:
    def __init__(self):
        # SFX
        self._shoot = _generate_shoot()
        self._death_variants = _generate_death_variants(5)
        self._level_up = _generate_level_up()

        # Music
        self._music_loop = _generate_music_loop()
        self._music_channel = None
        self._music_playing = False

        # Volume
        self._sfx_volume = 0.6
        self._music_volume = 0.4

    # --- SFX ---

    def play_shoot(self):
        self._shoot.set_volume(self._sfx_volume)
        self._shoot.play()

    def play_enemy_death(self):
        s = random.choice(self._death_variants)
        # Add subtle pitch variation via playback rate (not directly supported,
        # so we rely on the pre-generated variants)
        s.set_volume(self._sfx_volume * random.uniform(0.85, 1.0))
        s.play()

    def play_level_up(self):
        self._level_up.set_volume(self._sfx_volume)
        self._level_up.play()

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
