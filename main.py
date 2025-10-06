import pygame
import sys
import asyncio
import platform
from game_state_manager import GameStateManager

# Display constants
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 2560

async def main():
    """Main game function - now much cleaner with class-based architecture"""
    
    # Handle URL arguments for username (preserved from original)
    username = None
    url_arguments = {k: v for item in PyConfig.orig_argv if item for k, v in [item.split('=', 1)]}
    if 'user' in url_arguments:
        username = url_arguments['user']
        platform.console.log(f"Logged in with username {username}")

    # Initialize pygame
    pygame.init()
    
    # Initialize joystick support
    pygame.joystick.init()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gravitation Game")
    
    # Initialize the game state manager
    game_manager = GameStateManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Initialize scoreboard (once at startup)
    await game_manager.initialize_scoreboard()
    platform.console.log(f"{game_manager.scoreboard}")
    
    # Set username for scoreboard updates
    if username:
        game_manager.set_username(username)
    
    # Game loop
    clock = pygame.time.Clock()
    delta_time = 1.0  # Initialize delta_time for first frame
    
    while game_manager.is_running():
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_manager.quit()

        if game_manager.trigger_scoreboard_update:
            await game_manager.initialize_scoreboard()

        # Handle input and update game state based on current state
        if game_manager.get_current_state().value == "menu":
            # Handle menu input
            game_manager.handle_menu_input()
        
        elif game_manager.get_current_state().value == "playing":
            # Handle game input
            game_manager.handle_game_input()
            
            # Update gameplay logic with delta_time for frame-rate independent physics
            game_manager.update_gameplay(delta_time)
            
            # Check for level completion
            if game_manager.is_level_completed():
                # Handle scoreboard update and level completion logic
                await game_manager.handle_level_completion()
                
                # Show completion overlay (preserved from original)
                game_manager.renderer.render_level_completion_overlay(screen)
                game_manager.renderer.update_display()
                
                # Wait a moment then return to menu (preserved timing)
                await asyncio.sleep(2)
                game_manager.switch_to_menu()
                continue

        # Render the current state
        game_manager.render_current_state(screen)
        
        # Update display
        game_manager.renderer.update_display()
        
        # Control frame rate and calculate delta_time for frame-rate independent physics
        # clock.tick(60) returns milliseconds elapsed since last call
        dt_ms = clock.tick(60)
        # Normalize to a standard 60 FPS frame (16.67ms)
        delta_time = dt_ms / 16.67
        await asyncio.sleep(0)  # This line is critical; ensure you keep the sleep time at 0
    
    # Quit (preserved from original)
    pygame.quit()
    sys.exit()

# Run the game (preserved from original)
asyncio.run(main())