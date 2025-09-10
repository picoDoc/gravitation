import pygame
import sys
import math
import asyncio
import platform
from custom_request import RequestHandler
from level import Level
from menu import GameState, MenuState
import json

# Display constants
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 2560

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


def process_input_controls(joystick, menu_mode=False):
    """
    Process both keyboard and controller inputs, returning unified control states.
    
    Args:
        joystick: Current joystick object (can be None)
        menu_mode: Boolean indicating if we're processing menu inputs
        
    Returns:
        For game mode: tuple: (joystick, thrust, rotate_left, rotate_right)
        For menu mode: tuple: (joystick, navigate_left, navigate_right, select, back_to_menu)
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
    controller_action1 = False  # Thrust in game, Select in menu
    controller_left = False
    controller_right = False
    controller_up = False
    controller_down = False
    controller_action2 = False  # Back to menu (Circle button)
    
    if joystick is not None:
        # PS4 X button for main action (button 0)
        controller_action1 = joystick.get_button(0)
        
        # PS4 Circle button for secondary action (button 1) - back to menu
        try:
            controller_action2 = joystick.get_button(1)
        except:
            controller_action2 = False
        
        # Use left analog stick for navigation
        left_stick_x = joystick.get_axis(0)  # left/right axis
        left_stick_y = joystick.get_axis(1)  # up/down axis
        
        # Use D-pad for navigation as well
        try:
            dpad_left = joystick.get_button(14)
            dpad_right = joystick.get_button(15)
            dpad_up = joystick.get_button(12)
            dpad_down = joystick.get_button(13)
        except:
            # Fallback if D-pad buttons don't exist
            dpad_left = False
            dpad_right = False
            dpad_up = False
            dpad_down = False
        
        # Set controller navigation flags
        controller_left = (left_stick_x < -0.3) or dpad_left
        controller_right = (left_stick_x > 0.3) or dpad_right
        controller_up = (left_stick_y < -0.3) or dpad_up
        controller_down = (left_stick_y > 0.3) or dpad_down
    else:
        # Initialize controller directions when no joystick
        controller_left = False
        controller_right = False
        controller_up = False
        controller_down = False
    
    if menu_mode:
        # Menu input handling (up/down navigation for vertical layout)
        navigate_up = keys[pygame.K_UP] or controller_up
        navigate_down = keys[pygame.K_DOWN] or controller_down
        select = keys[pygame.K_RETURN] or controller_action1
        back_to_menu = keys[pygame.K_ESCAPE] or controller_action2
        
        return joystick, navigate_up, navigate_down, select, back_to_menu
    else:
        # Game input handling
        thrust = keys[pygame.K_UP] or controller_action1
        rotate_left = keys[pygame.K_LEFT] or controller_left
        rotate_right = keys[pygame.K_RIGHT] or controller_right
        back_to_menu = keys[pygame.K_ESCAPE] or controller_action2
        reset_level = keys[pygame.K_r]  # R key for reset
        
        # Add controller reset button (Triangle button - button 2)
        if joystick is not None:
            try:
                reset_level = reset_level or joystick.get_button(2)  # Triangle button
            except:
                pass  # Ignore if button doesn't exist
        
        return joystick, thrust, rotate_left, rotate_right, back_to_menu, reset_level


async def pull_scoreboard():
    return json.loads(await session.get("https://api.jsonbin.io/v3/b/68c0361ed0ea881f40776fe7"))["record"]


async def update_scoreboard(level=None, user=None, time=None):
    scoreboard = await pull_scoreboard()
    scoreboard[level][user] = time
    await session.put("https://api.jsonbin.io/v3/b/68c0361ed0ea881f40776fe7", data=scoreboard)
    return scoreboard


async def main():
    """Main game function containing the game loop and logic."""

    # Username state
    USERNAME = None

    url_arguments = {k: v for item in PyConfig.orig_argv if item for k, v in [item.split('=', 1)]}
    if 'user' in url_arguments:
        USERNAME = url_arguments['user']
        platform.console.log(f"Logged in with username {USERNAME}")

    # Try to get scoreboard data from jsonbin
    SCOREBOARD = await pull_scoreboard()
    platform.console.log(f"{SCOREBOARD}")

    SCOREBOARD = await update_scoreboard(level="Ryan Level", user="ryan", time="00:02:00.000")
    platform.console.log(f"{SCOREBOARD}")

    # Initialize pygame
    pygame.init()
    
    # Initialize joystick support
    pygame.joystick.init()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gravitation Game")
    
    # Set up controller (PS4 controller)
    joystick = None
    
    # Initialize game state management
    current_state = GameState.MENU
    menu_state = MenuState(SCREEN_WIDTH, SCREEN_HEIGHT, SCOREBOARD)
    
    # Game variables (will be initialized when a level is selected)
    current_level = None
    spaceship_image_original = None
    spaceship_image = None
    spaceship_rect = None
    spaceship_x = 0
    spaceship_y = 0
    spaceship_velocity_x = 0
    spaceship_velocity_y = 0
    spaceship_rotation = 0
    level_completed = False
    timer_font = pygame.font.Font(None, 48)
    timer_start_time = 0
    timer_current_time = 0
    
    # Input debouncing for menu navigation and reset
    last_navigate_time = 0
    last_select_time = 0
    last_reset_time = 0
    navigate_delay = 200  # milliseconds between navigation inputs
    select_delay = 300    # milliseconds between select inputs
    reset_delay = 500     # milliseconds between reset inputs
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        current_time = pygame.time.get_ticks()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ###################################################################
        ###                     STATE MANAGEMENT                        ###
        ###################################################################
        
        if current_state == GameState.MENU:
            # Menu state processing
            joystick, navigate_up, navigate_down, select, back_to_menu = process_input_controls(joystick, menu_mode=True)
            
            # Handle menu navigation with debouncing
            if navigate_up and current_time - last_navigate_time > navigate_delay:
                menu_state.navigate_up()
                last_navigate_time = current_time
            elif navigate_down and current_time - last_navigate_time > navigate_delay:
                menu_state.navigate_down()
                last_navigate_time = current_time
            
            # Handle level selection with debouncing
            if select and current_time - last_select_time > select_delay:
                selected_level = menu_state.get_selected_level()
                if selected_level:
                    # Load the selected level
                    current_level = Level(selected_level.filename)
                    print(f"Level {selected_level.name} loaded successfully!")
                    
                    # Load spaceship image
                    spaceship_image_original = pygame.image.load("spaceship.png")
                    spaceship_image = spaceship_image_original.copy()
                    spaceship_rect = spaceship_image.get_rect()
                    
                    # Reset spaceship position and physics
                    spaceship_x = 1300 - spaceship_rect.width // 2
                    spaceship_y = 2450
                    spaceship_velocity_x = 0
                    spaceship_velocity_y = 0
                    spaceship_rotation = 0
                    level_completed = False
                    
                    # Start the timer
                    timer_start_time = pygame.time.get_ticks()
                    
                    # Switch to playing state
                    current_state = GameState.PLAYING
                    
                last_select_time = current_time
            
            # Render menu
            menu_state.render(screen)
            
        elif current_state == GameState.PLAYING:
            # Game state processing
            joystick, thrust, rotate_left, rotate_right, back_to_menu, reset_level = process_input_controls(joystick, menu_mode=False)
            
            # Check for reset level input with debouncing
            if (reset_level and current_time - last_reset_time > reset_delay and
                current_level is not None and spaceship_image_original is not None):
                print("Reset button pressed - attempting reset...")
                
                # Reset spaceship image and rect (same as level loading)
                spaceship_image = spaceship_image_original.copy()
                spaceship_rect = spaceship_image.get_rect()
                
                # Reset spaceship position and physics to starting state
                spaceship_x = 1300 - spaceship_rect.width // 2
                spaceship_y = 2450
                spaceship_velocity_x = 0
                spaceship_velocity_y = 0
                spaceship_rotation = 0
                level_completed = False
                
                # Reset the timer
                timer_start_time = pygame.time.get_ticks()
                
                last_reset_time = current_time
                print("Level reset successful!")
            
            # Check for back to menu input
            if back_to_menu:
                current_state = GameState.MENU
                level_completed = False
                continue

            # Only process physics and input if level is not completed
            if not level_completed:
                
                ###################################################################
                ###                      GAME LOGIC                             ###
                ###################################################################

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
                    
                    # Determine bounce direction based on collision type
                    if collision_reason == "Screen boundary collision detected!":
                        # For screen boundaries, determine bounce direction from which boundary was hit
                        bounce_x = False
                        bounce_y = False
                        
                        # Check which screen boundary was hit (use current position that's outside bounds)
                        if spaceship_x < LEFT_BOUNDARY or spaceship_x + spaceship_image_original.get_width() > RIGHT_BOUNDARY:
                            bounce_x = True
                        if spaceship_y < TOP_BOUNDARY or spaceship_y + spaceship_image_original.get_height() > BOTTOM_BOUNDARY:
                            bounce_y = True
                            
                    else:
                        prev_collision_x = prev_spaceship_x + spaceship_image_original.get_width() // 2 - temp_spaceship_rect.width // 2
                        prev_collision_y = prev_spaceship_y + spaceship_image_original.get_height() // 2 - temp_spaceship_rect.height // 2

                        # For level geometry collisions, check the prev x position
                        solid_collision_x_back, _ = current_level.check_spaceship_collisions(
                            temp_spaceship_image, prev_collision_x, collision_y
                        )
                        
                        # and prev y position
                        solid_collision_y_back, _ = current_level.check_spaceship_collisions(
                            temp_spaceship_image, collision_x, prev_collision_y
                        )
                        
                        # If moving back in the direction of travel removes collision, bounce in that direction
                        bounce_x = not solid_collision_x_back
                        bounce_y = not solid_collision_y_back
                    
                    # Apply bouncing by reversing velocity in appropriate directions
                    if bounce_x:
                        spaceship_velocity_x = -spaceship_velocity_x
                    elif bounce_y:
                        spaceship_velocity_y = -spaceship_velocity_y
                    else:
                        spaceship_velocity_x = -spaceship_velocity_x
                        spaceship_velocity_y = -spaceship_velocity_y

                    # Revert to previous position
                    spaceship_x = prev_spaceship_x
                    spaceship_y = prev_spaceship_y
                    # Stop velocity to prevent getting stuck
                    spaceship_velocity_x *= 0.5  # Reduce velocity significantly
                    spaceship_velocity_y *= 0.5
            
            # Update timer (only if level not completed)
            if not level_completed:
                timer_current_time = pygame.time.get_ticks() - timer_start_time
            
            # Check for level completion and handle return to menu
            if level_completed:

                if USERNAME:
                    # get the time in text
                    # TODO make this a bit more succinct
                    total_seconds = timer_current_time // 1000
                    minutes = total_seconds // 60
                    seconds = total_seconds % 60
                    milliseconds = (timer_current_time % 1000) // 10  # Get centiseconds (00-99)
                    timer_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

                    # if it's a new best time, update it
                    if timer_text < SCOREBOARD[selected_level.name].get(USERNAME, '59:59.000'):
                        SCOREBOARD[selected_level.name][USERNAME] = timer_text
                        SCOREBOARD = await update_scoreboard(level=selected_level.name, user=USERNAME, time=timer_text)

                # Show completion message briefly, then return to menu
                completion_text = timer_font.render("Level Complete! Returning to menu...", True, WHITE)
                completion_rect = completion_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                
                # Draw completion overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(128)
                overlay.fill(BLACK)
                screen.blit(overlay, (0, 0))
                screen.blit(completion_text, completion_rect)
                pygame.display.flip()
                
                # Wait a moment then return to menu
                await asyncio.sleep(2)
                current_state = GameState.MENU
                level_completed = False
                continue

            #######################################################################
            ###                       DRAW SCREEN                               ###
            #######################################################################
            
            # Only render game screen if we're in playing state and level is loaded
            if current_level is not None:
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
                # TODO make this a bit more succinct
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
        
        # Update display for both states
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(60)
        await asyncio.sleep(0)  # This line is critical; ensure you keep the sleep time at 0
    
    # Quit
    pygame.quit()
    sys.exit()


asyncio.run(main())