import pygame
import math
from abc import ABC, abstractmethod

class Transform:
    """Component that handles position and rotation"""
    def __init__(self, x=0, y=0, rotation=0):
        self.x = x
        self.y = y
        self.rotation = rotation
    
    def set_position(self, x, y):
        """Set the position"""
        self.x = x
        self.y = y
    
    def get_position(self):
        """Get the position as a tuple"""
        return (self.x, self.y)
    
    def set_rotation(self, rotation):
        """Set the rotation, keeping it within 0-360 degrees"""
        self.rotation = rotation % 360
    
    def rotate(self, delta_rotation):
        """Add to the current rotation"""
        self.rotation = (self.rotation + delta_rotation) % 360

class Physics:
    """Component that handles velocity and physics calculations"""
    def __init__(self, velocity_x=0, velocity_y=0, max_velocity=15, min_velocity=-15):
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.max_velocity = max_velocity
        self.min_velocity = min_velocity
        
        # Store previous position for collision rollback
        self.prev_x = 0
        self.prev_y = 0
    
    def set_velocity(self, velocity_x, velocity_y):
        """Set the velocity components"""
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
    
    def add_velocity(self, delta_x, delta_y):
        """Add to the current velocity"""
        self.velocity_x += delta_x
        self.velocity_y += delta_y
    
    def apply_gravity(self, gravity):
        """Apply gravity to the velocity"""
        self.velocity_y += gravity
    
    def clamp_velocity(self):
        """Clamp velocity to min/max bounds"""
        self.velocity_x = max(self.min_velocity, min(self.max_velocity, self.velocity_x))
        self.velocity_y = max(self.min_velocity, min(self.max_velocity, self.velocity_y))
    
    def store_previous_position(self, x, y):
        """Store the previous position for collision rollback"""
        self.prev_x = x
        self.prev_y = y
    
    def get_previous_position(self):
        """Get the previous position"""
        return (self.prev_x, self.prev_y)

class Renderer:
    """Component that handles image rendering and rotation"""
    def __init__(self, image_path=None):
        self.original_image = None
        self.current_image = None
        self.rect = None
        
        if image_path:
            self.load_image(image_path)
    
    def load_image(self, image_path):
        """Load an image from file"""
        self.original_image = pygame.image.load(image_path)
        self.current_image = self.original_image.copy()
        self.rect = self.current_image.get_rect()
    
    def update_rotation(self, rotation):
        """Update the rendered image based on rotation"""
        if self.original_image:
            # Rotate the image (negative rotation for pygame coordinate system)
            self.current_image = pygame.transform.rotate(self.original_image, -rotation)
            # Update rect but preserve center position
            old_center = self.rect.center if self.rect else (0, 0)
            self.rect = self.current_image.get_rect()
            self.rect.center = old_center
    
    def update_position(self, x, y):
        """Update the renderer position"""
        if self.rect and self.original_image:
            # Center the rotated image on the entity position
            self.rect.centerx = x + self.original_image.get_width() // 2
            self.rect.centery = y + self.original_image.get_height() // 2
    
    def get_image(self):
        """Get the current rendered image"""
        return self.current_image
    
    def get_rect(self):
        """Get the current rect"""
        return self.rect
    
    def get_original_size(self):
        """Get the original image size"""
        if self.original_image:
            return self.original_image.get_size()
        return (0, 0)

class Entity(ABC):
    """Base class for all game entities"""
    def __init__(self, x=0, y=0, rotation=0, image_path=None):
        self.transform = Transform(x, y, rotation)
        self.physics = Physics()
        self.renderer = Renderer(image_path)
        
        # Initialize renderer position
        self.renderer.update_position(x, y)
        self.renderer.update_rotation(rotation)
    
    def get_position(self):
        """Get the entity position"""
        return self.transform.get_position()
    
    def set_position(self, x, y):
        """Set the entity position"""
        self.transform.set_position(x, y)
        self.renderer.update_position(x, y)
    
    def get_rotation(self):
        """Get the entity rotation"""
        return self.transform.rotation
    
    def set_rotation(self, rotation):
        """Set the entity rotation"""
        self.transform.set_rotation(rotation)
        self.renderer.update_rotation(self.transform.rotation)
    
    def get_velocity(self):
        """Get the entity velocity"""
        return (self.physics.velocity_x, self.physics.velocity_y)
    
    def set_velocity(self, velocity_x, velocity_y):
        """Set the entity velocity"""
        self.physics.set_velocity(velocity_x, velocity_y)
    
    def update_physics(self, delta_time=1.0):
        """Update entity physics (position based on velocity)"""
        # Store previous position for collision rollback
        self.physics.store_previous_position(self.transform.x, self.transform.y)
        
        # Update position based on velocity
        self.transform.x += self.physics.velocity_x * delta_time
        self.transform.y += self.physics.velocity_y * delta_time
        
        # Update renderer position
        self.renderer.update_position(self.transform.x, self.transform.y)
    
    def rollback_position(self):
        """Rollback to previous position (for collision handling)"""
        prev_x, prev_y = self.physics.get_previous_position()
        self.set_position(prev_x, prev_y)
    
    def render(self, screen):
        """Render the entity to the screen"""
        if self.renderer.get_image() and self.renderer.get_rect():
            screen.blit(self.renderer.get_image(), self.renderer.get_rect())
    
    @abstractmethod
    def update(self, delta_time=1.0):
        """Update the entity (to be implemented by subclasses)"""
        pass