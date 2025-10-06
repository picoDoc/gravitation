import pygame
import math
from entity import Entity

class Spaceship(Entity):
    """Spaceship entity with thrust and rotation capabilities"""
    
    # Physics constants - preserved from original main.py
    GRAVITY = 0.12
    THRUST_POWER = 0.25
    ROTATION_SPEED = 6
    MAX_VELOCITY = 15
    MIN_VELOCITY = -15
    
    # Starting position constants - preserved from original main.py
    START_X_OFFSET = 1300  # spaceship_x = 1300 - spaceship_rect.width // 2
    START_Y = 2450
    
    def __init__(self, image_path="spaceship.png"):
        super().__init__(0, 0, 0, image_path)
        
        # Set velocity limits
        self.physics.max_velocity = self.MAX_VELOCITY
        self.physics.min_velocity = self.MIN_VELOCITY
        
        # Initialize to starting position
        self.reset_to_start()
    
    def reset_to_start(self):
        """Reset spaceship to starting position and state"""
        # Calculate starting position based on image size (matching original logic)
        if self.renderer.original_image:
            start_x = self.START_X_OFFSET - self.renderer.original_image.get_width() // 2
        else:
            start_x = self.START_X_OFFSET
        
        self.set_position(start_x, self.START_Y)
        self.set_velocity(0, 0)
        self.set_rotation(0)
    
    def apply_thrust(self, thrust_active):
        """Apply thrust in the direction the spaceship is facing"""
        if thrust_active:
            # Convert rotation to radians for math functions (matching original)
            angle_rad = math.radians(self.transform.rotation)
            
            # Calculate thrust components (matching original logic exactly)
            # negative sin for x because pygame x increases right
            # negative cos for y because pygame y increases down, but we want up to be negative
            thrust_x = self.THRUST_POWER * math.sin(angle_rad)
            thrust_y = -self.THRUST_POWER * math.cos(angle_rad)
            
            # Add thrust to velocity
            self.physics.add_velocity(thrust_x, thrust_y)
    
    def apply_rotation(self, rotate_left, rotate_right, level=None):
        """Apply rotation based on input with collision-free positioning"""
        rotation_applied = False
        
        if rotate_left:
            self.transform.rotate(-self.ROTATION_SPEED)
            self.renderer.update_rotation(self.transform.rotation)
            rotation_applied = True
        elif rotate_right:
            self.transform.rotate(self.ROTATION_SPEED)
            self.renderer.update_rotation(self.transform.rotation)
            rotation_applied = True
        
        # If rotation was applied and we have a level, check for collision
        if rotation_applied and level is not None:
            if self.check_collision_with_level(level):
                # Find a collision-free position
                safe_position = self.find_collision_free_position(level)
                if safe_position:
                    # Move to safe position
                    self.set_position(safe_position[0], safe_position[1])
                    print(f"Collision-free rotation: moved to ({safe_position[0]:.1f}, {safe_position[1]:.1f})")
                # If no safe position found, rotation is still allowed but spaceship stays in place
    
    def apply_gravity(self):
        """Apply constant gravity (matching original)"""
        self.physics.apply_gravity(self.GRAVITY)
    
    def handle_collision(self, bounce_x=False, bounce_y=False):
        """Handle collision with bouncing (matching original logic exactly)"""
        # Apply bouncing by reversing velocity in appropriate directions
        if bounce_x:
            self.physics.velocity_x = -self.physics.velocity_x
        elif bounce_y:
            self.physics.velocity_y = -self.physics.velocity_y
        else:
            # If neither direction specified, bounce both
            self.physics.velocity_x = -self.physics.velocity_x
            self.physics.velocity_y = -self.physics.velocity_y
        
        # Rollback to previous position
        self.rollback_position()
        
        # Reduce velocity significantly (matching original)
        self.physics.velocity_x *= 0.5
        self.physics.velocity_y *= 0.5
    
    def get_collision_rect_info(self):
        """Get information needed for collision detection"""
        if not self.renderer.current_image or not self.renderer.original_image:
            return None, 0, 0
        
        # Calculate collision position (matching original logic)
        collision_x = (self.transform.x + self.renderer.original_image.get_width() // 2 - 
                      self.renderer.current_image.get_width() // 2)
        collision_y = (self.transform.y + self.renderer.original_image.get_height() // 2 - 
                      self.renderer.current_image.get_height() // 2)
        
        return self.renderer.current_image, collision_x, collision_y
    
    def is_within_screen_bounds(self, screen_width, screen_height):
        """Check if spaceship is within screen boundaries"""
        if not self.renderer.original_image:
            return True
        
        # Check screen boundaries (matching original logic)
        return not (self.transform.x < 0 or
                   self.transform.x + self.renderer.original_image.get_width() > screen_width or
                   self.transform.y < 0 or
                   self.transform.y + self.renderer.original_image.get_height() > screen_height)
    
    def get_boundary_collision_type(self, screen_width, screen_height):
        """Determine which boundary was hit for bounce direction"""
        if not self.renderer.original_image:
            return False, False
        
        bounce_x = False
        bounce_y = False
        
        # Check which screen boundary was hit (matching original logic)
        if (self.transform.x < 0 or 
            self.transform.x + self.renderer.original_image.get_width() > screen_width):
            bounce_x = True
        if (self.transform.y < 0 or 
            self.transform.y + self.renderer.original_image.get_height() > screen_height):
            bounce_y = True
        
        return bounce_x, bounce_y
    
    def update(self, delta_time=1.0):
        """Update spaceship state"""
        # Apply gravity every frame
        self.apply_gravity()
        
        # Update physics (position based on velocity)
        self.update_physics(delta_time)
    
    def get_image_for_collision(self):
        """Get the current rotated image for collision detection"""
        return self.renderer.current_image
    
    def get_original_image_size(self):
        """Get the original image size"""
        return self.renderer.get_original_size()
    
    def check_collision_with_level(self, level):
        """Check if spaceship collides with level at current position and rotation"""
        spaceship_image, collision_x, collision_y = self.get_collision_rect_info()
        if spaceship_image and level:
            solid_collision, special_collision = level.check_spaceship_collisions(
                spaceship_image, collision_x, collision_y
            )
            return solid_collision
        return False
    
    def check_collision_after_rotation(self, level, rotation_delta):
        """Check if spaceship would collide after applying rotation delta"""
        # Store current state
        original_rotation = self.transform.rotation
        
        # Temporarily apply rotation
        self.transform.rotate(rotation_delta)
        self.renderer.update_rotation(self.transform.rotation)
        
        # Check collision
        collision = self.check_collision_with_level(level)
        
        # Restore original state
        self.transform.set_rotation(original_rotation)
        self.renderer.update_rotation(self.transform.rotation)
        
        return collision
    
    def find_collision_free_position(self, level, max_distance=25):
        """
        Find a nearby collision-free position, prioritizing velocity direction.
        
        Args:
            level: The level object for collision checking
            max_distance: Maximum distance to search for a safe position
            
        Returns:
            tuple: (x, y) of safe position, or None if none found
        """
        # Get current velocity direction for prioritized search
        velocity_x, velocity_y = self.get_velocity()
        velocity_magnitude = math.sqrt(velocity_x**2 + velocity_y**2)
        
        # If we have velocity, use it as primary search direction
        if velocity_magnitude > 0.1:  # Minimum velocity threshold
            # Normalize velocity vector
            norm_vel_x = velocity_x / velocity_magnitude
            norm_vel_y = velocity_y / velocity_magnitude
            
            # Try positions along velocity direction first
            for distance in range(1, max_distance + 1, 2):  # Step by 2 pixels
                test_x = self.transform.x + norm_vel_x * distance
                test_y = self.transform.y + norm_vel_y * distance
                
                # Test this position
                if self._test_position_safe(level, test_x, test_y):
                    return (test_x, test_y)
        
        # If velocity direction doesn't work, try expanding circle search
        return self._expanding_circle_search(level, max_distance)
    
    def _test_position_safe(self, level, test_x, test_y):
        """Test if a position is collision-free"""
        # Store current position
        original_x, original_y = self.transform.x, self.transform.y
        
        # Temporarily move to test position
        self.set_position(test_x, test_y)
        
        # Check collision
        collision = self.check_collision_with_level(level)
        
        # Restore original position
        self.set_position(original_x, original_y)
        
        return not collision
    
    def _expanding_circle_search(self, level, max_distance):
        """Search for safe position in expanding circle pattern"""
        # Try positions in expanding circles
        for radius in range(1, max_distance + 1, 2):  # Step by 2 pixels
            # Try 8 directions around current position
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                angle_rad = math.radians(angle)
                test_x = self.transform.x + radius * math.cos(angle_rad)
                test_y = self.transform.y + radius * math.sin(angle_rad)
                
                if self._test_position_safe(level, test_x, test_y):
                    return (test_x, test_y)
        
        return None  # No safe position found