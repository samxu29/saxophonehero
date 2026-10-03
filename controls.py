"""Keyboard and mouse controls for the visualizer (mixed into SaxophoneVisualizer)"""

import pygame

import fingerings as fg


class ControlsMixin:
    """Input handling and the actions it triggers (seek, speed, zoom, scrubbing)"""

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

    def in_scroll_area(self, pos):
        """True over the scrolling notes (lanes and staff), which can be dragged to scrub"""
        return pos[0] >= self.lane_left and pos[1] < self.lanes_bottom

    def progress_beat(self, x):
        frac = min(max((x - self.progress_rect.x) / self.progress_rect.w, 0), 1)
        return frac * self.song_end

    def scroll(self, amount):
        """Move through the song by scroll-wheel units (positive = forward); sound resumes once scrolling stops"""
        beat = self.beat + amount * self.SCROLL_PIXELS / self.pixels_per_beat
        self.beat = min(max(beat, -self.LEAD_IN_BEATS), self.song_end)
        if self.audio_enabled:
            self.stop_audio()
        self.scroll_resync_at = pygame.time.get_ticks() + 150

    def set_cursor(self, cursor):
        if cursor != self.cursor:
            self.cursor = cursor
            try:
                pygame.mouse.set_cursor(cursor)
            except pygame.error:
                pass  # no system cursors on this platform; dragging still works

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.VIDEORESIZE:
            self.layout()
        elif self.track_menu_open:
            box, entries, backing = self.track_menu_geometry()
            if event.type == pygame.MOUSEWHEEL:
                self.track_menu_offset -= event.y
                self.track_menu_geometry()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if backing.collidepoint(event.pos):
                    self.toggle_backing()
                elif not box.collidepoint(event.pos):
                    self.track_menu_open = False
                else:
                    for index, rect in entries:
                        if self.track_mute_rect(rect).collidepoint(event.pos):
                            self.toggle_track_mute(index)
                            break
                        if rect.collidepoint(event.pos):
                            self.select_track(index)
                            self.track_menu_open = False
                            break
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_t):
                self.track_menu_open = False
            return True
        elif event.type == pygame.MOUSEWHEEL:
            # Horizontal scroll (tilt/thumb wheel, touchpad swipe, or Shift + wheel) moves through the
            # song; plain vertical scroll zooms
            dx = getattr(event, 'precise_x', event.x)
            dy = getattr(event, 'precise_y', event.y)
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                dx, dy = dx or -dy, 0
            if abs(dx) > abs(dy):
                self.scroll(dx)
            elif event.y:
                self.zoom(event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.track_button_rect.collidepoint(event.pos):
                self.track_menu_open = True
                self.track_menu_offset = self.track_index
                self.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                return True
            # Grab the notes (drag left = forward) or the progress bar; playback holds while dragging
            if self.progress_rect.inflate(0, 16).collidepoint(event.pos):
                self.drag = ('progress', None, None)
                self.beat = self.progress_beat(event.pos[0])
            elif self.in_scroll_area(event.pos):
                self.drag = ('notes', event.pos[0], self.beat)
            if self.drag and self.audio_enabled:
                self.stop_audio()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            self.drag = None
            self.seek(self.beat)  # clamp and resume sound from the new position
        elif event.type == pygame.MOUSEMOTION:
            if self.drag:
                kind, start_x, start_beat = self.drag
                if kind == 'progress':
                    self.beat = self.progress_beat(event.pos[0])
                else:
                    beat = start_beat - (event.pos[0] - start_x) / self.pixels_per_beat
                    self.beat = min(max(beat, -self.LEAD_IN_BEATS), self.song_end)
            if self.drag and self.drag[0] == 'notes':
                self.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
            elif self.track_button_rect.collidepoint(event.pos) or self.progress_rect.inflate(0, 16).collidepoint(event.pos) or self.drag:
                self.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            elif self.in_scroll_area(event.pos):
                self.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
            else:
                self.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
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
            elif event.key == pygame.K_t:
                self.track_menu_open = True
                self.track_menu_offset = self.track_index
            elif event.key == pygame.K_b:
                self.toggle_backing()
            elif event.key == pygame.K_s:
                self.toggle_instrument()
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
            elif event.key in (pygame.K_HOME, pygame.K_h):
                self.seek(-self.LEAD_IN_BEATS)
        return True
