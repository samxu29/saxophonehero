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
            'Eb_palm': SaxophoneKey('Eb', (80, 40), 5),
            'D_palm': SaxophoneKey('D', (90, 60), 5),  
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

        self.fingerings = {
            # Low register
            49: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_Bb'],  # A#/Bb
            50: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_B', 'C_side'],  # B
            51: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_C'],  # C
            52: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_C', 'C_side'],  # C#/Db
            53: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3'],  # D
            54: ['L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'Low_Eb'],  # D#/Eb
            55: ['L1', 'L2', 'L3', 'R1', 'R2'],  # E
            56: ['L1', 'L2', 'L3', 'R1'],  # F
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

class SaxophoneVisualizer:
    def __init__(self, midi_file, window_size=(1600, 900), scroll_speed=2):  # Increased from 1024x768 to 1600x900
        self.window_size = window_size
        self.scroll_speed = scroll_speed
        self.note_height = 30
        self.active_notes = deque()
        self.midi_file = midi_file
        
        # Adjust positions to ensure chart is visible
        self.playline_x = self.window_size[0] // 4  # Moved playline position relative to larger window
        self.chart_width = 200  # Increased chart width
        self.chart_x = 100  # More space from left edge
        self.note_start_x = self.playline_x
        
        # Define saxophone note ranges (standard alto saxophone range)
        self.min_note = 49  # Db3
        self.max_note = 80  # Ab5
        
        # Initialize colors
        self.bg_color = (0, 0, 0)
        self.playline_color = (255, 255, 255)
        self.note_colors = {
            'C': (255, 0, 0),    # Red
            'D': (255, 127, 0),  # Orange
            'E': (255, 255, 0),  # Yellow
            'F': (0, 255, 0),    # Green
            'G': (0, 0, 255),    # Blue
            'A': (75, 0, 130),   # Indigo
            'B': (148, 0, 211)   # Violet
        }
        
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Set up the display
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Saxophone MIDI Visualizer")
        
        # Create surfaces with alpha channel for transparency
        self.chart_surface = pygame.Surface((300, 900), pygame.SRCALPHA)  # Increased surface size
        self.chart_surface.fill((0, 0, 0, 0))
        
        # Initialize the fingering system
        self.fingering_system = SaxophoneFingering()
        
        # Add cache for current note and chart
        self.current_note = None
        self.current_chart = None
        
        # Initialize minimum lane height and spacing
        self.min_lane_height = 30  
        self.lane_spacing = 5    
        
        # Initialize video writer
        self.frames = []
        
        # Load and process MIDI file
        self.midi_data = self.process_midi_file()
        
        # Adjust the x-positions of all keys to be relative to chart_x
        self.adjust_key_positions()
        
        self.last_active_note = None

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

    def draw_note(self, note, is_active=False):
        """Draw note blocks in individual lanes with gaps and rounded corners"""
        fingering = self.fingering_system.fingerings.get(note['note'], [])
        color = self.get_note_color(note['note'])
        
        # Only draw notes before or at the playline
        if note['x'] <= self.playline_x:
            return
        
        # Draw note blocks for each required key
        for key_name in fingering:
            if key_name in self.fingering_system.key_lanes:
                lane_info = self.fingering_system.key_lanes[key_name]
                
                # Reduce height to create gaps
                lane_height = max(self.min_lane_height, lane_info['size'] * 2)
                note_height = lane_height * 0.7  # Reduce to 70% of lane height
                
                # Calculate vertical position to center in lane
                y_pos = lane_info['y'] - note_height/2
                
                # Draw note block with rounded corners
                note_width = 60  # Reduced width
                note_rect = pygame.Rect(note['x'], y_pos, note_width, note_height)
                radius = min(note_height / 2, 8)  # Radius for rounded corners, max 8 pixels
                
                pygame.draw.rect(self.screen, color, note_rect, border_radius=int(radius))
                
                # Draw hit effect when note reaches playline
                if self.playline_x - 30 <= note['x'] <= self.playline_x + 30:
                    hit_rect = pygame.Rect(note['x'], y_pos, note_width, note_height)
                    pygame.draw.rect(self.screen, (255, 255, 255), hit_rect,
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
            # Calculate lane height based on key size
            lane_height = max(self.min_lane_height, lane_info['size'] * 2)
            
            # Draw lane background
            lane_rect = pygame.Rect(self.note_start_x, 
                                  lane_info['y'] - lane_height//2,
                                  self.window_size[0] - self.note_start_x,
                                  lane_height)
            pygame.draw.rect(self.screen, (30, 30, 30, 30), lane_rect)
            
            # Draw key name aligned with the lane
            font = pygame.font.Font(None, 16)
            text = font.render(key_name.replace('_', ' '), True, (150, 150, 150))
            text_rect = text.get_rect(
                right=self.note_start_x - 5,
                centery=lane_info['y']
            )
            self.screen.blit(text, text_rect)


    def process_midi_file(self):
        """Process MIDI file and convert to timed note events"""
        midi = mido.MidiFile(self.midi_file)
        note_events = []
        current_time = 0
        
        for msg in midi.play():
            current_time += msg.time
            
            if hasattr(msg, 'note'):  # Check if message has note attribute
                if msg.type == 'note_on' and msg.velocity > 0:
                    note_events.append({
                        'time': current_time,
                        'note': msg.note,
                        'type': 'on',
                        'velocity': msg.velocity,
                        'x': self.window_size[0]
                    })
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    note_events.append({
                        'time': current_time,
                        'note': msg.note,
                        'type': 'off',
                        'velocity': 0
                    })
        
        # Store total duration for playback
        self.total_duration = current_time
        return note_events
    
    def note_to_lanes(self, note_number):
        """Convert MIDI note to required fingering lanes"""
        fingering = self.fingering_system.fingerings.get(note_number, [])
        active_lanes = []
        
        # Map each key in the fingering to its corresponding lane
        for key in fingering:
            for lane_name, lane_info in self.fingering_system.key_lanes.items():
                if key in lane_info['keys']:
                    active_lanes.append({
                        'y': lane_info['y'],
                        'name': lane_name,
                        'key': key
                    })
        
        return active_lanes

    def note_to_y_position(self, note_number):
        """Convert MIDI note number to y-position on screen"""
        total_range = self.max_note - self.min_note
        position = (note_number - self.min_note) / total_range
        return int(position * (self.window_size[1] - self.note_height))

    def get_note_color(self, note_number):
        """Get color based on note name"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_name = note_names[note_number % 12]
        base_note = note_name.replace('#', '')
        return self.note_colors[base_note]

    def draw_playline(self):
        """Draw the vertical playline"""
        # Draw main line
        pygame.draw.line(self.screen, self.playline_color,
                        (self.playline_x, 0),
                        (self.playline_x, self.window_size[1]), 2)


    def run(self):
        """Run the visualizer"""
        current_time = 0
        clock = pygame.time.Clock()
        event_index = 0
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Draw lanes
            self.draw_lanes()
            
            # Process notes
            while (event_index < len(self.midi_data) and 
                self.midi_data[event_index]['time'] <= current_time):
                event = self.midi_data[event_index]
                
                if event['type'] == 'on':
                    self.active_notes.append({
                        'note': event['note'],
                        'x': self.window_size[0]
                    })
                
                event_index += 1
            
            # Update and draw notes
            notes_to_remove = []
            current_active_note = None
            
            for note in self.active_notes:
                note['x'] -= self.scroll_speed
                
                # Remove notes as soon as they hit the playline
                if note['x'] <= self.playline_x:
                    notes_to_remove.append(note)
                    current_active_note = note  # Set as active note before removing
                else:
                    self.draw_note(note)
            
            # Update last_active_note if there's a new active note
            if current_active_note:
                self.last_active_note = current_active_note
            
            # Draw fingering chart using last active note
            if self.last_active_note:
                self.draw_fingering_chart(self.last_active_note['note'])
            
            # # Draw playline last so it's always visible
            # self.draw_playline()
            
            # Remove notes that hit the playline
            for note in notes_to_remove:
                self.active_notes.remove(note)
            
            pygame.display.flip()
            clock.tick(60)
            current_time += 1/60
            
            # Keep running until all notes are processed and have moved off screen
            if event_index >= len(self.midi_data) and not self.active_notes:
                running = False
                
            # Add safety timeout
            if current_time > self.total_duration + 30:
                running = False

    def save_video(self, filename, fps=60):
        """Save recorded frames as video"""
        if self.frames:
            print(f"\nSaving video to {filename}...")
            clip = ImageSequenceClip(self.frames, fps=fps)
            clip.write_videofile(filename)
            print("Video saved successfully!")
        else:
            print("No frames captured. Video not saved.")

    def cleanup(self):
        """Clean up resources"""
        pygame.quit()

def main():
    midi_file = "test.mid"  # Replace with your MIDI file path
    try:
        visualizer = SaxophoneVisualizer(midi_file)
        visualizer.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        visualizer.cleanup()

if __name__ == "__main__":
    main()