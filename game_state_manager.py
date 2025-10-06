import pygame
import platform
import json
from menu import GameState, MenuState
from level import Level
from spaceship import Spaceship
from game_renderer import GameRenderer
from input_manager import InputManager
from timer import GameTimer
from custom_request import RequestHandler
from ghost_system import GhostRecorder, GhostPlayback, Ghost

class GameStateManager:
    """Manages game state transitions and coordinates game loop"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialize game state
        self.current_state = GameState.MENU
        self.running = True
        
        # Initialize scoreboard session and ghosts
        self.session = RequestHandler()
        self.scoreboard = {}
        self.trigger_scoreboard_update = False
        self.best_ghosts = {}
        self.best_ghost_urls = {
            "Ryan Level": "https://api.jsonbin.io/v3/b/68c43384d0ea881f407ba93b",
            "John Level": "https://api.jsonbin.io/v3/b/68ca94be43b1c97be945f7db",
            "Martin Level": "https://api.jsonbin.io/v3/b/68ca94d343b1c97be945f7f6"
        }
        
        # Initialize components (menu_state will be created after scoreboard loads)
        self.menu_state = None
        self.renderer = GameRenderer(screen_width, screen_height)
        self.input_manager = InputManager()
        self.timer = GameTimer()
        
        # Game objects (initialized when level is selected)
        self.current_level = None
        self.spaceship = None
        self.selected_level = None
        self.level_completed = False
        
        # Ghost system components
        self.ghost_recorder = GhostRecorder()
        self.ghost_playback = GhostPlayback()
        self.ghost = None
        
        # Username for scoreboard updates
        self.username = None
    
    async def initialize_scoreboard(self):
        """Initialize scoreboard by pulling data from API"""
        self.trigger_scoreboard_update = False
        try:
            self.scoreboard = json.loads(await self.session.get("https://api.jsonbin.io/v3/b/68c0361ed0ea881f40776fe7"))["record"]
            # Create menu state now that we have scoreboard data
            self.menu_state = MenuState(self.screen_width, self.screen_height, self.scoreboard)
            self.best_ghosts = {}
            for url in self.best_ghost_urls.values():
                ghost = json.loads(await self.session.get(url))["record"]
                self.best_ghosts = {**self.best_ghosts, **ghost}
            return True
        except Exception as e:
            print(f"Failed to load scoreboard: {e}")
            # Fallback to empty scoreboard
            self.scoreboard = {}
            self.menu_state = MenuState(self.screen_width, self.screen_height, self.scoreboard)
            return False
    
    def set_username(self, username):
        """Set the username for scoreboard updates"""
        self.username = username
    
    async def update_scoreboard_api(self, level_name, user, time):
        """Update scoreboard via API"""
        try:
            # Pull fresh data to avoid conflicts
            fresh_scoreboard = json.loads(await self.session.get("https://api.jsonbin.io/v3/b/68c0361ed0ea881f40776fe7"))["record"]
            # Update with new score
            if level_name not in fresh_scoreboard:
                fresh_scoreboard[level_name] = {}
            fresh_scoreboard[level_name][user] = time
            # Push back to API
            await self.session.put("https://api.jsonbin.io/v3/b/68c0361ed0ea881f40776fe7", data=fresh_scoreboard)
            return fresh_scoreboard
        except Exception as e:
            print(f"Failed to update scoreboard: {e}")
            return self.scoreboard
        
    async def update_ghost_api(self, level_name, ghost_recording):
        """Update scoreboard via API"""
        try:
            # Update with new ghost
            ghosts = {}
            ghosts[level_name] = ghost_recording
            self.best_ghosts[level_name] = ghost_recording
            # And push back to API
            await self.session.put(self.best_ghost_urls[level_name], data=ghosts)
            return ghosts
        except Exception as e:
            print(f"Failed to update ghosts: {e}")
            return self.scoreboard
    
    async def handle_level_completion(self):
        """Handle level completion including scoreboard updates"""
        if not self.level_completed or not self.selected_level:
            return False
        
        # Handle scoreboard update if username provided
        if self.username:
            timer_text = self.timer.get_formatted_time()
            
            # Check if it's a new best time (preserved logic)
            current_best = self.scoreboard.get(self.selected_level.name, {}).get(self.username, '59:59.000')
            if timer_text < current_best:
                # Update scoreboard via API
                self.scoreboard = await self.update_scoreboard_api(
                    self.selected_level.name,
                    self.username,
                    timer_text
                )

                # Recreate menu state with updated scoreboard
                self.menu_state = MenuState(self.screen_width, self.screen_height, self.scoreboard)

                global_best = min(self.scoreboard.get(self.selected_level.name, {}).values())

                if timer_text == global_best:
                    platform.window.console.log(f"Exporting new ghost for best time on {self.selected_level.name}!!")
                    new_ghost = await self.update_ghost_api(self.selected_level.name, self.ghost_recorder.export_playback_data())
                    self.best_ghosts = {**self.best_ghosts, **new_ghost}
        
        return True
    
    def switch_to_menu(self):
        """Switch to menu state"""
        self.current_state = GameState.MENU
        self.level_completed = False
        self.current_level = None
        self.spaceship = None
        
        # Stop ghost recording and playback when returning to menu
        if self.ghost_recorder.is_recording():
            self.ghost_recorder.stop_recording()
        if self.ghost_playback.is_playing():
            self.ghost_playback.stop_playback()
        self.ghost = None
        
        self.trigger_scoreboard_update = True
    
    def switch_to_playing(self, level_info):
        """Switch to playing state with selected level"""
        try:
            # Load the selected level
            self.current_level = Level(level_info.filename)
            print(f"Level {level_info.name} loaded successfully!")
            
            # Create spaceship
            self.spaceship = Spaceship("spaceship.png")
            
            # Initialize ghost system
            self.ghost = Ghost("spaceship.png")
            
            # Start playback of thecurrent best ghost if available
            if self.best_ghosts.get(level_info.name, []):
                self.ghost_playback.load_playback_data(self.best_ghosts[level_info.name])
                print("Starting ghost playback from previous attempt")
                self.ghost_playback.start_playback()
            
            # Start recording new attempt
            self.ghost_recorder.start_recording()
            print("Started recording new ghost attempt")
            
            # Reset game state
            self.level_completed = False
            self.selected_level = level_info
            
            # Start the timer
            self.timer.start()
            
            # Switch to playing state
            self.current_state = GameState.PLAYING
            
            return True
            
        except Exception as e:
            print(f"Failed to load level {level_info.filename}: {e}")
            return False
    
    def reset_current_level(self):
        """Reset the current level"""
        if self.current_level is not None and self.spaceship is not None:
            print("Reset button pressed - attempting reset...")
            
            # Start new recording
            self.ghost_recorder.start_recording()
            
            # Load and start playback of the correct ghost for this level
            if self.selected_level and self.best_ghosts.get(self.selected_level.name, []):
                self.ghost_playback.load_playback_data(self.best_ghosts[self.selected_level.name])
                self.ghost_playback.start_playback()
                print(f"Started ghost playback for {self.selected_level.name}")
            else:
                # Stop playback if no ghost data for this level
                self.ghost_playback.stop_playback()
                print("No ghost data available for this level")
            
            print("Started recording new attempt after reset")
            
            # Reset spaceship to starting state
            self.spaceship.reset_to_start()
            self.level_completed = False
            
            # Reset the timer
            self.timer.start()
            
            print("Level reset successful!")
    
    def handle_menu_input(self):
        """Handle menu input processing"""
        current_time = pygame.time.get_ticks()
        joystick, navigate_up, navigate_down, select, back_to_menu = self.input_manager.process_menu_input()
        
        # Handle menu navigation with debouncing
        if self.input_manager.check_debounced_navigate(navigate_up, current_time):
            self.menu_state.navigate_up()
        elif self.input_manager.check_debounced_navigate(navigate_down, current_time):
            self.menu_state.navigate_down()
        
        # Handle level selection with debouncing
        if self.input_manager.check_debounced_select(select, current_time):
            selected_level = self.menu_state.get_selected_level()
            if selected_level:
                self.switch_to_playing(selected_level)
    
    def handle_game_input(self):
        """Handle game input processing"""
        current_time = pygame.time.get_ticks()
        joystick, thrust, rotate_left, rotate_right, back_to_menu, reset_level = self.input_manager.process_game_input()
        
        # Check for reset level input with debouncing
        if self.input_manager.check_debounced_reset(reset_level, current_time):
            self.reset_current_level()
        
        # Check for back to menu input
        if back_to_menu:
            self.switch_to_menu()
            return
        
        # Apply spaceship controls if level is not completed
        if not self.level_completed and self.spaceship:
            self.spaceship.apply_thrust(thrust)
            self.spaceship.apply_rotation(rotate_left, rotate_right, self.current_level)
    
    def update_gameplay(self, delta_time=1.0):
        """Update gameplay logic with frame-rate independent physics"""
        if not self.level_completed and self.spaceship and self.current_level:
            # Update spaceship physics with delta_time for frame-rate independence
            self.spaceship.update(delta_time)
            
            # Record current spaceship state for ghost system
            if self.ghost_recorder.is_recording():
                self.ghost_recorder.record_frame(self.spaceship)
            
            # Update ghost playback
            if self.ghost_playback.is_playing() and self.ghost:
                current_ghost_frame = self.ghost_playback.get_current_ghost_state()
                self.ghost.update_from_ghost_frame(current_ghost_frame)
            
            # Check for collision with level geometry
            spaceship_image, collision_x, collision_y = self.spaceship.get_collision_rect_info()
            if spaceship_image:
                solid_collision, special_collision = self.current_level.check_spaceship_collisions(
                    spaceship_image, collision_x, collision_y
                )
                
                # Check for target zone collision (special zones)
                if special_collision:
                    self.level_completed = True
                    # Stop recording when level is completed
                    if self.ghost_recorder.is_recording():
                        self.ghost_recorder.stop_recording()
                        print("Level completed - stopped ghost recording")
                    return
                
                # Check for collision
                collision_occurred = False
                collision_reason = ""
                
                # Check screen boundaries
                if not self.spaceship.is_within_screen_bounds(self.screen_width, self.screen_height):
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
                        bounce_x, bounce_y = self.spaceship.get_boundary_collision_type(
                            self.screen_width, self.screen_height
                        )
                    else:
                        # For level geometry collisions, check the prev positions to determine bounce direction
                        prev_x, prev_y = self.spaceship.physics.get_previous_position()
                        
                        # Check prev x position collision
                        prev_collision_x = (prev_x + self.spaceship.renderer.original_image.get_width() // 2 -
                                           spaceship_image.get_width() // 2)
                        solid_collision_x_back, _ = self.current_level.check_spaceship_collisions(
                            spaceship_image, prev_collision_x, collision_y
                        )
                        
                        # Check prev y position collision
                        prev_collision_y = (prev_y + self.spaceship.renderer.original_image.get_height() // 2 -
                                           spaceship_image.get_height() // 2)
                        solid_collision_y_back, _ = self.current_level.check_spaceship_collisions(
                            spaceship_image, collision_x, prev_collision_y
                        )
                        
                        # If moving back in the direction of travel removes collision, bounce in that direction
                        bounce_x = not solid_collision_x_back
                        bounce_y = not solid_collision_y_back
                    
                    # Apply collision handling
                    self.spaceship.handle_collision(bounce_x, bounce_y)
        
        # Update timer only if level not completed
        if not self.level_completed:
            self.timer.update()
    
    def render_current_state(self, screen):
        """Render the current game state"""
        if self.current_state == GameState.MENU:
            self.renderer.render_menu(screen, self.menu_state)
        
        elif self.current_state == GameState.PLAYING:
            if self.current_level is not None:
                # Get current timer text
                timer_text = self.timer.get_formatted_time()
                
                # Render gameplay scene with ghost
                self.renderer.render_gameplay_scene(screen, self.current_level, self.spaceship, timer_text, self.ghost)
    
    def quit(self):
        """Quit the game"""
        self.running = False
    
    def is_running(self):
        """Check if game is still running"""
        return self.running
    
    def get_current_state(self):
        """Get the current game state"""
        return self.current_state
    
    def is_level_completed(self):
        """Check if current level is completed"""
        return self.level_completed