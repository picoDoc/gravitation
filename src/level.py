import pygame
import os

class Level:
    """
    Level class for managing image-based collision detection.
    Uses color-coded pixels to determine collision types:
    - Black (0,0,0): Solid asteroids - collision
    - White (255,255,255): Free space - no collision
    - Green (0,255,0): Goal areas (future use)
    - Red (255,0,0): Hazard zones (future use)
    - Blue (0,0,255): Special areas (future use)
    """
    
    def __init__(self, image_path):
        """
        Initialize level with collision map from image file.
        
        Args:
            image_path (str): Path to the level image file
        """
        self.image_path = image_path
        self.collision_surface = None
        self.visual_surface = None
        self.width = 0
        self.height = 0
        
        # Color definitions for collision types
        self.COLLISION_COLORS = {
            'SOLID': (0, 0, 0),      # Black - asteroids
            'FREE': (255, 255, 255), # White - free space
            'GOAL': (0, 255, 0),     # Green - goal areas
            'HAZARD': (255, 0, 0),   # Red - hazard zones
            'SPECIAL': (0, 0, 255)   # Blue - special areas
        }
        
        # Collision masks for fast collision detection
        self.solid_mask = None
        self.special_mask = None
        self.hazard_mask = None
        
        self.load_level()
    
    def load_level(self):
        """Load and prepare the level image for collision detection."""
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Level image not found: {self.image_path}")
        
        try:
            # Load the image
            loaded_image = pygame.image.load(self.image_path)
            
            # Convert to a format suitable for fast pixel access
            self.collision_surface = loaded_image.convert()
            
            # Create a visual copy for rendering (could be enhanced later)
            self.visual_surface = self.collision_surface.copy()
            
            # Store dimensions
            self.width = self.collision_surface.get_width()
            self.height = self.collision_surface.get_height()
            
            # Create collision masks for fast collision detection
            self._create_collision_masks()
            
        except pygame.error as e:
            raise RuntimeError(f"Failed to load level image {self.image_path}: {e}")
    
    def _create_collision_masks(self):
        """Create pygame masks for each collision type using fast threshold operations."""
        # Use pygame.mask.from_threshold for much faster mask creation
        # This directly creates a mask from pixels matching a specific color
        
        # Create solid collision mask (black pixels)
        self.solid_mask = pygame.mask.from_threshold(
            self.collision_surface,
            self.COLLISION_COLORS['SOLID'],  # Color to match
            (1, 1, 1, 255)  # Threshold - allow exact match only
        )
        
        # Create special collision mask (blue pixels)
        self.special_mask = pygame.mask.from_threshold(
            self.collision_surface,
            self.COLLISION_COLORS['SPECIAL'],  # Color to match
            (1, 1, 1, 255)  # Threshold - allow exact match only
        )
        
        # Create hazard collision mask (red pixels)
        self.hazard_mask = pygame.mask.from_threshold(
            self.collision_surface,
            self.COLLISION_COLORS['HAZARD'],  # Color to match
            (1, 1, 1, 255)  # Threshold - allow exact match only
        )
    
    def check_collision_at_point(self, x, y):
        """
        Check collision type at a specific point.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            str: Collision type ('SOLID', 'FREE', 'GOAL', 'HAZARD', 'SPECIAL', 'UNKNOWN')
        """
        # Bounds checking
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return 'SOLID'  # Treat out-of-bounds as solid collision
        
        # Get pixel color at the specified point
        try:
            pixel_color = self.collision_surface.get_at((int(x), int(y)))[:3]  # Get RGB, ignore alpha
            
            # Match color to collision type
            for collision_type, color in self.COLLISION_COLORS.items():
                if pixel_color == color:
                    return collision_type
            
            # If no exact match, return UNKNOWN (treat as solid for safety)
            return 'SOLID'
            
        except Exception:
            # If any error occurs, treat as solid collision
            return 'SOLID'
    
    
    def is_solid_collision(self, x, y):
        """
        Quick check if a point has solid collision.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if solid collision, False otherwise
        """
        collision_type = self.check_collision_at_point(x, y)
        return collision_type == 'SOLID'
    
    
    def is_special_collision(self, x, y):
        """
        Quick check if a point has special collision (target zone).
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if special collision, False otherwise
        """
        collision_type = self.check_collision_at_point(x, y)
        return collision_type == 'SPECIAL'
    
    
    def check_spaceship_collisions(self, spaceship_surface, spaceship_x, spaceship_y):
        """
        Check for collision between spaceship and level using pygame masks for fast detection.
        This is much faster than pixel-by-pixel checking.
        
        Args:
            spaceship_surface (pygame.Surface): The rotated spaceship surface
            spaceship_x (int): X position of spaceship (top-left corner)
            spaceship_y (int): Y position of spaceship (top-left corner)
            
        Returns:
            tuple: (solid_collision, special_collision, hazard_collision) - all bool values
        """
        # Create mask from spaceship surface (this is cached internally by pygame when possible)
        spaceship_mask = pygame.mask.from_surface(spaceship_surface)
        
        # Calculate offset for mask overlap checking
        # Offset is the position of the spaceship relative to the level
        offset = (int(spaceship_x), int(spaceship_y))
        
        # Check for collisions using fast mask overlap
        solid_collision = self.solid_mask.overlap(spaceship_mask, offset) is not None
        special_collision = self.special_mask.overlap(spaceship_mask, offset) is not None
        hazard_collision = self.hazard_mask.overlap(spaceship_mask, offset) is not None
        
        return solid_collision, special_collision, hazard_collision

    def get_visual_surface(self):
        """
        Get the surface for rendering the level.
        
        Returns:
            pygame.Surface: Surface to blit to screen
        """
        return self.visual_surface
    
    def get_dimensions(self):
        """
        Get level dimensions.
        
        Returns:
            tuple: (width, height)
        """
        return (self.width, self.height)