"""Music notation helpers: note spelling, names and staff positions"""

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
