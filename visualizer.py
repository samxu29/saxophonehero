"""The Saxophone Hero app: song state, playback and the main loop"""

from bisect import bisect_right

import pygame
from moviepy import ImageSequenceClip

import fingerings as fg
from controls import ControlsMixin
from drawing import DrawingMixin
from midi_loader import load_midi_tracks, instrument_name
from synth import SAMPLE_RATE, SaxSynth, BackingSynth


class SaxophoneVisualizer(DrawingMixin, ControlsMixin):
    SAMPLE_RATE = SAMPLE_RATE
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
    BAR_GAP = 5  # pixels of empty space after each note bar
    BAR_RADIUS = 8  # corner rounding of note bars (a large value like 99 gives full pill ends)
    SCROLL_PIXELS = 60  # how far one horizontal scroll step moves the notes
    PLAYLINE_FRACTION = 0.25  # playline position across the scrolling area; left of it is history

    # Staff geometry (within the staff area)
    LINE_SPACING = 18
    BOTTOM_LINE_STEP = 30  # E4 = 4 * 7 + 2
    TOP_LINE_STEP = 38  # F5

    BG_TOP = (14, 24, 48)
    BG_BOTTOM = (22, 50, 94)
    TEXT = (225, 232, 245)
    TEXT_DIM = (120, 140, 175)
    HIGHLIGHT = (255, 214, 90)

    def __init__(self, midi_file, window_size=(1600, 900)):
        self.midi_file = midi_file
        self.frames = []
        self.tracks, self.bpm, self.beats_per_bar = load_midi_tracks(midi_file)
        self.track_index = next((i for i, track in enumerate(self.tracks)
                                 if any(n['channel'] != 9 and 64 <= n['program'] <= 67
                                        for n in track['notes'])),
                                next((i for i, track in enumerate(self.tracks)
                                      if any(n['channel'] != 9 for n in track['notes'])), 0))
        self.notes = self.tracks[self.track_index]['notes'] if self.tracks else []
        self.track_menu_open = False
        self.track_menu_offset = 0
        self.muted_tracks = set()
        self.backing_enabled = True
        self.refresh_backing()
        self.starts = [n['start'] for n in self.notes]
        self.show_all_keys = False
        self.set_instrument(fg.DEFAULT_INSTRUMENT)
        self.max_duration = max((n['end'] - n['start'] for n in self.notes), default=0)
        self.song_end = max((n['end'] for t in self.tracks for n in t['notes']), default=0)

        self.beat = -self.LEAD_IN_BEATS
        self.playing = True
        self.speed_index = self.SPEEDS.index(1.0)
        self.pixels_per_beat = self.DEFAULT_PIXELS_PER_BEAT
        self.popup = None  # (title, subtitle, shown_at_ms)
        self.cursor = pygame.SYSTEM_CURSOR_ARROW
        self.drag = None  # ('notes', start_x, start_beat) or ('progress', None, None) while dragging
        self.scroll_resync_at = None  # when to restart sound after horizontal scrolling

        pygame.mixer.pre_init(self.SAMPLE_RATE, -16, 1, 512)
        pygame.init()
        self.audio_enabled = pygame.mixer.get_init() is not None
        if self.audio_enabled:
            pygame.mixer.set_num_channels(64)
            pygame.mixer.set_reserved(1)
            self.sax_channel = pygame.mixer.Channel(0)
        else:
            print("Audio unavailable; running without sound.")
        self.synth = SaxSynth(self.SAMPLE_RATE)
        self.backing_synth = BackingSynth(self.SAMPLE_RATE)

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

    def refresh_backing(self):
        self.backing_notes = sorted((n for i, track in enumerate(self.tracks)
                                     if i != self.track_index for n in track['notes']),
                                    key=lambda n: n['start'])
        self.backing_starts = [n['start'] for n in self.backing_notes]

    def track_label(self, index):
        track = self.tracks[index]
        instruments = list(dict.fromkeys(instrument_name(n) for n in track['notes']))
        return f"{track['name']} — {', '.join(instruments)}"

    def cycle_track(self, step=1):
        if self.tracks:
            self.select_track((self.track_index + step) % len(self.tracks))

    def select_track(self, index):
        if not self.tracks:
            self.show_popup("No note tracks", "This MIDI contains no notes")
            return
        self.track_index = index
        self.notes = self.tracks[self.track_index]['notes']
        self.starts = [n['start'] for n in self.notes]
        self.max_duration = max((n['end'] - n['start'] for n in self.notes), default=0)
        self.refresh_backing()
        self.set_instrument(self.instrument)
        self.resync_audio()
        self.show_popup(self.tracks[self.track_index]['name'],
                        f"Sax track {self.track_index + 1} of {len(self.tracks)}")

    def toggle_track_mute(self, index):
        track_id = self.tracks[index]['index']
        if track_id in self.muted_tracks:
            self.muted_tracks.remove(track_id)
        else:
            self.muted_tracks.add(track_id)
        self.resync_audio()

    def toggle_backing(self):
        self.backing_enabled = not self.backing_enabled
        self.resync_audio()
        self.show_popup("Backing on" if self.backing_enabled else "Backing muted",
                        "Other tracks accompany the selected sax track")

    def stop_audio(self):
        if self.audio_enabled:
            pygame.mixer.stop()

    def play_backing(self, note):
        if (not self.audio_enabled or not self.backing_enabled
                or note['track'] in self.muted_tracks or note['end'] <= self.beat):
            return
        channel = next((pygame.mixer.Channel(i) for i in range(1, pygame.mixer.get_num_channels())
                        if not pygame.mixer.Channel(i).get_busy()), None)
        if channel:
            duration = (note['end'] - self.beat) * 60 / self.bpm / self.speed
            channel.play(self.backing_synth.note_sound(note, duration))

    @staticmethod
    def load_font(names, size, bold=False):
        return pygame.font.Font(pygame.font.match_font(names, bold=bold), size)

    def set_instrument(self, instrument):
        """Switch alto/tenor: re-transpose notes and refit the staff and lanes"""
        self.instrument = instrument
        self.transpose = fg.INSTRUMENTS[instrument]['transpose']
        fg.assign_fingerings(self.notes, self.transpose)
        self.used_keys = {key for n in self.notes for key in n['keys']}
        if hasattr(self, 'screen'):  # already set up (toggling while running)
            self.fit_staff_to_song()
            self.layout()

    def toggle_instrument(self):
        names = list(fg.INSTRUMENTS)
        self.set_instrument(names[(names.index(self.instrument) + 1) % len(names)])
        info = fg.INSTRUMENTS[self.instrument]
        out = sum(not n['in_range'] for n in self.notes)
        detail = f"{info['key']} \u00b7 written = concert + {self.transpose} semitones"
        self.show_popup(info['name'], detail + (f" \u00b7 {out} notes out of range" if out else ""))

    @property
    def speed(self):
        return self.SPEEDS[self.speed_index]

    def current_note(self):
        """Note sounding at the current beat, if any"""
        i = bisect_right(self.starts, self.beat) - 1
        if i >= 0 and self.notes[i]['start'] <= self.beat < self.notes[i]['end']:
            return self.notes[i]
        return None

    def format_time(self, beat):
        seconds = max(beat, 0) * 60 / self.bpm
        return f"{int(seconds // 60)}:{int(seconds % 60):02d}"

    def play_from(self, note, beat):
        """Play the rest of a note starting at the given beat"""
        if not self.audio_enabled or note['track'] in self.muted_tracks:
            return
        remaining_beats = note['end'] - beat
        if remaining_beats < 0.05:
            return
        duration = remaining_beats * 60 / self.bpm / self.speed
        self.sax_channel.play(self.synth.note_sound(note['note'], duration))

    def update_audio(self, prev_beat):
        """Trigger the latest note that started since the previous frame"""
        i0 = bisect_right(self.starts, prev_beat)
        i1 = bisect_right(self.starts, self.beat)
        if i1 > i0:
            self.play_from(self.notes[i1 - 1], self.beat)
        for note in self.backing_notes[bisect_right(self.backing_starts, prev_beat):
                                       bisect_right(self.backing_starts, self.beat)]:
            self.play_backing(note)

    def resync_audio(self):
        """After a seek/pause/speed change, restart whatever should be sounding"""
        if not self.audio_enabled:
            return
        self.stop_audio()
        note = self.current_note()
        if self.playing and note:
            self.play_from(note, self.beat)
        if self.playing:
            for backing in self.backing_notes:
                if backing['start'] <= self.beat < backing['end']:
                    self.play_backing(backing)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False

            dt = clock.tick(60) / 1000
            if self.scroll_resync_at and pygame.time.get_ticks() >= self.scroll_resync_at:
                self.scroll_resync_at = None
                self.resync_audio()
            if self.playing and not self.drag:
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
