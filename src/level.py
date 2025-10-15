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
            
        except pygame.error as e:
            raise RuntimeError(f"Failed to load level image {self.image_path}: {e}")
    
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
        Check for pixel-perfect collision between spaceship and level for SOLID, SPECIAL, and HAZARD zones.
        Only considers non-transparent pixels of the spaceship.
        This combined method avoids duplicate pixel iteration.
        
        Args:
            spaceship_surface (pygame.Surface): The rotated spaceship surface
            spaceship_x (int): X position of spaceship (top-left corner)
            spaceship_y (int): Y position of spaceship (top-left corner)
            
        Returns:
            tuple: (solid_collision, special_collision, hazard_collision) - all bool values
        """
        # Get spaceship dimensions
        ship_width = spaceship_surface.get_width()
        ship_height = spaceship_surface.get_height()
        
        # Check bounds to avoid unnecessary pixel checking
        if (spaceship_x >= self.width or spaceship_y >= self.height or
            spaceship_x + ship_width <= 0 or spaceship_y + ship_height <= 0):
            return False, False, False
        
        # Calculate the overlapping region between spaceship and level
        # Convert float coordinates to integers for range operations
        spaceship_x_int = int(spaceship_x)
        spaceship_y_int = int(spaceship_y)
        
        start_x = max(0, spaceship_x_int)
        end_x = min(self.width, spaceship_x_int + ship_width)
        start_y = max(0, spaceship_y_int)
        end_y = min(self.height, spaceship_y_int + ship_height)
        
        # Track collision types found
        solid_collision = False
        special_collision = False
        hazard_collision = False
        
        # Check each pixel in the overlapping region
        for level_x in range(start_x, end_x):
            for level_y in range(start_y, end_y):
                # Calculate corresponding spaceship pixel coordinates
                ship_pixel_x = level_x - spaceship_x_int
                ship_pixel_y = level_y - spaceship_y_int
                
                # Skip if outside spaceship bounds (shouldn't happen but safety check)
                if (ship_pixel_x < 0 or ship_pixel_x >= ship_width or
                    ship_pixel_y < 0 or ship_pixel_y >= ship_height):
                    continue
                
                # Get spaceship pixel (with alpha channel)
                try:
                    spaceship_pixel = spaceship_surface.get_at((ship_pixel_x, ship_pixel_y))
                    spaceship_alpha = spaceship_pixel[3] if len(spaceship_pixel) > 3 else 255
                    
                    # Only check collision if spaceship pixel is not transparent
                    if spaceship_alpha > 0:  # Non-transparent pixel
                        # Check collision type at this level position
                        collision_type = self.check_collision_at_point(level_x, level_y)
                        
                        if collision_type == 'SOLID':
                            solid_collision = True
                        elif collision_type == 'SPECIAL':
                            special_collision = True
                        elif collision_type == 'HAZARD':
                            hazard_collision = True
                        
                        # Early exit optimization: if we found solid collision, no need to continue
                        # (since solid collision would stop the game anyway)
                        if solid_collision:
                            return True, special_collision, hazard_collision
                            
                except (IndexError, pygame.error):
                    # Skip invalid pixels
                    continue
        
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