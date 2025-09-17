import pygame
from entity import Entity

class GhostFrame:
    """Represents a single frame of ghost data"""
    def __init__(self, timestamp, x, y, rotation):
        self.timestamp = timestamp
        self.x = x
        self.y = y
        self.rotation = rotation

class GhostRecorder:
    """Handles recording spaceship state data for ghost playback"""
    
    def __init__(self):
        self.frames = []
        self.recording = False
        self.start_time = 0
    
    def start_recording(self):
        """Start recording ghost data"""
        self.frames = []
        self.recording = True
        self.start_time = pygame.time.get_ticks()
    
    def stop_recording(self):
        """Stop recording ghost data"""
        self.recording = False
    
    def record_frame(self, spaceship):
        """Record a frame of spaceship data"""
        if not self.recording or not spaceship:
            return
        
        current_time = pygame.time.get_ticks()
        timestamp = current_time - self.start_time
        
        # Get spaceship position and rotation
        x, y = spaceship.get_position()
        rotation = spaceship.get_rotation()
        
        # Create and store frame data
        frame = GhostFrame(timestamp, x, y, rotation)
        self.frames.append(frame)
    
    def get_recorded_data(self):
        """Get the recorded frame data"""
        return self.frames.copy()
    
    def export_recording(self):
        """Export recorded data as a list of dictionaries for saving"""
        return [
            {
                'timestamp': frame.timestamp,
                'x': int(frame.x),
                'y': int(frame.y),
                'rotation': int(frame.rotation)
            }
            for frame in self.frames
        ]
    
    def import_recording(self, recording_data):
        """Import recording data from a list of dictionaries"""
        self.frames = []
        for frame_dict in recording_data:
            frame = GhostFrame(
                frame_dict['timestamp'],
                frame_dict['x'],
                frame_dict['y'],
                frame_dict['rotation']
            )
            self.frames.append(frame)
    
    def is_recording(self):
        """Check if currently recording"""
        return self.recording
    
    def clear_recording(self):
        """Clear recorded data"""
        self.frames = []
        self.recording = False

    def export_playback_data(self):
        """Export current playback data as a list of dictionaries"""
        return [
            {
                'timestamp': frame.timestamp,
                'x': int(frame.x),
                'y': int(frame.y),
                'rotation': frame.rotation
            }
            for frame in self.frames
        ]

class GhostPlayback:
    """Handles playing back recorded ghost data"""
    
    def __init__(self):
        self.frames = []
        self.playing = False
        self.start_time = 0
        self.current_frame_index = 0
    
    def start_playback(self):
        """Start playback with recorded data"""
        self.playing = True
        self.start_time = pygame.time.get_ticks()
        self.current_frame_index = 0
    
    def stop_playback(self):
        """Stop playback"""
        self.playing = False
        self.current_frame_index = 0
    
    def get_current_ghost_state(self):
        """Get the current ghost state based on playback time"""
        if not self.playing or not self.frames:
            return None
        
        current_time = pygame.time.get_ticks()
        playback_time = current_time - self.start_time
        
        # Find the appropriate frame for current time
        target_frame = None
        for frame in self.frames[self.current_frame_index:]:
            if frame.timestamp <= playback_time:
                target_frame = frame
                self.current_frame_index = self.frames.index(frame)
            else:
                break
        
        return target_frame

    
    def load_playback_data(self, recording_data):
        """Load playback data from a list of dictionaries"""
        self.frames = []
        for frame_dict in recording_data:
            frame = GhostFrame(
                frame_dict['timestamp'],
                frame_dict['x'],
                frame_dict['y'],
                frame_dict['rotation']
            )
            self.frames.append(frame)
    
    def is_playing(self):
        """Check if currently playing back"""
        return self.playing


class Ghost(Entity):
    """Ghost entity that represents the recorded spaceship path"""
    
    def __init__(self, image_path="spaceship.png"):
        super().__init__(0, 0, 0, image_path)
        self.visible = False
        self.alpha = 128  # 50% transparency
        
        # Create a semi-transparent version of the spaceship image
        if self.renderer.original_image:
            self._create_transparent_image()
    
    def _create_transparent_image(self):
        """Create a semi-transparent version of the spaceship image"""
        # Create a copy of the original image with alpha channel
        transparent_image = self.renderer.original_image.copy().convert_alpha()
        
        # Apply transparency to the entire image
        for x in range(transparent_image.get_width()):
            for y in range(transparent_image.get_height()):
                pixel = transparent_image.get_at((x, y))
                if pixel[3] > 0:  # If pixel is not fully transparent
                    # Set alpha to our desired transparency level
                    transparent_image.set_at((x, y), (pixel[0], pixel[1], pixel[2], self.alpha))
        
        # Update the renderer with the transparent image
        self.renderer.original_image = transparent_image
        self.renderer.current_image = transparent_image.copy()
    
    def update_from_ghost_frame(self, ghost_frame):
        """Update ghost position and rotation from a ghost frame"""
        if ghost_frame:
            self.set_position(ghost_frame.x, ghost_frame.y)
            self.set_rotation(ghost_frame.rotation)
            self.visible = True
        else:
            self.visible = False
    
    def update(self, delta_time=1.0):
        """Update the ghost entity (no physics needed)"""
        # Ghost doesn't need physics updates, it just follows recorded data
        pass
    
    def is_visible(self):
        """Check if ghost should be rendered"""
        return self.visible
    
    def set_visible(self, visible):
        """Set ghost visibility"""
        self.visible = visible