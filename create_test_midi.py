from midiutil import MIDIFile
import os

def create_test_midi():
    # Create a MIDI file with 1 track
    midi = MIDIFile(1)
    
    # Setup the track
    track = 0
    time = 0
    channel = 0
    tempo = 120  # BPM
    volume = 100  # 0-127
    
    # Add track name and tempo
    midi.addTempo(track, time, tempo)

    # 49    A#3/Bb3      L1, L2, L3, R1, R2, R3, Low_Bb
    # 50    B3           L1, L2, L3, R1, R2, R3, Low_B, C_side
    # 51    C4           L1, L2, L3, R1, R2, R3, Low_C
    # 52    C#4/Db4      L1, L2, L3, R1, R2, R3, Low_C, C_side
    # 53    D3           L1, L2, L3, R1, R2, R3
    # 54    D#4/Eb4      L1, L2, L3, R1, R2, R3, Low_Eb
    # 55    E4           L1, L2, L3, R1, R2
    # 56    F4           L1, L2, L3, R1
    # 57    F#4/Gb4      L1, L2, L3, R2  
    # 58    G4           L1, L2, L3
    # 59    G#4/Ab4      L1, L2, L3, G#
    # 60    A4           L1, L2
    # 61    A#4/Bb4      L1, Bis
    # 62    B4           L1,
    # 63    C5           L2,
    # 64    C#5/Db5      -
    # 65    D5           Oct, L1, L2, L3, R1, R2, R3
    # 66    D#5/Eb5      Oct, L1, L2, L3, R1, R2, R3, Low_Eb
    # 67    E5           Oct, L1, L2, L3, R1, R2
    # 68    F5           Oct, L1, L2, L3, R1
    # 69    F#5/Gb5      Oct, L1, L2, L3, R2
    # 70    G5           Oct, L1, L2, L3
    # 71    G#5/Ab5      Oct, L1, L2, L3, G#
    # 72    A5           Oct, L1, L2
    # 73    A#5/Bb5      Oct, L1, Bis
    # 74    B5           Oct, L1
    # 75    C6           Oct, L2
    # 76    C#6/Db6      Oct
    # 77    D6           Oct, D_palm
    # 78    D#6/Eb6      Oct, D_palm, Eb_palm
    # 79    E6           Oct, D_palm, Eb_palm, E_side
    # 80    F6           Oct, D_palm, Eb_palm, F_palm, E_side
    
    
    notes = [
        # Note, duration (in beats), Concert pitch -> Eb Transposed (Alto/Baritone)
        (49, 4),  # C#3/Db3 -> A#3/Bb3
        (50, 4),  # D3 -> B3
        (51, 4),  # D#3/Eb3 -> C4
        (52, 4),  # E3 -> C#4
        (53, 4),  # F3 -> D4
        (54, 4),  # F#3 -> D#4/Eb4
        (55, 4),  # G3 -> E4
        (56, 4),  # G#3/Ab3 -> F4
        (57, 4),  # A3 -> F#4/Gb4
        (58, 4),  # A#3/Bb3 -> G4
        (59, 4),  # B3 -> G#4/Ab4
        (60, 4),  # C4 -> A4
        (61, 4),  # C#4/Db4 -> A#4/Bb4
        (62, 4),  # D4 -> B4
        (63, 4),  # D#4/Eb4 -> C5
        (64, 4),  # E4 -> C#5
        (65, 4),  # F4 -> D5
        (66, 4),  # F#4 -> D#5/Eb5
        (67, 4),  # G4 -> E5
        (68, 4),  # G#4/Ab4 -> F5
        (69, 4),  # A4 -> F#5/Gb5
        (70, 4),  # A#4/Bb4 -> G5
        (71, 4),  # B4 -> G#5/Ab5
        (72, 4),  # C5 -> A5
        (73, 4),  # C#5/Db5 -> A#5/Bb5
        (74, 4),  # D5 -> B5
        (75, 4),  # D#5/Eb5 -> C6
        (76, 4),  # E5 -> C#6
        (77, 4),  # F5 -> D6
        (78, 4),  # F#5 -> D#6/Eb6
        (79, 4),  # G5 -> E6
        (80, 4),  # G#5/Ab5 -> F6
    ]
    
    # Add notes to the track
    for note, duration in notes:
        midi.addNote(track, channel, note, time, duration, volume)
        time += duration
    
    # Save the MIDI file
    filename = "test.mid"
    with open(filename, "wb") as file:
        midi.writeFile(file)
    
    print(f"MIDI file created: {os.path.abspath(filename)}")
    return filename

if __name__ == "__main__":
    create_test_midi()