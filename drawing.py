"""Layout and rendering for the visualizer (mixed into SaxophoneVisualizer)"""

from bisect import bisect_left, bisect_right

import numpy as np
import pygame

import fingerings as fg
from notation import ACCIDENTAL_GLYPH, note_name, spell, staff_step


class DrawingMixin:
    """Methods that position and draw everything; state lives on SaxophoneVisualizer"""

    # ---------- Layout & static background ----------

    def fit_staff_to_song(self):
        """Size the staff area to the song's pitch range so the big staff doesn't waste lane space"""
        steps = [staff_step(n['written']) for n in self.notes]
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
        self.track_button_rect = pygame.Rect(16, 162, self.lane_left - 112, 24)
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

    def visible_notes(self):
        w = self.screen.get_width()
        history_beats = (self.playline_x - self.lane_left) / self.pixels_per_beat
        ahead_beats = (w - self.playline_x) / self.pixels_per_beat
        lo = bisect_left(self.starts, self.beat - history_beats - self.max_duration - 1)
        hi = bisect_right(self.starts, self.beat + ahead_beats + 1)
        return self.notes[lo:hi]

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
            for key in note['keys']:
                lane = self.lanes[key]
                bh = lane['h'] * (0.62 if lane['shape'] == 'main' else 0.66)
                radius = int(min(self.BAR_RADIUS, bh / 2, width / 2))
                rect = pygame.Rect(xs, lane['cy'] - bh / 2, width, bh)
                color = lane['color']
                if active:
                    color = tuple(min(255, c + (255 - c) * 0.35) for c in color)
                elif note['end'] <= self.beat:
                    color = self.dim(color)
                if key in note['optional_keys']:
                    # Optional key: see-through fill with a solid outline
                    fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(fill, (*color, 70 if active else 45), fill.get_rect(), border_radius=radius)
                    self.screen.blit(fill, rect)
                    pygame.draw.rect(self.screen, color, rect, 2, border_radius=radius)
                    continue
                pygame.draw.rect(self.screen, color, rect, border_radius=radius)
                if active:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=radius)
        self.screen.set_clip(None)

    def draw_staff_notes(self, current):
        w = self.screen.get_width()
        self.screen.set_clip(pygame.Rect(self.lane_left, 0, w, self.staff_height))
        ls = self.LINE_SPACING
        half = ls / 2
        head_w, head_h = ls * 1.35, ls * 0.95
        for note in self.visible_notes():
            written = note['written']
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
            if key in current['optional_keys']:
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
        optional = current['optional_keys'] if current else set()
        for key, lane in self.lanes.items():
            font = self.lane_font(lane)
            color = self.TEXT_DIM
            if key in optional:
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
            name = self.text(self.font_big, note_name(current['written']), self.HIGHLIGHT)
            sub = f"concert {note_name(current['note'])}"
            hint = current['fingering']
            if not current['in_range']:
                hint = f"out of {fg.INSTRUMENTS[self.instrument]['name'].lower()} range"
        else:
            name = self.text(self.font_big, '\u2014', self.TEXT_DIM)
            sub = 'rest' if self.beat >= 0 else 'get ready'
        self.screen.blit(self.text(self.font_small, f"SAX TRACK {self.track_index + 1}/{len(self.tracks)} · Click to choose" if self.tracks else 'NO NOTE TRACKS', self.TEXT_DIM), (18, 20))
        self.screen.blit(name, (16, 40))
        self.screen.blit(self.text(self.font_small, sub, self.TEXT_DIM), (18, 116))
        if hint:
            self.screen.blit(self.text(self.font_small, hint, self.HIGHLIGHT), (18, 140))
        pygame.draw.rect(self.screen, (40, 62, 100), self.track_button_rect, border_radius=5)
        caption = f"Sax track {self.track_index + 1}/{len(self.tracks)}  ▾" if self.tracks else 'No note tracks'
        self.screen.blit(self.text(self.font_small, caption, self.TEXT), (22, 165))

    def track_menu_geometry(self):
        w, h = self.screen.get_size()
        rows = min(len(self.tracks), max(1, (h - 180) // 48))
        box = pygame.Rect(0, 0, min(720, w - 32), 112 + rows * 48)
        box.center = (w // 2, h // 2)
        self.track_menu_offset = min(max(self.track_menu_offset, 0), max(0, len(self.tracks) - rows))
        entries = [(i, pygame.Rect(box.x + 12, box.y + 60 + j * 48, box.w - 24, 44))
                   for j, i in enumerate(range(self.track_menu_offset,
                                               min(len(self.tracks), self.track_menu_offset + rows)))]
        backing = pygame.Rect(box.x + 12, box.bottom - 42, box.w - 24, 30)
        return box, entries, backing

    @staticmethod
    def track_mute_rect(row):
        return pygame.Rect(row.right - 92, row.y + 7, 82, 30)

    def draw_track_menu(self):
        if not self.track_menu_open:
            return
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        self.screen.blit(shade, (0, 0))
        box, entries, backing = self.track_menu_geometry()
        pygame.draw.rect(self.screen, (22, 35, 60), box, border_radius=12)
        self.screen.blit(self.text(self.font_label_bold, 'Choose the track to display as saxophone', self.TEXT),
                         (box.x + 16, box.y + 10))
        self.screen.blit(self.text(self.font_tiny, 'Click a track to display · Mute toggles sound · Click outside to close', self.TEXT_DIM),
                         (box.x + 16, box.y + 36))
        for index, rect in entries:
            selected = index == self.track_index
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (65, 75, 90) if selected else (38, 58, 92) if hover else (28, 44, 72),
                             rect, border_radius=5)
            label = ('✓ ' if selected else '') + self.track_label(index)
            rendered = self.text(self.font_small, label, self.HIGHLIGHT if selected else self.TEXT)
            self.screen.blit(rendered, (rect.x + 10, rect.y + 4), pygame.Rect(0, 0, rect.w - 112, 22))
            detail = f"{len(self.tracks[index]['notes'])} notes · " + ('Saxophone chart' if selected else 'Backing')
            self.screen.blit(self.text(self.font_tiny, detail, self.TEXT_DIM), (rect.x + 10, rect.y + 25))
            muted = self.tracks[index]['index'] in self.muted_tracks
            mute_rect = self.track_mute_rect(rect)
            pygame.draw.rect(self.screen, (115, 55, 60) if muted else (40, 75, 95), mute_rect, border_radius=5)
            mute_label = self.text(self.font_small, 'Unmute' if muted else 'Mute', self.TEXT)
            self.screen.blit(mute_label, mute_label.get_rect(center=mute_rect.center))
        pygame.draw.rect(self.screen, (40, 62, 100), backing, border_radius=5)
        self.screen.blit(self.text(self.font_small, '☑ Play backing tracks' if self.backing_enabled else '☐ Play backing tracks', self.TEXT),
                         (backing.x + 10, backing.y + 4))

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

        speed = self.text(self.font_label, f"{fg.INSTRUMENTS[self.instrument]['name']}  \u00b7  "
                                           f"{self.bpm * self.speed:.0f} BPM  \u00b7  {self.speed:.0%}", self.TEXT)

        # Key hints in the middle; shrink or hide them if the window is too narrow
        hints = ("Space play \u00b7 \u2190/\u2192 seek \u00b7 \u2191/\u2193 speed (R reset) \u00b7 Scroll zoom (Z reset) \u00b7 "
                 "Click Sax track · B backing · Drag/side-scroll scrub \u00b7 K keys \u00b7 S alto/tenor \u00b7 H/Home restart")
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
        box = pygame.Rect(0, 0, max(label.get_width(), sub.get_width()) + 60,
                          label.get_height() + sub.get_height() + 36)
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
        self.draw_track_menu()
