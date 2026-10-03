"""Load MIDI notes while preserving their source tracks and channels."""

from collections import defaultdict, deque

import mido


def load_midi_tracks(path):
    midi = mido.MidiFile(path)
    tempo = None
    beats_per_bar = 4
    tracks = []
    for index, track in enumerate(midi.tracks):
        tick = 0
        opened = defaultdict(deque)
        programs = defaultdict(int)
        notes = []
        name = track.name or f'Track {index + 1}'
        for msg in track:
            tick += msg.time
            if msg.type == 'set_tempo' and tempo is None:
                tempo = msg.tempo
            elif msg.type == 'time_signature':
                beats_per_bar = msg.numerator
            elif msg.type == 'program_change':
                programs[msg.channel] = msg.program
            elif msg.type == 'note_on' and msg.velocity > 0:
                opened[(msg.channel, msg.note)].append((tick, msg.velocity, programs[msg.channel]))
            elif msg.type in ('note_off', 'note_on'):
                queue = opened[(msg.channel, msg.note)]
                if queue:
                    start, velocity, program = queue.popleft()
                    notes.append(dict(note=msg.note, start=start / midi.ticks_per_beat,
                                      end=tick / midi.ticks_per_beat, channel=msg.channel,
                                      velocity=velocity, program=program, track=index))
        for (channel, pitch), queue in opened.items():
            for start, velocity, program in queue:
                notes.append(dict(note=pitch, start=start / midi.ticks_per_beat,
                                  end=tick / midi.ticks_per_beat, channel=channel,
                                  velocity=velocity, program=program, track=index))
        if notes:
            notes.sort(key=lambda n: n['start'])
            tracks.append(dict(index=index, name=name, notes=notes))
    return tracks, mido.tempo2bpm(tempo or 500000), beats_per_bar


def load_midi(path):
    """Compatibility helper returning all tracks as one note list."""
    tracks, bpm, meter = load_midi_tracks(path)
    notes = sorted((n for track in tracks for n in track['notes']), key=lambda n: n['start'])
    return notes, bpm, meter


def instrument_name(note):
    """Readable names for track menus, using zero-based GM program numbers."""
    if note['channel'] == 9:
        return 'Drums'
    program = note['program']
    names = {0: 'Acoustic piano', 1: 'Bright piano', 4: 'Electric piano',
             24: 'Nylon guitar', 25: 'Steel guitar', 26: 'Jazz guitar',
             27: 'Clean guitar', 28: 'Muted guitar', 32: 'Acoustic bass',
             33: 'Electric bass', 40: 'Violin', 42: 'Cello', 44: 'Tremolo strings',
             48: 'Strings', 64: 'Soprano sax', 65: 'Alto sax',
             66: 'Tenor sax', 67: 'Baritone sax'}
    if program in names:
        return names[program]
    families = ['Piano', 'Chromatic percussion', 'Organ', 'Guitar', 'Bass',
                'Strings', 'Ensemble', 'Brass', 'Reed', 'Pipe', 'Synth lead',
                'Synth pad', 'Synth effects', 'Ethnic', 'Percussive', 'Sound effects']
    return f'{families[program // 8]} (GM {program + 1})'
