import pygame
import sys
import math
import asyncio
import platform

# Display constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Physics constants
GRAVITY = 0.25  # Constant downward acceleration
THRUST_POWER = 0.65  # Thrust acceleration magnitude
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


async def main():
    """Main game function containing the game loop and logic."""
    # Initialize pygame
    pygame.init()
    
    # Initialize joystick support
    pygame.joystick.init()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gravitation Game")
    
    # Set up controller (PS4 controller)
    joystick = None        
    
    # Load spaceship image
    spaceship_image_original = pygame.image.load("spaceship.png")
    spaceship_image = spaceship_image_original.copy()
    spaceship_rect = spaceship_image.get_rect()
    
    # Spaceship position and physics
    spaceship_x = 400 - spaceship_rect.width // 2
    spaceship_y = 550
    spaceship_velocity_x = 0  # Horizontal velocity (positive = moving right)
    spaceship_velocity_y = 0  # Vertical velocity (positive = moving down)
    spaceship_rotation = 0  # Rotation angle in degrees (0 = pointing up)
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Setup ps4 controller
        if joystick is None and pygame.joystick.get_count() > 0:
            # TODO figure out something more robust to pick the right controller
            joystick = pygame.joystick.Joystick(1)
            joystick.init()
            platform.console.log(f"Controller detected: {joystick.get_name()}")

        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        
        # Check for controller inputs
        controller_thrust = False
        controller_left = False
        controller_right = False
        
        if joystick is not None:
            # PS4 X button for thrust (button 1 on most systems)
            # TODO pick x for this not o
            controller_thrust = joystick.get_button(1)
            
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
        
        # Apply directional thrust when up key is pressed OR controller X button
        if keys[pygame.K_UP] or controller_thrust:
            # Convert rotation to radians for math functions
            angle_rad = math.radians(spaceship_rotation)
            # Calculate thrust components (negative sin for x because pygame x increases right)
            # negative cos for y because pygame y increases down, but we want up to be negative
            thrust_x = THRUST_POWER * math.sin(angle_rad)
            thrust_y = -THRUST_POWER * math.cos(angle_rad)
            
            spaceship_velocity_x += thrust_x
            spaceship_velocity_y += thrust_y
        
        # Handle rotation (keyboard OR controller)
        if keys[pygame.K_LEFT] or controller_left:
            spaceship_rotation -= ROTATION_SPEED
        if keys[pygame.K_RIGHT] or controller_right:
            spaceship_rotation += ROTATION_SPEED
        
        # Keep rotation within 0-360 degrees
        spaceship_rotation = spaceship_rotation % 360
        
        # Always apply gravity
        spaceship_velocity_y += GRAVITY
        
        # Update position based on velocity
        spaceship_x += spaceship_velocity_x
        spaceship_y += spaceship_velocity_y
        
        # Keep spaceship on screen - horizontal boundaries
        if spaceship_x < LEFT_BOUNDARY:
            spaceship_x = LEFT_BOUNDARY
            spaceship_velocity_x = 0
        elif spaceship_x > RIGHT_BOUNDARY - spaceship_rect.width:
            spaceship_x = RIGHT_BOUNDARY - spaceship_rect.width
            spaceship_velocity_x = 0
        
        # Keep spaceship on screen - vertical boundaries
        if spaceship_y < TOP_BOUNDARY:
            spaceship_y = TOP_BOUNDARY
            spaceship_velocity_y = 0
        elif spaceship_y > BOTTOM_BOUNDARY - spaceship_rect.height:
            spaceship_y = BOTTOM_BOUNDARY - spaceship_rect.height
            spaceship_velocity_y = 0
        
        # Fill screen with white
        screen.fill(WHITE)
        
        # Rotate spaceship image
        spaceship_image = pygame.transform.rotate(spaceship_image_original, -spaceship_rotation)
        spaceship_rect = spaceship_image.get_rect()
        
        # Update spaceship position (center the rotated image)
        spaceship_rect.centerx = spaceship_x + spaceship_image_original.get_width() // 2
        spaceship_rect.centery = spaceship_y + spaceship_image_original.get_height() // 2
        
        screen.blit(spaceship_image, spaceship_rect)
        
        # Update display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(60)
        await asyncio.sleep(0)  # This line is critical; ensure you keep the sleep time at 0
    
    # Quit
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
