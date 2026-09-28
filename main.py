import sys
from bisect import bisect_left, bisect_right

import pygame
import mido
import numpy as np
from moviepy import ImageSequenceClip

import fingerings as fg

# Alto sax is an Eb instrument: written pitch = concert pitch + 9 semitones.
# MIDI files hold concert pitch; everything shown to the player is written pitch.
ALTO_TRANSPOSE = 9

# Pitch class -> (letter index C=0..B=6, accidental), using common sax spellings
SPELLING = [(0, ''), (0, '#'), (1, ''), (2, 'b'), (2, ''), (3, ''),
            (3, '#'), (4, ''), (4, '#'), (5, ''), (6, 'b'), (6, '')]
LETTERS = 'CDEFGAB'
ACCIDENTAL_GLYPH = {'': '', '#': '♯', 'b': '♭'}


def spell(midi_note):
    """Return (letter index, accidental, octave) for a MIDI note"""
    letter, accidental = SPELLING[midi_note % 12]
    return letter, accidental, midi_note // 12 - 1


def staff_step(midi_note):
    """Diatonic position on the staff (C4 = 28, E4 = 30 = bottom line of treble staff)"""
    letter, _, octave = spell(midi_note)
    return octave * 7 + letter


def note_name(midi_note):
    letter, accidental, octave = spell(midi_note)
    return f"{LETTERS[letter]}{ACCIDENTAL_GLYPH[accidental]}{octave}"


class SaxophoneVisualizer:
    SAMPLE_RATE = 44100
    LEAD_IN_BEATS = 4
    SEEK_BEATS = 4
    DEFAULT_PIXELS_PER_BEAT = 250
    ZOOM_STEP = 1.15
    ZOOM_RANGE = (80, 700)  # pixels per beat
    MIN_STAFF_HEIGHT = 190  # staff area grows to fit the song's highest/lowest notes
    FOOTER_HEIGHT = 58
    HEADER_WIDTH = 320
    ICON_COLUMN_INSET = 100  # main key column sits this far left of the lanes
    SPEEDS = [round(0.25 + 0.05 * i, 2) for i in range(36)]  # 25% .. 200%
    BAR_GAP = 14  # pixels of empty space after each note bar
    PLAYLINE_FRACTION = 0.3  # playline position across the scrolling area; left of it is history

    # Staff geometry (within the staff area)
    LINE_SPACING = 18
    BOTTOM_LINE_STEP = 30  # E4 = 4 * 7 + 2
    TOP_LINE_STEP = 38  # F5

    BG_TOP = (14, 24, 48)
    BG_BOTTOM = (22, 50, 94)
    TEXT = (225, 232, 245)
    TEXT_DIM = (120, 140, 175)
    HIGHLIGHT = (255, 214, 90)
    OPEN_GREY = (130, 140, 160)  # OPEN marker for notes played with no keys

    def __init__(self, midi_file, window_size=(1600, 900)):
        self.midi_file = midi_file
        self.frames = []
        self.notes, self.bpm, self.beats_per_bar = self.process_midi_file()
        self.starts = [n['start'] for n in self.notes]
        fg.assign_fingerings(self.notes)
        self.used_keys = {key for n in self.notes for key in n['keys']}
        self.show_all_keys = False
        self.max_duration = max((n['end'] - n['start'] for n in self.notes), default=0)
        self.song_end = max((n['end'] for n in self.notes), default=0)

        self.beat = -self.LEAD_IN_BEATS
        self.playing = True
        self.speed_index = self.SPEEDS.index(1.0)
        self.pixels_per_beat = self.DEFAULT_PIXELS_PER_BEAT
        self.popup = None  # (title, subtitle, shown_at_ms)

        pygame.mixer.pre_init(self.SAMPLE_RATE, -16, 1, 512)
        pygame.init()
        self.audio_enabled = pygame.mixer.get_init() is not None
        if self.audio_enabled:
            self.sax_channel = pygame.mixer.Channel(0)
        else:
            print("Audio unavailable; running without sound.")
        self.sound_cache = {}

        self.screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Saxophone Hero")
        pygame.key.set_repeat(300, 90)

        ui_fonts = 'dejavusans,notosans'
        self.font_tiny = self.load_font(ui_fonts, 13)
        self.font_small = self.load_font(ui_fonts, 16)
        self.font_label = self.load_font(ui_fonts, 19)
        self.font_label_bold = self.load_font(ui_fonts, 19, bold=True)
        self.font_big = self.load_font(ui_fonts, 60, bold=True)
        self.font_accidental = self.load_font(ui_fonts, 34)
        clef_path = pygame.font.match_font('notomusic')
        self.font_clef = pygame.font.Font(clef_path, int(self.LINE_SPACING * 5.4)) if clef_path else None
        self.text_cache = {}
        self.glow_cache = {}

        self.fit_staff_to_song()
        self.layout()

    @staticmethod
    def load_font(names, size, bold=False):
        return pygame.font.Font(pygame.font.match_font(names, bold=bold), size)

    def process_midi_file(self):
        """Read notes as {'note', 'start', 'end'} in beats, plus tempo and meter"""
        midi = mido.MidiFile(self.midi_file)
        tpb = midi.ticks_per_beat
        tempo = None
        beats_per_bar = 4
        notes = []

        for track in midi.tracks:
            tick = 0
            open_notes = {}
            for msg in track:
                tick += msg.time
                if msg.type == 'set_tempo' and tempo is None:
                    tempo = msg.tempo
                elif msg.type == 'time_signature':
                    beats_per_bar = msg.numerator
                elif msg.type == 'note_on' and msg.velocity > 0:
                    open_notes[msg.note] = tick
                elif msg.type in ('note_off', 'note_on') and msg.note in open_notes:
                    start = open_notes.pop(msg.note)
                    notes.append({'note': msg.note, 'start': start / tpb, 'end': tick / tpb})

        notes.sort(key=lambda n: n['start'])
        bpm = mido.tempo2bpm(tempo or 500000)
        print(f"Loaded {len(notes)} notes at {bpm:.0f} BPM")
        return notes, bpm, beats_per_bar

    # ---------- Layout & static background ----------

    def fit_staff_to_song(self):
        """Size the staff area to the song's pitch range so the big staff doesn't waste lane space"""
        steps = [staff_step(n['note'] + ALTO_TRANSPOSE) for n in self.notes]
        half = self.LINE_SPACING / 2
        top_step = max(steps + [self.TOP_LINE_STEP + 1])  # always room for the space above the staff
        low_step = min(steps + [self.BOTTOM_LINE_STEP - 1])  # ...and the space below it
        measure_numbers = 30
        self.bottom_line_y = int(measure_numbers + (top_step - self.BOTTOM_LINE_STEP + 1) * half)
        names_y = self.bottom_line_y + (self.BOTTOM_LINE_STEP - low_step + 1) * half + 8
        self.names_y = int(names_y)
        self.staff_height = max(int(names_y + self.font_label.get_height() + 10), self.MIN_STAFF_HEIGHT)

    def layout(self):
        """Compute lane positions and pre-render the static background"""
        w, h = self.screen.get_size()
        self.lane_left = self.HEADER_WIDTH
        self.playline_x = int(self.lane_left + (w - self.lane_left) * self.PLAYLINE_FRACTION)
        self.lanes_top = self.staff_height + 8
        self.lanes_bottom = h - self.FOOTER_HEIGHT - 8
        self.progress_rect = pygame.Rect(16, h - self.FOOTER_HEIGHT + 10, w - 32, 6)

        gap = 10
        # Only keys this song presses (plus the main six), unless K toggled "show all"
        lanes = [k for k in fg.KEYS
                 if self.show_all_keys or k[0] in self.used_keys or k[0] in fg.ALWAYS_SHOWN]
        weights = [2.2 if shape == 'main' else 1.0 for _, _, _, shape in lanes]
        n_gaps = sum(1 for a, b in zip(lanes, lanes[1:]) if a[2] != b[2])
        unit = (self.lanes_bottom - self.lanes_top - n_gaps * gap) / sum(weights)

        self.lanes = {}
        y = self.lanes_top
        prev_group = None
        for (key, label, group, shape), weight in zip(lanes, weights):
            if prev_group and group != prev_group:
                y += gap
            height = weight * unit
            self.lanes[key] = {
                'key': key, 'label': label, 'group': group, 'shape': shape,
                'y': y, 'h': height, 'cy': y + height / 2,
                'icon_x': self.lane_left - self.ICON_COLUMN_INSET + fg.ICON_OFFSET.get(key, 0),
                'color': fg.GROUP_COLORS[group],
            }
            y += height
            prev_group = group

        self.background = self.render_background()

    def render_background(self):
        w, h = self.screen.get_size()
        bg = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            color = [int(a + (b - a) * t) for a, b in zip(self.BG_TOP, self.BG_BOTTOM)]
            pygame.draw.line(bg, color, (0, y), (w, y))

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        # Darker header column and footer
        overlay.fill((0, 0, 0, 70), pygame.Rect(0, self.staff_height, self.lane_left, h))
        overlay.fill((0, 0, 0, 90), pygame.Rect(0, h - self.FOOTER_HEIGHT, w, self.FOOTER_HEIGHT))
        # Lane stripes
        for i, lane in enumerate(self.lanes.values()):
            rect = pygame.Rect(self.lane_left, lane['y'] + 1, w - self.lane_left, lane['h'] - 2)
            overlay.fill((255, 255, 255, 14 if i % 2 else 8), rect)
        bg.blit(overlay, (0, 0))

        # Slightly darker history region left of the playline
        history = pygame.Surface((self.playline_x - self.lane_left, self.lanes_bottom - self.lanes_top),
                                 pygame.SRCALPHA)
        history.fill((0, 0, 0, 45))
        bg.blit(history, (self.lane_left, self.lanes_top))

        # Outline key clusters (palm, table, side, right pinky) like a fingering chart
        for group in fg.CLUSTERS:
            members = [l for l in self.lanes.values() if l['group'] == group]
            if len(members) < 2:
                continue
            xs = [l['icon_x'] for l in members]
            box = pygame.Rect(min(xs) - 24, members[0]['y'] + 1, max(xs) - min(xs) + 48,
                              members[-1]['y'] + members[-1]['h'] - members[0]['y'] - 2)
            pygame.draw.rect(bg, (70, 90, 130), box, 1, border_radius=12)

        # Idle key icons (labels are drawn per frame so pressed ones can switch to bold)
        for lane in self.lanes.values():
            self.draw_key_icon(bg, lane, pressed=False)

        # Staff lines and clef
        staff_x0 = self.lane_left - 80
        for i in range(5):
            y = self.bottom_line_y - i * self.LINE_SPACING
            pygame.draw.line(bg, (150, 170, 205), (staff_x0, y), (w, y), 2)
        if self.font_clef:
            clef = self.font_clef.render('\U0001D11E', True, (200, 212, 235))
            bg.blit(clef, clef.get_rect(x=staff_x0 + 2,
                                        centery=self.bottom_line_y - 2 * self.LINE_SPACING + self.LINE_SPACING * 0.4))
        return bg

    def draw_key_icon(self, surface, lane, pressed, color=None):
        cx, cy = lane['icon_x'], lane['cy']
        color = (color or lane['color']) if pressed else (32, 44, 72)
        outline = (255, 255, 255) if pressed else (170, 185, 215)
        shape = lane['shape']
        h = lane['h']
        if shape in ('main', 'small'):
            r = int(min(h * 0.36, 22)) if shape == 'main' else int(min(h * 0.3, 8))
            pygame.draw.circle(surface, color, (cx, cy), r)
            pygame.draw.circle(surface, outline, (cx, cy), r, 2)
        elif shape == 'tri':
            # Octave key: triangle pointing up, like the thumb key on the chart
            s = min(h * 0.45, 12)
            points = [(cx - s * 0.2, cy - s), (cx + s * 0.8, cy + s), (cx - s * 0.9, cy + s * 0.6)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, outline, points, 2)
        else:
            if shape == 'oval':  # palm keys: tall ovals
                size = (13, min(h * 0.8, 24))
            elif shape == 'table':  # spatula keys
                size = (fg.TABLE_WIDTH[lane['key']], min(h * 0.7, 16))
            elif shape == 'side':  # side keys: tall narrow bars
                size = (11, min(h * 0.85, 24))
            elif shape == 'side_small':  # high F# and alternate F#: short side levers
                size = (9, min(h * 0.6, 14))
            else:  # right pinky: two halves of one round key
                size = (30, min(h * 0.75, 16))
            rect = pygame.Rect(0, 0, *size)
            rect.center = (cx, cy)
            if shape == 'pinky_top':
                radii = dict(border_top_left_radius=15, border_top_right_radius=15)
            elif shape == 'pinky_bottom':
                radii = dict(border_bottom_left_radius=15, border_bottom_right_radius=15)
            elif shape == 'table':
                radii = dict(border_radius=3)
            else:
                radii = dict(border_radius=int(min(size) / 2))
            pygame.draw.rect(surface, color, rect, **radii)
            pygame.draw.rect(surface, outline, rect, 2, **radii)

    # ---------- Helpers ----------

    def lane_font(self, lane):
        """Large label font, or the small one when the lane is too short (small windows)"""
        return self.font_label if lane['h'] >= self.font_label.get_height() * 0.9 else self.font_small

    def text(self, font, string, color):
        key = (id(font), string, color)
        if key not in self.text_cache:
            self.text_cache[key] = font.render(string, True, color)
        return self.text_cache[key]

    def glow(self, color, radius):
        key = (color, radius)
        if key not in self.glow_cache:
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -2):
                alpha = int(110 * (1 - r / radius) ** 1.6)
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
            self.glow_cache[key] = surf
        return self.glow_cache[key]

    @staticmethod
    def dim(color):
        """Fade an already-played bar toward the background"""
        return tuple(int(c * 0.4 + b * 0.6) for c, b in zip(color, (30, 50, 90)))

    def beat_to_x(self, beat):
        return self.playline_x + (beat - self.beat) * self.pixels_per_beat

    @property
    def speed(self):
        return self.SPEEDS[self.speed_index]

    def current_note(self):
        """Note sounding at the current beat, if any"""
        i = bisect_right(self.starts, self.beat) - 1
        if i >= 0 and self.notes[i]['start'] <= self.beat < self.notes[i]['end']:
            return self.notes[i]
        return None

    def visible_notes(self):
        w = self.screen.get_width()
        history_beats = (self.playline_x - self.lane_left) / self.pixels_per_beat
        ahead_beats = (w - self.playline_x) / self.pixels_per_beat
        lo = bisect_left(self.starts, self.beat - history_beats - self.max_duration - 1)
        hi = bisect_right(self.starts, self.beat + ahead_beats + 1)
        return self.notes[lo:hi]

    def format_time(self, beat):
        seconds = max(beat, 0) * 60 / self.bpm
        return f"{int(seconds // 60)}:{int(seconds % 60):02d}"

    # ---------- Audio ----------

    def get_note_sound(self, note_number, duration):
        """Synthesize a sax-like tone (concert pitch) for the given duration in seconds"""
        key = (note_number, round(duration, 2))
        if key in self.sound_cache:
            return self.sound_cache[key]

        freq = 440.0 * 2 ** ((note_number - 69) / 12)
        t = np.arange(int(self.SAMPLE_RATE * duration)) / self.SAMPLE_RATE

        # Gentle vibrato that fades in after the attack
        vibrato = 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.3, 0, 1)
        phase = 2 * np.pi * freq * (t + np.cumsum(vibrato) / self.SAMPLE_RATE)

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

    def play_from(self, note, beat):
        """Play the rest of a note starting at the given beat"""
        if not self.audio_enabled:
            return
        remaining_beats = note['end'] - beat
        if remaining_beats < 0.05:
            return
        duration = remaining_beats * 60 / self.bpm / self.speed
        self.sax_channel.play(self.get_note_sound(note['note'], duration))

    def update_audio(self, prev_beat):
        """Trigger the latest note that started since the previous frame"""
        i0 = bisect_right(self.starts, prev_beat)
        i1 = bisect_right(self.starts, self.beat)
        if i1 > i0:
            self.play_from(self.notes[i1 - 1], self.beat)

    def resync_audio(self):
        """After a seek/pause/speed change, restart whatever should be sounding"""
        if not self.audio_enabled:
            return
        self.sax_channel.stop()
        note = self.current_note()
        if self.playing and note:
            self.play_from(note, self.beat)

    # ---------- Controls ----------

    def seek(self, beat):
        self.beat = min(max(beat, -self.LEAD_IN_BEATS), self.song_end)
        self.resync_audio()

    def change_speed(self, step):
        self.speed_index = min(max(self.speed_index + step, 0), len(self.SPEEDS) - 1)
        self.show_popup(f"Speed {self.speed:.0%}", f"{self.bpm * self.speed:.0f} BPM")
        self.resync_audio()

    def zoom(self, steps):
        """Change bar length; positive steps zoom in (longer bars)"""
        self.set_zoom(self.pixels_per_beat * self.ZOOM_STEP ** steps)

    def set_zoom(self, pixels_per_beat):
        lo, hi = self.ZOOM_RANGE
        self.pixels_per_beat = min(max(pixels_per_beat, lo), hi)
        visible = (self.screen.get_width() - self.lane_left) / self.pixels_per_beat
        self.show_popup(f"Zoom {self.pixels_per_beat / self.DEFAULT_PIXELS_PER_BEAT:.0%}",
                        f"{visible:.1f} beats on screen")

    def show_popup(self, title, subtitle):
        self.popup = (title, subtitle, pygame.time.get_ticks())

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.VIDEORESIZE:
            self.layout()
        elif event.type == pygame.MOUSEWHEEL:
            self.zoom(event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.progress_rect.inflate(0, 16).collidepoint(event.pos):
                frac = (event.pos[0] - self.progress_rect.x) / self.progress_rect.w
                self.seek(frac * self.song_end)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
            elif event.key == pygame.K_SPACE:
                if self.beat >= self.song_end:
                    self.beat = -self.LEAD_IN_BEATS
                self.playing = not self.playing
                self.resync_audio()
            elif event.key == pygame.K_RIGHT:
                self.seek(self.beat + self.SEEK_BEATS)
            elif event.key == pygame.K_LEFT:
                self.seek(self.beat - self.SEEK_BEATS)
            elif event.key == pygame.K_UP:
                self.change_speed(1)
            elif event.key == pygame.K_DOWN:
                self.change_speed(-1)
            elif event.key == pygame.K_r:
                self.change_speed(self.SPEEDS.index(1.0) - self.speed_index)
            elif event.key == pygame.K_k:
                self.show_all_keys = not self.show_all_keys
                self.layout()
                self.show_popup("All keys" if self.show_all_keys else "Song keys only",
                                f"{len(self.lanes)} of {len(fg.KEYS)} keys shown")
            elif event.key == pygame.K_z:
                self.set_zoom(self.DEFAULT_PIXELS_PER_BEAT)
            elif event.key == pygame.K_PAGEUP:
                self.zoom(1)
            elif event.key == pygame.K_PAGEDOWN:
                self.zoom(-1)
            elif event.key == pygame.K_HOME:
                self.seek(-self.LEAD_IN_BEATS)
        return True

    # ---------- Drawing ----------

    def draw_grid(self):
        """Beat and measure lines scrolling through the lanes"""
        w = self.screen.get_width()
        first = int(np.floor(self.beat - (self.playline_x - self.lane_left) / self.pixels_per_beat))
        last = int(self.beat + (w - self.playline_x) / self.pixels_per_beat) + 1
        for b in range(max(first, 0), last + 1):
            x = self.beat_to_x(b)
            if x < self.lane_left:
                continue
            is_bar = b % self.beats_per_bar == 0
            color = (70, 95, 140) if is_bar else (40, 60, 100)
            pygame.draw.line(self.screen, color, (x, self.lanes_top), (x, self.lanes_bottom), 1)
            if is_bar:
                # Bar line and measure number on the staff
                top = self.bottom_line_y - 4 * self.LINE_SPACING
                bx = x - self.LINE_SPACING * 0.6
                pygame.draw.line(self.screen, (150, 170, 205), (bx, top), (bx, self.bottom_line_y), 2)
                num = self.text(self.font_small, str(b // self.beats_per_bar + 1), self.TEXT_DIM)
                self.screen.blit(num, (x - 4, 8))

    def draw_bars(self, current):
        w = self.screen.get_width()
        self.screen.set_clip(pygame.Rect(self.lane_left, self.lanes_top, w - self.lane_left,
                                         self.lanes_bottom - self.lanes_top))
        for note in self.visible_notes():
            xs, xe = self.beat_to_x(note['start']), self.beat_to_x(note['end'])
            active = note is current
            width = max(xe - xs - self.BAR_GAP, 6)
            if not note['keys'] and note['note'] in fg.FINGERINGS:
                self.draw_open_marker(xs, width, active, played=note['end'] <= self.beat)
                continue
            for key in note['keys']:
                lane = self.lanes[key]
                bh = lane['h'] * (0.62 if lane['shape'] == 'main' else 0.66)
                radius = int(min(bh, width) / 2)
                rect = pygame.Rect(xs, lane['cy'] - bh / 2, width, bh)
                color = lane['color']
                if active:
                    color = tuple(min(255, c + (255 - c) * 0.35) for c in color)
                elif note['end'] <= self.beat:
                    color = self.dim(color)
                if note['optional']:
                    # Optional fingering: see-through fill with a solid outline
                    fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(fill, (*color, 70 if active else 45), fill.get_rect(), border_radius=radius)
                    self.screen.blit(fill, rect)
                    pygame.draw.rect(self.screen, color, rect, 2, border_radius=radius)
                    continue
                pygame.draw.rect(self.screen, color, rect, border_radius=radius)
                if active:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=radius)
        self.screen.set_clip(None)

    def draw_open_marker(self, x, width, active, played):
        """Outlined OPEN pill across the L1-L3 lanes for notes played with no keys"""
        top = self.lanes['L1']['y'] + 6
        rect = pygame.Rect(x, top, width, self.lanes['L3']['y'] + self.lanes['L3']['h'] - 6 - top)
        radius = int(min(rect.w, 28) / 2)
        color = (235, 240, 255) if active else self.dim(self.OPEN_GREY) if played else self.OPEN_GREY
        fill = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(fill, (*color, 60 if active else 25), fill.get_rect(), border_radius=radius)
        self.screen.blit(fill, rect)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=radius)
        label = self.text(self.font_label_bold, 'OPEN', color)
        if label.get_width() + 12 < rect.w:
            self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_staff_notes(self, current):
        w = self.screen.get_width()
        self.screen.set_clip(pygame.Rect(self.lane_left, 0, w, self.staff_height))
        ls = self.LINE_SPACING
        half = ls / 2
        head_w, head_h = ls * 1.35, ls * 0.95
        for note in self.visible_notes():
            written = note['note'] + ALTO_TRANSPOSE
            _, accidental, _ = spell(written)
            step = staff_step(written)
            y = self.bottom_line_y - (step - self.BOTTOM_LINE_STEP) * half
            cx = self.beat_to_x(note['start']) + head_w / 2 + 2
            active = note is current
            played = not active and note['end'] <= self.beat
            color = self.HIGHLIGHT if active else self.TEXT_DIM if played else self.TEXT

            # Duration trail
            trail_end = self.beat_to_x(note['end']) - self.BAR_GAP
            if trail_end > cx:
                pygame.draw.line(self.screen, (70, 100, 150), (cx, y), (trail_end, y), 4)

            # Ledger lines below and above the staff
            ledgers = list(range(28, step - 1, -2)) + list(range(40, step + 1, 2))
            for s in ledgers:
                ly = self.bottom_line_y - (s - self.BOTTOM_LINE_STEP) * half
                pygame.draw.line(self.screen, (150, 170, 205), (cx - head_w * 0.85, ly), (cx + head_w * 0.85, ly), 2)

            pygame.draw.ellipse(self.screen, color, pygame.Rect(cx - head_w / 2, y - head_h / 2, head_w, head_h))
            if accidental:
                acc = self.text(self.font_accidental, ACCIDENTAL_GLYPH[accidental], color)
                self.screen.blit(acc, acc.get_rect(right=cx - head_w / 2 - 3, centery=y - 3))

            font = self.font_label_bold if active else self.font_label
            name = self.text(font, note_name(written), self.HIGHLIGHT if active else self.TEXT_DIM)
            self.screen.blit(name, name.get_rect(centerx=cx, y=self.names_y))
        self.screen.set_clip(None)

    def draw_pressed_keys(self, current):
        if not current:
            return
        for key in current['keys']:
            lane = self.lanes[key]
            if current['optional']:
                # Half-lit icon: suggested, not required
                half = tuple((c + b) // 2 for c, b in zip(lane['color'], (32, 44, 72)))
                self.draw_key_icon(self.screen, lane, pressed=True, color=half)
                continue
            radius = int(max(lane['h'] * 0.6, 24))
            glow = self.glow(lane['color'], radius)
            self.screen.blit(glow, glow.get_rect(center=(lane['icon_x'], lane['cy'])))
            self.draw_key_icon(self.screen, lane, pressed=True)

    def draw_lane_labels(self, current):
        """Key names: bold white when pressed, brighter for optional keys, dim otherwise"""
        pressed = set(current['keys']) if current else set()
        optional = bool(current and current['optional'])
        for key, lane in self.lanes.items():
            font = self.lane_font(lane)
            color = self.TEXT_DIM
            if key in pressed and optional:
                color = self.TEXT
            elif key in pressed:
                font = self.font_label_bold if font is self.font_label else font
                color = (255, 255, 255)
            label = self.text(font, lane['label'], color)
            self.screen.blit(label, label.get_rect(x=16, centery=lane['cy']))

    def draw_playline(self):
        x = self.playline_x
        pygame.draw.line(self.screen, (235, 240, 255), (x, 20), (x, self.lanes_bottom), 2)
        pygame.draw.polygon(self.screen, (235, 240, 255), [(x - 7, 12), (x + 7, 12), (x, 22)])

    def draw_note_card(self, current):
        """Big current-note readout in the top-left corner"""
        hint = None
        if current:
            written = current['note'] + ALTO_TRANSPOSE
            name = self.text(self.font_big, note_name(written), self.HIGHLIGHT)
            sub = f"concert {note_name(current['note'])}"
            hint = current['fingering']
            if current['note'] not in fg.FINGERINGS:
                sub = "out of alto range"
        else:
            name = self.text(self.font_big, '\u2014', self.TEXT_DIM)
            sub = 'rest' if self.beat >= 0 else 'get ready'
        self.screen.blit(self.text(self.font_small, 'NOW PLAYING', self.TEXT_DIM), (18, 20))
        self.screen.blit(name, (16, 40))
        self.screen.blit(self.text(self.font_small, sub, self.TEXT_DIM), (18, 116))
        if hint:
            self.screen.blit(self.text(self.font_small, hint, self.HIGHLIGHT), (18, 140))

    def draw_footer(self):
        w, h = self.screen.get_size()
        y0 = h - self.FOOTER_HEIGHT
        self.progress_rect = pygame.Rect(16, y0 + 10, w - 32, 6)
        pygame.draw.rect(self.screen, (50, 70, 110), self.progress_rect, border_radius=3)
        frac = min(max(self.beat / self.song_end, 0), 1) if self.song_end else 0
        filled = self.progress_rect.copy()
        filled.w = int(self.progress_rect.w * frac)
        pygame.draw.rect(self.screen, self.HIGHLIGHT, filled, border_radius=3)
        pygame.draw.circle(self.screen, (255, 255, 255), (filled.right, filled.centery), 7)

        state = '❚❚ Paused' if not self.playing else '▶ Playing'
        info = f"{state}    {self.format_time(self.beat)} / {self.format_time(self.song_end)}"
        info = self.text(self.font_label, info, self.TEXT)
        self.screen.blit(info, (16, y0 + 26))

        speed = self.text(self.font_label, f"{self.bpm * self.speed:.0f} BPM  \u00b7  {self.speed:.0%}", self.TEXT)

        # Key hints in the middle; shrink or hide them if the window is too narrow
        hints = ("Space play/pause   \u2190/\u2192 rewind/forward   \u2191/\u2193 speed   R reset speed   "
                 "Scroll/PgUp/PgDn zoom   Z reset zoom   K all keys   Home restart")
        room = w - info.get_width() - speed.get_width() - 80
        for font in (self.font_small, self.font_tiny):
            hint = self.text(font, hints, self.TEXT_DIM)
            if hint.get_width() <= room:
                self.screen.blit(hint, hint.get_rect(centerx=w / 2, centery=y0 + 26 + info.get_height() / 2))
                break

        self.screen.blit(speed, speed.get_rect(right=w - 16, y=y0 + 26))

    def draw_popup(self):
        """Briefly show a speed/zoom change in the middle of the screen"""
        if not self.popup:
            return
        title, subtitle, shown_at = self.popup
        age = pygame.time.get_ticks() - shown_at
        if age > 1200:
            return
        alpha = 255 if age < 800 else int(255 * (1200 - age) / 400)
        w, h = self.screen.get_size()
        label = self.text(self.font_big, title, (255, 255, 255))
        sub = self.text(self.font_label, subtitle, self.TEXT)
        box = pygame.Rect(0, 0, label.get_width() + 60, label.get_height() + sub.get_height() + 36)
        box.center = (self.lane_left + (w - self.lane_left) / 2, h / 2)
        popup = pygame.Surface(box.size, pygame.SRCALPHA)
        pygame.draw.rect(popup, (10, 16, 32, 220), popup.get_rect(), border_radius=16)
        popup.blit(label, label.get_rect(centerx=box.w / 2, y=14))
        popup.blit(sub, sub.get_rect(centerx=box.w / 2, y=18 + label.get_height()))
        popup.set_alpha(alpha)
        self.screen.blit(popup, box)

    def draw(self):
        current = self.current_note()
        self.screen.blit(self.background, (0, 0))
        self.draw_grid()
        self.draw_bars(current)
        self.draw_staff_notes(current)
        self.draw_lane_labels(current)
        self.draw_pressed_keys(current)
        self.draw_playline()
        self.draw_note_card(current)
        self.draw_footer()
        self.draw_popup()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False

            dt = clock.tick(60) / 1000
            if self.playing:
                prev_beat = self.beat
                self.beat += dt * self.bpm / 60 * self.speed
                if self.beat >= self.song_end:
                    self.beat = self.song_end
                    self.playing = False
                self.update_audio(prev_beat)

            self.draw()
            pygame.display.flip()

        pygame.quit()

    def save_video(self, filename, fps=60):
        """Save recorded frames as video"""
        if self.frames:
            print(f"\nSaving video to {filename}...")
            clip = ImageSequenceClip(self.frames, fps=fps)
            clip.write_videofile(filename)
            print("Video saved successfully!")
        else:
            print("No frames captured. Video not saved.")


def main():
    midi_file = sys.argv[1] if len(sys.argv) > 1 else "test.mid"
    try:
        visualizer = SaxophoneVisualizer(midi_file)
        visualizer.run()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
