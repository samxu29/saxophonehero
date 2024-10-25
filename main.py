import pygame
import mido
import cv2
import numpy as np
from moviepy.editor import ImageSequenceClip
from collections import deque
import time

class SaxophoneKey:
    def __init__(self, name, position, size=10):
        self.name = name
        self.position = position  # (x, y) coordinates
        self.size = size
        self.pressed = False


class SaxophoneFingering:
    def __init__(self):
        # Keep your existing key definitions...
        self.keys = {
            # Octave key
            'Oct': SaxophoneKey('Oct', (60, 20), 5),
            
            # Left Palm keys
            'Eb_palm': SaxophoneKey('Eb', (90, 40), 5),
            'D_palm': SaxophoneKey('D', (80, 60), 5),  
            'F_palm': SaxophoneKey('F', (70, 80), 5),  
            
            # Left Main keys
            'Front_f': SaxophoneKey('Front F', (60, 100), 5),
            'L1': SaxophoneKey('L1', (60, 130), 10),
            'Bis': SaxophoneKey('Bis', (60, 160), 5),
            'L2': SaxophoneKey('L2', (60, 190), 10),
            'L3': SaxophoneKey('L3', (60, 250), 10),
            
            # Left Pinky keys
            'G#': SaxophoneKey('G#', (80, 280), 5),          
            'Low_C#': SaxophoneKey('_C#', (70, 300), 5),  
            'Low_B': SaxophoneKey('_B', (90, 320), 5),    
            'Low_Bb': SaxophoneKey('_Bb', (80, 340), 5),  
            
            # Right Side keys
            'E_side': SaxophoneKey('E', (20, 380), 5),    
            'C_side': SaxophoneKey('C', (20, 400), 5),    
            'Bb_side': SaxophoneKey('Bb', (20, 420), 5),
                   
            # Right Main keys
            'R1': SaxophoneKey('R1', (60, 470), 10),  
            'R2': SaxophoneKey('R2', (60, 510), 10),  
            'F#_side': SaxophoneKey('F#', (20, 560), 5),
            'R3': SaxophoneKey('R3', (60, 590), 10),              
            
            # Right Pinky keys
            'Low_Eb': SaxophoneKey('_Eb', (20, 620), 5),  
            'Low_C': SaxophoneKey('_C', (20, 640), 5),    
        }
        
        # Define fingering combinations for each note
        self.fingerings = {
            # Low register
            49: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_Bb'],  # A#/Bb
            50: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_B', 'C_side'],  # B
            51: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_C'],  # C
            52: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_C', 'C_side'],  # C#/Db
            53: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3'],  # D
            54: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_Eb'],  # D#/Eb
            55: ['L1', 'L2', 'L3', 'R1', 'R2'],  # E
            56: ['L1', 'L2', 'L3', 'R1'],  # FO
            57: ['L1', 'L2', 'L3', 'R2'],  # F#/Gb
            58: ['L1', 'L2', 'L3'],  # G
            59: ['L1', 'L2', 'L3', 'G#'],  # G#/Ab
            60: ['L1', 'L2'],  # A
            61: ['L1', 'Bis'],  # A#/Bb
            62: ['L1'],  # B
            63: ['L2'],  # C
            64: [],  # C#/Db
            # Middle and high register (with octave key)
            65: ['Oct', 'L1', 'L2', 'L3', 'R1', 'R2', 'R3'],  # D
            66: ['Oct', 'L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_Eb'],  # D#/Eb
            67: ['Oct', 'L1', 'L2', 'L3', 'R1', 'R2'],  # E
            68: ['Oct', 'L1', 'L2', 'L3', 'R1'],  # F
            69: ['Oct', 'L1', 'L2', 'L3', 'R2'],  # F#/Gb
            70: ['Oct', 'L1', 'L2', 'L3'],  # G
            71: ['Oct', 'L1', 'L2', 'L3', 'G#'],  # G#/Ab
            72: ['Oct', 'L1', 'L2'],  # A
            73: ['Oct', 'L1', 'Bis'],  # A#/Bb
            74: ['Oct', 'L1'],  # B
            75: ['Oct', 'L2'],  # C
            76: ['Oct'],  # C#/Db
            77: ['Oct', 'D_palm'],  # D
            78: ['Oct', 'D_palm', 'Eb_palm'],  # D#/Eb
            79: ['Oct', 'D_palm', 'Eb_palm', 'E_side'],  # E
            80: ['Oct', 'D_palm', 'Eb_palm', 'F_palm', 'E_side'],  # F
        }
        
        # Create individual lanes for each key
        self.key_lanes = {}
        for key_name, key in self.keys.items():
            self.key_lanes[key_name] = {
                'y': key.position[1] + 40, 
                # 'x': key.position[0],       
                'x': 20,
                'size': key.size,           
                'keys': [key_name]        
            }


    def draw_fingering_chart(self, surface, note_number):
        """Draw the complete fingering chart with pressed keys highlighted"""
        # Reset all keys
        for key in self.keys.values():
            key.pressed = False
        
        # Get the fingering for the current note
        fingering = self.fingerings.get(note_number, [])
        
        # Mark the required keys as pressed
        for key_name in fingering:
            if key_name in self.keys:
                self.keys[key_name].pressed = True
        
        # Draw all keys
        for key in self.keys.values():
            # Draw key circle
            if key.pressed:
                color = (255, 255, 255, 255)  # White with full opacity for pressed keys
                border_color = (255, 255, 255, 255)  # White border for pressed keys
            else:
                color = (255, 255, 255, 40)  # Transparent white for unpressed keys
                border_color = (255, 255, 255, 100)  # Semi-transparent white border
            
            # Draw border
            pygame.draw.circle(surface, border_color, key.position, key.size + 1)
            # Draw key
            pygame.draw.circle(surface, color, key.position, key.size)
        
        return surface

    def get_note_name(self, note_number):
        """Convert MIDI note number to note name"""
        notes = {
                      49: 'A#3', 50: 'B3', 51: 'C4', 52: 'C#4', 53: 'D4', 54: 'D#4', 55: 'E4', 56: 'F4', 57: 'F#4', 58: 'G4', 59: 'G#4', 
            60: 'A4', 61: 'A#4', 62: 'B4', 63: 'C5', 64: 'C#5', 65: 'D5', 66: 'D#5', 67: 'E5', 68: 'F5', 69: 'F#5', 70: 'G5', 71: 'G#5', 
            72: 'A5', 73: 'A#5', 74: 'B5', 75: 'C6', 76: 'C#6', 77: 'D6', 78: 'Eb6', 79: 'E6', 80: 'F6'
        }
        return notes.get(note_number, f"Note {note_number}")
    pass


class SaxophoneVisualizer:
    def __init__(self, midi_file, window_size=(1600, 900), scroll_speed=2):
        # Keep existing initialization code...
        self.tempo = 500000  # Default tempo (microseconds per beat)
        self.ticks_per_beat = None
        self.scroll_speed = scroll_speed
        self.pixels_per_beat = 60  # This defines how many pixels represent one beat
        
        # Window and display settings
        self.window_size = window_size
        self.note_height = 30
        self.active_notes = deque()
        self.midi_file = midi_file
        
        # Add missing attributes for lanes and visualization
        self.min_lane_height = 20
        
        # Your color scheme
        self.key_colors = {
            'Oct': (147, 51, 234),      # Purple
            'Eb_palm': (41, 121, 255),  # Blue
            'D_palm': (41, 121, 255),   # Blue
            'F_palm': (41, 121, 255),   # Blue
            'Front_f': (255, 136, 0),   # Orange
            'L1': (0, 200, 83),         # Green
            'L2': (0, 200, 83),         # Green
            'L3': (0, 200, 83),         # Green
            'Bis': (255, 214, 0),       # Yellow
            'G#': (255, 64, 129),       # Pink
            'Low_C#': (255, 64, 129),   # Pink
            'Low_B': (255, 64, 129),    # Pink
            'Low_Bb': (255, 64, 129),   # Pink
            'E_side': (244, 67, 54),    # Red
            'C_side': (244, 67, 54),    # Red
            'Bb_side': (244, 67, 54),   # Red
            'R1': (0, 188, 212),        # Cyan
            'R2': (0, 188, 212),        # Cyan
            'R3': (0, 188, 212),        # Cyan
            'F#_side': (0, 150, 136),   # Teal
            'Low_Eb': (255, 87, 34),    # Deep Orange
            'Low_C': (255, 87, 34),     # Deep Orange
        }
        
        # Rest of initialization...
        self.playline_color = (255, 255, 255)
        self.playline_x = 400
        self.chart_width = 200
        self.chart_x = 100
        self.note_start_x = self.playline_x
        
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Saxophone MIDI Visualizer")
        
        self.chart_surface = pygame.Surface((300, 900), pygame.SRCALPHA)
        self.fingering_system = SaxophoneFingering()
        self.current_note = None
        self.current_chart = None
        self.last_active_note = None
        
        self.midi_data = self.process_midi_file()
        self.adjust_key_positions()
        
    def process_midi_file(self):
        """Process MIDI file and calculate note lengths based on tempo"""
        midi = mido.MidiFile(self.midi_file)
        self.ticks_per_beat = midi.ticks_per_beat
        note_events = []
        
        # Initialize tempo (microseconds per beat)
        tempo = 500000  # Default: 120 BPM (60000000 / 500000 = 120)
        
        # Read tempo from MIDI if available
        for msg in midi.tracks[0]:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break
        
        # Calculate timing conversion factors
        microseconds_per_beat = tempo
        seconds_per_beat = microseconds_per_beat / 1000000
        beats_per_second = 1 / seconds_per_beat
        beats_per_minute = beats_per_second * 60
        
        print(f"Tempo: {beats_per_minute} BPM")
        print(f"Seconds per beat: {seconds_per_beat}")
        
        # Process notes
        current_time = 0
        initial_x = self.window_size[0] + 200
        
        for track in midi.tracks:
            absolute_time = 0
            for msg in track:
                absolute_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    note_start = absolute_time
                    # Find corresponding note_off event
                    note_end = None
                    next_time = absolute_time
                    for next_msg in track[track.index(msg) + 1:]:
                        next_time += next_msg.time
                        if (next_msg.type in ['note_off', 'note_on'] and 
                            next_msg.note == msg.note and 
                            (next_msg.type == 'note_off' or next_msg.velocity == 0)):
                            note_end = next_time
                            break
                    
                    if note_end is not None:
                        # Calculate note duration in beats
                        duration_ticks = note_end - note_start
                        duration_beats = duration_ticks / self.ticks_per_beat
                        
                        # Convert duration to pixels
                        note_length_pixels = duration_beats * self.pixels_per_beat
                        
                        note_events.append({
                            'time': note_start,
                            'note': msg.note,
                            'velocity': msg.velocity,
                            'x': initial_x + (note_start / self.ticks_per_beat * self.pixels_per_beat),
                            'length': note_length_pixels,
                            'duration_beats': duration_beats
                        })
                        
                        print(f"Note {msg.note}: duration = {duration_beats} beats, length = {note_length_pixels} pixels")
        
        note_events.sort(key=lambda x: x['time'])
        
        if note_events:
            max_time = max(event['time'] for event in note_events)
            self.total_duration = (max_time / self.ticks_per_beat) * self.pixels_per_beat / self.scroll_speed
        else:
            self.total_duration = 0
        
        return note_events

    def adjust_key_positions(self):
        """Adjust key positions to fit within the chart area"""
        for key in self.fingering_system.keys.values():
            # Keep original y position, adjust x position to be relative to chart_x
            new_x = key.position[0] + self.chart_x
            key.position = (new_x, key.position[1])

    def draw_fingering_chart(self, note_number):
        """Draw saxophone fingering chart for given note"""
        if self.current_note != note_number:
            self.chart_surface.fill((0, 0, 0, 0))  # Clear with transparency
            
            # Draw the diagram
            self.fingering_system.draw_fingering_chart(self.chart_surface, note_number)
            
            # Add note name above the chart
            font = pygame.font.Font(None, 36)  # Increased font size
            note_name = self.fingering_system.get_note_name(note_number)
            text = font.render(note_name, True, (255, 255, 255))
            text_rect = text.get_rect(centerx=150, y=800)  # Adjusted position
            self.chart_surface.blit(text, text_rect)
            
            self.current_note = note_number
            self.current_chart = self.chart_surface.copy()
        
        # Draw chart at the specified position
        self.screen.blit(self.current_chart, (0, 40))
        
    def draw_note(self, note):
            """Draw note blocks in individual lanes with correct lengths"""
            fingering = self.fingering_system.fingerings.get(note['note'], [])
            note_end_x = note['x'] + note['length']
            
            # Only draw if note is at least partially visible
            if note_end_x > 0:  # Changed from self.playline_x - 10
                for key_name in fingering:
                    if key_name in self.fingering_system.key_lanes:
                        lane_info = self.fingering_system.key_lanes[key_name]
                        color = self.key_colors.get(key_name, (150, 150, 150))
                        
                        # Calculate note dimensions
                        lane_height = max(self.min_lane_height, lane_info['size'] * 2.5)
                        note_height = lane_height * 0.8
                        y_pos = lane_info['y'] - note_height/2
                        
                        # Calculate correct x positions
                        x_start = max(note['x'], 0)  # Don't start before left edge
                        note_width = min(note_end_x, self.window_size[0]) - x_start  # Don't extend past right edge
                        
                        if note_width > 0:
                            note_rect = pygame.Rect(x_start, y_pos, note_width, note_height)
                            radius = min(note_height / 2, 10)
                            
                            # Draw note with better visibility
                            pygame.draw.rect(self.screen, color, note_rect, border_radius=int(radius))
                            
                            # Highlight note if it's at the playline
                            if self.playline_x - 2 <= note['x'] <= self.playline_x + 2:
                                pygame.draw.rect(self.screen, (255, 255, 255), note_rect,
                                            width=2, border_radius=int(radius))    
    
    def draw_lanes(self):
        """Draw individual lanes for each key with transparency"""
        # Draw background for lanes area with high transparency
        lane_area_rect = pygame.Rect(self.note_start_x, 0, 
                                   self.window_size[0] - self.note_start_x, 
                                   self.window_size[1])
        pygame.draw.rect(self.screen, (20, 20, 20, 30), lane_area_rect)
        
        # Draw separator line between chart and lanes
        pygame.draw.line(self.screen, (100, 100, 100),
                        (self.playline_x - 10, 0),
                        (self.playline_x - 10, self.window_size[1]), 1)
        
        for key_name, lane_info in self.fingering_system.key_lanes.items():
            lane_height = max(self.min_lane_height, lane_info['size'] * 2)
            
            # Draw lane background
            lane_rect = pygame.Rect(self.note_start_x, 
                                  lane_info['y'] - lane_height//2,
                                  self.window_size[0] - self.note_start_x,
                                  lane_height)
            pygame.draw.rect(self.screen, (30, 30, 30, 30), lane_rect)
            
            # Draw key name
            font = pygame.font.Font(None, 16)
            text = font.render(key_name.replace('_', ' '), True, (150, 150, 150))
            text_rect = text.get_rect(
                right=self.note_start_x - 5,
                centery=lane_info['y']
            )
            self.screen.blit(text, text_rect)
    
    def draw_playline(self):
        """Draw the vertical playline"""
        pygame.draw.line(self.screen, self.playline_color,
                        (self.playline_x, 0),
                        (self.playline_x, self.window_size[1]), 2)
    
    def run(self):
        """Modified run function with improved timing"""
        current_time = 0
        clock = pygame.time.Clock()
        event_index = 0
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self.screen.fill((0, 0, 0))
            self.draw_lanes()
            self.draw_playline()
            
            # Process new notes
            while (event_index < len(self.midi_data) and 
                   self.midi_data[event_index]['time'] <= current_time * self.ticks_per_beat):
                note_data = {
                    'note': self.midi_data[event_index]['note'],
                    'x': self.window_size[0],
                    'length': self.midi_data[event_index]['length'],
                    'start_time': current_time
                }
                self.active_notes.append(note_data)
                event_index += 1
            
            # Update and draw active notes
            notes_to_remove = []
            for note in self.active_notes:
                note['x'] -= self.scroll_speed
                self.draw_note(note)
                
                # Check if note is at playline
                if self.playline_x - 2 <= note['x'] <= self.playline_x + 2:
                    self.draw_fingering_chart(note['note'])
                    self.last_active_note = note
                
                # Remove notes that have passed
                if note['x'] + note['length'] < 0:
                    notes_to_remove.append(note)
            
            # Remove passed notes
            for note in notes_to_remove:
                self.active_notes.remove(note)
            
            pygame.display.flip()
            clock.tick(60)
            current_time += 1/60
            
            # Check if complete
            if event_index >= len(self.midi_data) and not self.active_notes:
                running = False
        
        pygame.quit()
    
    def cleanup(self):
        """Clean up resources"""
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
    midi_file = "test.mid"
    try:
        visualizer = SaxophoneVisualizer(midi_file, scroll_speed=2)
        visualizer.run()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()