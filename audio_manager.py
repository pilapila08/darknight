"""
AudioManager — synthesizes and plays all game audio.
No external asset files needed; everything is generated via numpy.
"""
import math
import random
import numpy as np
import pygame


SAMPLE_RATE = 22050


def _make_sound(samples):
    """Convert a float numpy array (-1..1) to a pygame Sound."""
    arr = (samples * 32767).astype(np.int16)
    if arr.ndim == 1:
        arr = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(arr)


def _sine(freq, duration, amp=1.0):
    """Generate a sine wave at given frequency and duration."""
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    return (np.sin(2 * math.pi * freq * t) * amp).astype(np.float32)


def _envelope(duration, attack=0.005, release=None):
    """Generate a linear attack-release envelope."""
    n = int(SAMPLE_RATE * duration)
    env = np.ones(n, dtype=np.float32)
    attack_n = int(SAMPLE_RATE * attack)
    if attack_n > 0 and attack_n < n:
        env[:attack_n] = np.linspace(0, 1, attack_n, dtype=np.float32)
    if release is None:
        release = duration * 0.3
    release_n = int(SAMPLE_RATE * release)
    if release_n > 0 and release_n < n:
        env[-release_n:] = np.linspace(1, 0, release_n, dtype=np.float32)
    return env


def _generate_shoot():
    dur = 0.04
    s = _sine(800, dur) * _envelope(dur, attack=0.002, release=0.02)
    s += _sine(1200, dur) * _envelope(dur, attack=0.002, release=0.015) * 0.3
    # Add noise burst at start for "click"
    noise = np.random.uniform(-1, 1, int(SAMPLE_RATE * 0.005)).astype(np.float32) * 0.2
    s[:len(noise)] += noise * np.linspace(1, 0, len(noise), dtype=np.float32)
    return _make_sound(np.clip(s, -1, 1) * 0.7)


def _generate_death_variants(count=5):
    variants = []
    for _ in range(count):
        freq = random.uniform(130, 180)
        dur = 0.12
        noise = np.random.uniform(-1, 1, int(SAMPLE_RATE * dur)).astype(np.float32)
        noise *= _envelope(dur, attack=0.003, release=0.08) * 0.6
        tone = _sine(freq, dur) * _envelope(dur, attack=0.003, release=0.1) * 0.7
        s = tone + noise
        # Sub-bass thump
        s += _sine(freq * 0.5, dur) * _envelope(dur, attack=0.002, release=0.06) * 0.4
        variants.append(_make_sound(np.clip(s, -1, 1) * 0.6))
    return variants


def _generate_level_up():
    """Rising arpeggio chime: C5-E5-G5-C6"""
    notes = [523, 659, 784, 1047]
    note_dur = 0.08
    segments = []
    for i, freq in enumerate(notes):
        seg = _sine(freq, note_dur + 0.02)
        env = _envelope(note_dur + 0.02, attack=0.005, release=0.06)
        seg *= env
        # Add harmonic sparkle
        seg += _sine(freq * 2, note_dur + 0.02) * env * 0.15
        seg += _sine(freq * 3, note_dur + 0.02) * env * 0.05
        segments.append(seg)
    s = np.concatenate(segments)
    return _make_sound(np.clip(s, -1, 1) * 0.7)


def _generate_music_loop():
    """8-second ambient drone loop."""
    duration = 8.0
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    s = np.zeros(n, dtype=np.float32)

    # Bass drone: A1 (55 Hz) with slow pulse
    bass = np.sin(2 * math.pi * 55 * t)
    lfo = np.sin(2 * math.pi * 0.25 * t) * 0.3 + 0.7  # slow volume pulse
    s += bass * lfo * 0.25

    # Sub-bass: A0 (27.5 Hz)
    s += np.sin(2 * math.pi * 27.5 * t) * 0.15

    # Gentle pad: A2 (110 Hz) + E3 (165 Hz)
    pad = np.sin(2 * math.pi * 110 * t) * 0.1
    pad += np.sin(2 * math.pi * 165 * t) * 0.08
    s += pad

    # Slow filter sweep effect (simple tremolo on higher harmonic)
    sweep = np.sin(2 * math.pi * 0.15 * t) * 0.5 + 0.5
    s += np.sin(2 * math.pi * 220 * t) * sweep * 0.06

    # Gentle fade in/out at loop boundary (crossfade 0.5s)
    fade_n = int(SAMPLE_RATE * 0.5)
    fade_in = np.linspace(0, 1, fade_n, dtype=np.float32)
    fade_out = np.linspace(1, 0, fade_n, dtype=np.float32)
    s[:fade_n] *= fade_in
    s[-fade_n:] *= fade_out

    s = np.clip(s, -1, 1) * 0.5
    return _make_sound(s)


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
            self._music_channel = self._music_loop.play(-1)  # loop forever
            self._music_loop.set_volume(self._music_volume)
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
