import pygame
import sys
import math
import asyncio
import platform
from custom_request import RequestHandler
from level import Level

# Display constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200

# Physics constants
GRAVITY = 0.15  # Constant downward acceleration
THRUST_POWER = 0.35  # Thrust acceleration magnitude
ROTATION_SPEED = 3  # Degrees per frame when rotating

# Boundary constants
TOP_BOUNDARY = 0
BOTTOM_BOUNDARY = SCREEN_HEIGHT
LEFT_BOUNDARY = 0
RIGHT_BOUNDARY = SCREEN_WIDTH
MAX_VELOCITY = 15  # Prevent extreme velocities
MIN_VELOCITY = -15

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)

session = RequestHandler()


def process_input_controls(joystick):
    """
    Process both keyboard and controller inputs, returning unified control states.
    
    Args:
        joystick: Current joystick object (can be None)
        
    Returns:
        tuple: (joystick, thrust, rotate_left, rotate_right)
            - joystick: Updated joystick object
            - thrust: Boolean indicating if thrust should be applied
            - rotate_left: Boolean indicating if ship should rotate left
            - rotate_right: Boolean indicating if ship should rotate right
    """
    # Setup ps4 controller if not already initialized
    if joystick is None and pygame.joystick.get_count() > 0:
        # TODO figure out something more robust to pick the right controller (on mobile especially)
        for i in range(pygame.joystick.get_count()):
            if 'Wireless Controller' in pygame.joystick.Joystick(i).get_name():
                joystick = pygame.joystick.Joystick(i)
                break
        if joystick is not None:
            joystick.init()
            platform.console.log(f"Controller detected: {joystick.get_name()}")

    # Handle continuous key presses
    keys = pygame.key.get_pressed()
    
    # Check for controller inputs
    controller_thrust = False
    controller_left = False
    controller_right = False
    
    if joystick is not None:
        # PS4 X button for thrust (button 0 on PS4 controllers)
        controller_thrust = joystick.get_button(0)
        
        # Use left analog stick for rotation (axis 0: left/right)
        left_stick_x = joystick.get_axis(0)
        
        # Use D-pad for rotation as well (buttons 14 and 15 on PS4 controller)
        try:
            dpad_left = joystick.get_button(14)
            dpad_right = joystick.get_button(15)
        except:
            # Fallback if D-pad buttons don't exist
            dpad_left = False
            dpad_right = False
        
        # Set controller rotation flags
        controller_left = (left_stick_x < -0.3) or dpad_left
        controller_right = (left_stick_x > 0.3) or dpad_right
    
    # Combine keyboard and controller inputs
    thrust = keys[pygame.K_UP] or controller_thrust
    rotate_left = keys[pygame.K_LEFT] or controller_left
    rotate_right = keys[pygame.K_RIGHT] or controller_right
    
    return joystick, thrust, rotate_left, rotate_right


async def main():
    """Main game function containing the game loop and logic."""

    # Try to get http data
    #resp = await session.get("https://api.jsonbin.io/v3/b/68b5a0ccae596e708fded73d")
    #platform.console.log(f"{resp}")

    # Initialize pygame
    pygame.init()
    
    # Initialize joystick support
    pygame.joystick.init()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gravitation Game")
    
    # Set up controller (PS4 controller)
    joystick = None
    
    # Load level
    current_level = Level("test_level.png")
    print("Level loaded successfully!")
    
    # Load spaceship image
    spaceship_image_original = pygame.image.load("spaceship.png")
    spaceship_image = spaceship_image_original.copy()
    spaceship_rect = spaceship_image.get_rect()
    
    # Spaceship position and physics
    spaceship_x = 1100 - spaceship_rect.width // 2  # Center horizontally (1600/2)
    spaceship_y = 1100  # Spawn in the middle clear area of the test level (1200/2)
    spaceship_velocity_x = 0  # Horizontal velocity (positive = moving right)
    spaceship_velocity_y = 0  # Vertical velocity (positive = moving down)
    spaceship_rotation = 0  # Rotation angle in degrees (0 = pointing up)
    
    # Game state management
    level_completed = False  # Flag to track if the level has been completed
    
    # Timer setup
    timer_font = pygame.font.Font(None, 48)  # Font for timer display (larger for better visibility)
    timer_start_time = 0  # Will be set when game loop starts
    timer_current_time = 0  # Current elapsed time in milliseconds
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    # Start the timer
    timer_start_time = pygame.time.get_ticks()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Only process physics and input if level is not completed
        if not level_completed:
            # Process input controls (keyboard + controller)
            joystick, thrust, rotate_left, rotate_right = process_input_controls(joystick)
            
            # Apply directional thrust when thrust input is active
            if thrust:
                # Convert rotation to radians for math functions
                angle_rad = math.radians(spaceship_rotation)
                # Calculate thrust components (negative sin for x because pygame x increases right)
                # negative cos for y because pygame y increases down, but we want up to be negative
                thrust_x = THRUST_POWER * math.sin(angle_rad)
                thrust_y = -THRUST_POWER * math.cos(angle_rad)
                
                spaceship_velocity_x += thrust_x
                spaceship_velocity_y += thrust_y
            
            # Handle rotation
            if rotate_left:
                spaceship_rotation -= ROTATION_SPEED
            if rotate_right:
                spaceship_rotation += ROTATION_SPEED
            
            # Keep rotation within 0-360 degrees
            spaceship_rotation = spaceship_rotation % 360
            
            # Always apply gravity
            spaceship_velocity_y += GRAVITY
            
            # Store previous position for collision rollback
            prev_spaceship_x = spaceship_x
            prev_spaceship_y = spaceship_y
            
            # Update position based on velocity
            spaceship_x += spaceship_velocity_x
            spaceship_y += spaceship_velocity_y
            
            # Check for collision with level geometry (both solid and special zones)
            temp_spaceship_image = pygame.transform.rotate(spaceship_image_original, -spaceship_rotation)
            temp_spaceship_rect = temp_spaceship_image.get_rect()
            collision_x = spaceship_x + spaceship_image_original.get_width() // 2 - temp_spaceship_rect.width // 2
            collision_y = spaceship_y + spaceship_image_original.get_height() // 2 - temp_spaceship_rect.height // 2
            
            # Combined collision check - checks both solid and special zones in one pass
            solid_collision, special_collision = current_level.check_spaceship_collisions(temp_spaceship_image, collision_x, collision_y)
            
            # Check for target zone collision (special zones)
            if special_collision:
                level_completed = True
        
            # Check for screen boundary collisions first
            collision_occurred = False
            collision_reason = ""
            
            # Check screen boundaries
            if (spaceship_x < LEFT_BOUNDARY or
                spaceship_x + spaceship_image_original.get_width() > RIGHT_BOUNDARY or
                spaceship_y < TOP_BOUNDARY or
                spaceship_y + spaceship_image_original.get_height() > BOTTOM_BOUNDARY):
                collision_occurred = True
                collision_reason = "Screen boundary collision detected!"
            
            # If no boundary collision, check for solid collision with level geometry
            if not collision_occurred and solid_collision:
                collision_occurred = True
                collision_reason = "Pixel-perfect collision detected!"
            
            # Handle any collision that occurred
            if collision_occurred:
                print(collision_reason)
                # Revert to previous position
                spaceship_x = prev_spaceship_x
                spaceship_y = prev_spaceship_y
                # Stop velocity to prevent getting stuck
                spaceship_velocity_x *= 0.1  # Reduce velocity significantly
                spaceship_velocity_y *= 0.1
        
            # Update timer (only if level not completed)
            timer_current_time = pygame.time.get_ticks() - timer_start_time
        
        # Render level background
        screen.blit(current_level.get_visual_surface(), (0, 0))
        
        # Rotate spaceship image
        spaceship_image = pygame.transform.rotate(spaceship_image_original, -spaceship_rotation)
        spaceship_rect = spaceship_image.get_rect()
        
        # Update spaceship position (center the rotated image)
        spaceship_rect.centerx = spaceship_x + spaceship_image_original.get_width() // 2
        spaceship_rect.centery = spaceship_y + spaceship_image_original.get_height() // 2
        
        screen.blit(spaceship_image, spaceship_rect)
        
        # Render timer in top-right corner
        # Convert milliseconds to MM:SS.ms format
        total_seconds = timer_current_time // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        milliseconds = (timer_current_time % 1000) // 10  # Get centiseconds (00-99)
        
        timer_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        timer_surface = timer_font.render(timer_text, True, WHITE)
        timer_rect = timer_surface.get_rect()
        timer_rect.topright = (SCREEN_WIDTH - 20, 20)  # 20px padding from edges
        
        # Draw black background rectangle for better text readability
        background_padding = 8
        background_rect = timer_rect.copy()
        background_rect.inflate_ip(background_padding * 2, background_padding * 2)
        pygame.draw.rect(screen, BLACK, background_rect)
        
        # Draw the timer text on top of the black background
        screen.blit(timer_surface, timer_rect)
        
        # Update display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(60)
        await asyncio.sleep(0)  # This line is critical; ensure you keep the sleep time at 0
    
    # Quit
    pygame.quit()
    sys.exit()


asyncio.run(main())
