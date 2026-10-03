"""Saxophone tone synthesis"""

import numpy as np
import pygame

SAMPLE_RATE = 44100


class SaxSynth:
    """Generates (and caches) a pygame Sound for a concert-pitch MIDI note and duration"""

    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.sound_cache = {}

    def note_sound(self, note_number, duration):
        """Synthesize a sax-like tone (concert pitch) for the given duration in seconds"""
        key = (note_number, round(duration, 2))
        if key in self.sound_cache:
            return self.sound_cache[key]

        freq = 440.0 * 2 ** ((note_number - 69) / 12)
        t = np.arange(int(self.sample_rate * duration)) / self.sample_rate

        # Gentle vibrato that fades in after the attack
        vibrato = 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.3, 0, 1)
        phase = 2 * np.pi * freq * (t + np.cumsum(vibrato) / self.sample_rate)

        # Reed-like harmonic mix
        harmonics = [1.0, 0.6, 0.45, 0.3, 0.2, 0.12, 0.08]
        wave = sum(amp * np.sin((i + 1) * phase) for i, amp in enumerate(harmonics))
        wave /= sum(harmonics)

        # Attack / release envelope to avoid clicks
        attack = np.clip(t / 0.03, 0, 1)
        release = np.clip((duration - t) / 0.05, 0, 1)
        wave *= attack * release

        samples = (wave * 0.5 * 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(samples)
        self.sound_cache[key] = sound
        return sound


class BackingSynth:
    """Distinct synthesized piano, guitar, bass, strings and percussion voices."""

    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.sound_cache = {}

    def note_sound(self, note, duration):
        drum = note['channel'] == 9
        duration = min(duration, 0.5) if drum else duration
        key = (note['note'], drum, note['program'], round(duration, 2), note['velocity'])
        if key in self.sound_cache:
            return self.sound_cache[key]
        t = np.arange(max(1, int(self.sample_rate * duration))) / self.sample_rate
        freq = 440 * 2 ** ((note['note'] - 69) / 12)
        if drum:
            noise = np.random.default_rng(note['note']).uniform(-1, 1, len(t))
            if note['note'] in (35, 36):
                wave = np.sin(2 * np.pi * (65 * t + 6 * (1 - np.exp(-t * 30)))) * np.exp(-t * 18)
            else:
                decay = 35 if note['note'] in (42, 44, 46) else 16
                wave = noise * np.exp(-t * decay)
        else:
            phase = 2 * np.pi * freq * t
            program = note['program']
            attack = np.clip(t / 0.005, 0, 1)
            if 24 <= program <= 31:  # Plucked strings: bright attack, quickly fading overtones
                wave = sum(np.sin(h * phase) * np.exp(-t * (2.0 + h * 0.9)) / h
                           for h in range(1, 9)) / 1.8
            elif 32 <= program <= 39:
                wave = (np.sin(phase) + 0.2 * np.sin(2 * phase)) / 1.2
                wave *= np.exp(-t * 1.5)
            elif 40 <= program <= 55:  # Sustained bowed/ensemble voice
                wave = sum(np.sin(h * phase) / h for h in range(1, 7)) / 1.8
                attack = np.clip(t / 0.12, 0, 1)
            else:  # Piano: decaying body with a bell-like attack
                wave = (np.sin(phase) * np.exp(-t * 1.5)
                        + 0.45 * np.sin(2 * phase) * np.exp(-t * 3)
                        + 0.2 * np.sin(3.01 * phase) * np.exp(-t * 5)) / 1.65
            wave *= attack
        wave *= np.clip((duration - t) / 0.03, 0, 1)
        sound = pygame.sndarray.make_sound((wave * 0.25 * note['velocity'] / 127 * 32767).astype(np.int16))
        if len(self.sound_cache) >= 256:
            self.sound_cache.clear()
        self.sound_cache[key] = sound
        return sound
