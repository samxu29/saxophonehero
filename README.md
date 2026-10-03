# saxophonehero

short for saxhero
a app suppose to convert midi into alto saxophone scrolling fingering chart
Run with `.venv/bin/python main.py path/to/song.mid`.

For multitrack MIDI files:

- Click **Sax track** above the chart to open a menu of tracks and instruments, then click a track to display it as saxophone. **T** also opens the menu.
- The app initially selects a track marked with a MIDI saxophone instrument, or the first pitched track otherwise.
- Each track has a **Mute / Unmute** button in the menu, including the selected sax track. Muting silences audio while keeping the fingering chart visible. Mute choices stay in effect when switching tracks.
- All other note tracks play as accompaniment. **B** toggles accompaniment on/off.
- The selected track and backing status appear above the chart. Pause, seek, and speed controls apply to all parts.

Backing uses distinct synthesized piano, guitar, bass, strings, and percussion voices (drums on MIDI channel 10). These are approximate sounds, not a full General MIDI instrument library. Selection works by MIDI track; files containing several instruments in one track need to be split into tracks first. Playback currently uses the first tempo in the file rather than following tempo changes.

Press **H** or **Home** to return to the beginning, including the count-in.
