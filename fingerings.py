"""Alto saxophone keys and fingerings.

Edit this file to rename keys, move their icons, or change which keys a note uses.
Key IDs start with the hand and key group: L/R = left/right hand, then Thumb, Palm,
Front, Bis, Table (spatula), Side, Alt or Pinky. L1-L3 / R1-R3 are the main finger keys.
"""

# All keys, top-to-bottom as they sit on the instrument: (key id, label, group, icon shape)
KEYS = [
    ('LThumb_Oct', 'LThumb Oct', 'octave', 'tri'),
    ('LPalm_D', 'LPalm D', 'palm', 'oval'),
    ('LPalm_Eb', 'LPalm E♭', 'palm', 'oval'),
    ('LPalm_F', 'LPalm F', 'palm', 'oval'),
    ('LFront_F', 'LFront F', 'left', 'small'),
    ('L1', 'L1', 'left', 'main'),
    ('LBis', 'LBis B♭', 'left', 'small'),
    ('L2', 'L2', 'left', 'main'),
    ('L3', 'L3', 'left', 'main'),
    ('LTable_Gs', 'LTable G♯', 'left_table', 'table'),
    ('LTable_Cs', 'LTable C♯', 'left_table', 'table'),
    ('LTable_B', 'LTable B', 'left_table', 'table'),
    ('LTable_Bb', 'LTable B♭', 'left_table', 'table'),
    ('RSide_E', 'RSide E', 'side', 'side'),
    ('RSide_C', 'RSide C', 'side', 'side'),
    ('RSide_Bb', 'RSide B♭', 'side', 'side'),
    ('RSide_HighFs', 'RSide F♯', 'side', 'side_small'),
    ('R1', 'R1', 'right', 'main'),
    ('R2', 'R2', 'right', 'main'),
    ('RAlt_Fs', 'RAlt F♯', 'right', 'side_small'),
    ('R3', 'R3', 'right', 'main'),
    ('RPinky_Eb', 'RPinky E♭', 'right_pinky', 'pinky_top'),
    ('RPinky_C', 'RPinky C', 'right_pinky', 'pinky_bottom'),
]

# Always shown, even if a song never presses them, so the column still reads like a sax
ALWAYS_SHOWN = ('L1', 'L2', 'L3', 'R1', 'R2', 'R3')

GROUP_COLORS = {
    'octave': (255, 128, 170),      # Pink
    'palm': (255, 170, 80),         # Orange
    'left': (255, 214, 90),         # Yellow
    'left_table': (255, 140, 110),  # Coral
    'side': (240, 100, 100),        # Red
    'right': (110, 200, 255),       # Light blue
    'right_pinky': (90, 220, 190),  # Teal
}

# Icon position (pixels) relative to the main key column, following a standard fingering chart:
# thumb and side keys to the left, front F/bis/palm/table to the right, right pinky low-left
ICON_OFFSET = {
    'LThumb_Oct': -48,
    'LPalm_D': 50, 'LPalm_Eb': 64, 'LPalm_F': 40,
    'LFront_F': 20, 'LBis': 30,
    'LTable_Gs': 54, 'LTable_Cs': 43, 'LTable_B': 65, 'LTable_Bb': 54,
    'RSide_E': -46, 'RSide_C': -46, 'RSide_Bb': -46, 'RSide_HighFs': -38,
    'RAlt_Fs': -34,
    'RPinky_Eb': -36, 'RPinky_C': -36,
}
# Table (spatula) key widths: G# and Bb span the table, C# and B sit side by side
TABLE_WIDTH = {'LTable_Gs': 42, 'LTable_Cs': 20, 'LTable_B': 20, 'LTable_Bb': 42}
# Groups outlined as clusters in the key column
CLUSTERS = ('palm', 'left_table', 'side', 'right_pinky')

_LEFT = ['L1', 'L2', 'L3']
_ALL_SIX = ['L1', 'L2', 'L3', 'R1', 'R2', 'R3']

# Saxophones share fingerings by *written* note; each instrument only differs in how far
# written pitch sits above the concert pitch stored in MIDI files.
INSTRUMENTS = {
    'alto': {'name': 'Alto sax', 'key': 'E\u266d', 'transpose': 9},  # written = concert + major 6th
    'tenor': {'name': 'Tenor sax', 'key': 'B\u266d', 'transpose': 14},  # written = concert + major 9th
}
DEFAULT_INSTRUMENT = 'alto'

# Standard fingerings keyed by written-pitch MIDI note (same for alto and tenor)
FINGERINGS = {
    # Low register
    58: _ALL_SIX + ['LTable_Bb'],  # Bb3
    59: _ALL_SIX + ['LTable_B'],  # B3
    60: _ALL_SIX + ['RPinky_C'],  # C4
    61: _ALL_SIX + ['LTable_Cs'],  # C#4
    62: _ALL_SIX,  # D4
    63: _ALL_SIX + ['RPinky_Eb'],  # Eb4
    64: _LEFT + ['R1', 'R2'],  # E4
    65: _LEFT + ['R1'],  # F4
    66: _LEFT + ['R2'],  # F#4
    67: _LEFT,  # G4
    68: _LEFT + ['LTable_Gs'],  # G#4
    69: ['L1', 'L2'],  # A4
    70: ['L1', 'LBis'],  # Bb4
    71: ['L1'],  # B4
    72: ['L2'],  # C5
    73: [],  # C#5 (open; L3 shown as optional, see OPTIONAL_KEYS)
    # Middle and high register (with octave key)
    74: ['LThumb_Oct'] + _ALL_SIX,  # D5
    75: ['LThumb_Oct'] + _ALL_SIX + ['RPinky_Eb'],  # Eb5
    76: ['LThumb_Oct'] + _LEFT + ['R1', 'R2'],  # E5
    77: ['LThumb_Oct'] + _LEFT + ['R1'],  # F5
    78: ['LThumb_Oct'] + _LEFT + ['R2'],  # F#5
    79: ['LThumb_Oct'] + _LEFT,  # G5
    80: ['LThumb_Oct'] + _LEFT + ['LTable_Gs'],  # G#5
    81: ['LThumb_Oct', 'L1', 'L2'],  # A5
    82: ['LThumb_Oct', 'L1', 'LBis'],  # Bb5
    83: ['LThumb_Oct', 'L1'],  # B5
    84: ['LThumb_Oct', 'L2'],  # C6
    85: ['LThumb_Oct'],  # C#6 (L3 shown as optional, see OPTIONAL_KEYS)
    # Palm keys
    86: ['LThumb_Oct', 'LPalm_D'],  # D6
    87: ['LThumb_Oct', 'LPalm_D', 'LPalm_Eb'],  # Eb6
    88: ['LThumb_Oct', 'LPalm_D', 'LPalm_Eb', 'RSide_E'],  # E6
    89: ['LThumb_Oct', 'LPalm_D', 'LPalm_Eb', 'LPalm_F', 'RSide_E'],  # F6
}

# Extra keys shown see-through as "optional" on top of a note's standard fingering, keyed by
# written pitch, as (keys, card label). On open C# (C#5, and C#6 with the octave key),
# holding L3 down doesn't change the pitch.
OPTIONAL_KEYS = {
    73: (['L3'], 'open C\u266f \u00b7 L3 optional'),  # C#5
    85: (['L3'], 'C\u266f \u00b7 L3 optional'),  # C#6
}


def assign_fingerings(notes, transpose):
    """Set note['written'], note['keys'] (all keys to show), note['optional_keys'],
    note['fingering'] (card label) and note['in_range'] for an instrument's transposition"""
    for note in notes:
        written = note['note'] + transpose
        keys = FINGERINGS.get(written, [])
        optional, label = OPTIONAL_KEYS.get(written, ([], None))
        note['written'] = written
        note['in_range'] = written in FINGERINGS
        note['keys'] = keys + [k for k in optional if k not in keys]
        note['optional_keys'] = set(optional)
        note['fingering'] = label
