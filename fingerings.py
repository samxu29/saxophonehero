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

# Standard fingerings keyed by concert-pitch MIDI note (comments are written pitch)
FINGERINGS = {
    # Low register
    49: _ALL_SIX + ['LTable_Bb'],  # Bb3
    50: _ALL_SIX + ['LTable_B'],  # B3
    51: _ALL_SIX + ['RPinky_C'],  # C4
    52: _ALL_SIX + ['LTable_Cs'],  # C#4
    53: _ALL_SIX,  # D4
    54: _ALL_SIX + ['RPinky_Eb'],  # Eb4
    55: _LEFT + ['R1', 'R2'],  # E4
    56: _LEFT + ['R1'],  # F4
    57: _LEFT + ['R2'],  # F#4
    58: _LEFT,  # G4
    59: _LEFT + ['LTable_Gs'],  # G#4
    60: ['L1', 'L2'],  # A4
    61: ['L1', 'LBis'],  # Bb4
    62: ['L1'],  # B4
    63: ['L2'],  # C5
    64: [],  # C#5 (open; see C# alternates below)
    # Middle and high register (with octave key)
    65: ['LThumb_Oct'] + _ALL_SIX,  # D5
    66: ['LThumb_Oct'] + _ALL_SIX + ['RPinky_Eb'],  # Eb5
    67: ['LThumb_Oct'] + _LEFT + ['R1', 'R2'],  # E5
    68: ['LThumb_Oct'] + _LEFT + ['R1'],  # F5
    69: ['LThumb_Oct'] + _LEFT + ['R2'],  # F#5
    70: ['LThumb_Oct'] + _LEFT,  # G5
    71: ['LThumb_Oct'] + _LEFT + ['LTable_Gs'],  # G#5
    72: ['LThumb_Oct', 'L1', 'L2'],  # A5
    73: ['LThumb_Oct', 'L1', 'LBis'],  # Bb5
    74: ['LThumb_Oct', 'L1'],  # B5
    75: ['LThumb_Oct', 'L2'],  # C6
    76: ['LThumb_Oct'],  # C#6
    # Palm keys
    77: ['LThumb_Oct', 'LPalm_D'],  # D6
    78: ['LThumb_Oct', 'LPalm_D', 'LPalm_Eb'],  # Eb6
    79: ['LThumb_Oct', 'LPalm_D', 'LPalm_Eb', 'RSide_E'],  # E6
    80: ['LThumb_Oct', 'LPalm_D', 'LPalm_Eb', 'LPalm_F', 'RSide_E'],  # F6
}

# Middle C# (written C#5) alternates, picked by context in assign_fingerings()
MIDDLE_C_SHARP = 64
MIDDLE_D = 65
C_SHARP_LONG = ['LThumb_Oct'] + _ALL_SIX + ['LTable_Cs']  # smooth to/from D: just lift the pinky
C_SHARP_VENTED = ['LThumb_Oct', 'L3']  # fuller tone and pitch on held notes
HELD_NOTE_BEATS = 0.9  # C# about a beat or longer is "held" (MIDI files often trim a few ticks)
ADJACENT_GAP_BEATS = 0.5  # max gap for a neighbouring D to count as a D <-> C# transition


def assign_fingerings(notes):
    """Set note['keys'], note['fingering'] (label for alternates) and note['optional'].
    Middle C# picks: long fingering next to a middle D, vented when held, otherwise open."""
    for i, note in enumerate(notes):
        note['keys'] = FINGERINGS.get(note['note'], [])
        note['fingering'] = None
        note['optional'] = False  # alternate fingering; open is also fine
        if note['note'] != MIDDLE_C_SHARP:
            continue
        prev = notes[i - 1] if i > 0 else None
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        near_d = ((prev and prev['note'] == MIDDLE_D
                   and note['start'] - prev['end'] <= ADJACENT_GAP_BEATS) or
                  (nxt and nxt['note'] == MIDDLE_D
                   and nxt['start'] - note['end'] <= ADJACENT_GAP_BEATS))
        if near_d:
            note['keys'], note['fingering'] = C_SHARP_LONG, 'long C♯ · or open'
            note['optional'] = True
        elif note['end'] - note['start'] >= HELD_NOTE_BEATS:
            note['keys'], note['fingering'] = C_SHARP_VENTED, 'vented C♯ · or open'
            note['optional'] = True
        else:
            note['fingering'] = 'open C♯ · lift all fingers'
