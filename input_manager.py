import pygame
import platform

class InputManager:
    """Handles input processing for both keyboard and controller with debouncing"""
    
    def __init__(self):
        self.joystick = None
        
        # Input debouncing timers - preserved from original main.py
        self.last_navigate_time = 0
        self.last_select_time = 0
        self.last_reset_time = 0
        
        # Debouncing delays - preserved from original main.py
        self.navigate_delay = 200  # milliseconds between navigation inputs
        self.select_delay = 300    # milliseconds between select inputs
        self.reset_delay = 500     # milliseconds between reset inputs
    
    def setup_controller(self):
        """Setup PS4 controller if not already initialized (matching original logic)"""
        if self.joystick is None and pygame.joystick.get_count() > 0:
            # TODO figure out something more robust to pick the right controller (on mobile especially)
            for i in range(pygame.joystick.get_count()):
                if 'Wireless Controller' in pygame.joystick.Joystick(i).get_name():
                    self.joystick = pygame.joystick.Joystick(i)
                    break
            if self.joystick is not None:
                self.joystick.init()
                platform.console.log(f"Controller detected: {self.joystick.get_name()}")
        
        return self.joystick
    
    def get_controller_inputs(self):
        """Get controller input states (matching original logic)"""
        controller_action1 = False  # Thrust in game, Select in menu
        controller_left = False
        controller_right = False
        controller_up = False
        controller_down = False
        controller_action2 = False  # Back to menu (Circle button)
        controller_reset = False    # Reset (Triangle button)
        
        if self.joystick is not None:
            # PS4 X button for main action (button 0)
            controller_action1 = self.joystick.get_button(0)
            
            # PS4 Circle button for secondary action (button 1) - back to menu
            try:
                controller_action2 = self.joystick.get_button(1)
            except:
                controller_action2 = False
            
            # PS4 Triangle button for reset (button 2)
            try:
                controller_reset = self.joystick.get_button(2)
            except:
                controller_reset = False
            
            # Use left analog stick for navigation
            left_stick_x = self.joystick.get_axis(0)  # left/right axis
            left_stick_y = self.joystick.get_axis(1)  # up/down axis
            
            # Use D-pad for navigation as well
            try:
                dpad_left = self.joystick.get_button(14)
                dpad_right = self.joystick.get_button(15)
                dpad_up = self.joystick.get_button(12)
                dpad_down = self.joystick.get_button(13)
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
        
        return (controller_action1, controller_action2, controller_reset,
                controller_left, controller_right, controller_up, controller_down)
    
    def process_menu_input(self):
        """Process menu input (matching original logic exactly)"""
        # Setup controller
        self.joystick = self.setup_controller()
        
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        
        # Get controller inputs
        (controller_action1, controller_action2, controller_reset,
         controller_left, controller_right, controller_up, controller_down) = self.get_controller_inputs()
        
        # Menu input handling (up/down navigation for vertical layout)
        navigate_up = keys[pygame.K_UP] or controller_up
        navigate_down = keys[pygame.K_DOWN] or controller_down
        select = keys[pygame.K_RETURN] or controller_action1
        back_to_menu = keys[pygame.K_ESCAPE] or controller_action2
        
        return self.joystick, navigate_up, navigate_down, select, back_to_menu
    
    def process_game_input(self):
        """Process game input (matching original logic exactly)"""
        # Setup controller
        self.joystick = self.setup_controller()
        
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        
        # Get controller inputs
        (controller_action1, controller_action2, controller_reset,
         controller_left, controller_right, controller_up, controller_down) = self.get_controller_inputs()
        
        # Game input handling
        thrust = keys[pygame.K_UP] or controller_action1
        rotate_left = keys[pygame.K_LEFT] or controller_left
        rotate_right = keys[pygame.K_RIGHT] or controller_right
        back_to_menu = keys[pygame.K_ESCAPE] or controller_action2
        reset_level = keys[pygame.K_r] or controller_reset  # R key + Triangle button
        
        return self.joystick, thrust, rotate_left, rotate_right, back_to_menu, reset_level
    
    def check_debounced_navigate(self, navigate_input, current_time):
        """Check if navigation input should be processed (with debouncing)"""
        if navigate_input and current_time - self.last_navigate_time > self.navigate_delay:
            self.last_navigate_time = current_time
            return True
        return False
    
    def check_debounced_select(self, select_input, current_time):
        """Check if select input should be processed (with debouncing)"""
        if select_input and current_time - self.last_select_time > self.select_delay:
            self.last_select_time = current_time
            return True
        return False
    
    def check_debounced_reset(self, reset_input, current_time):
        """Check if reset input should be processed (with debouncing)"""
        if reset_input and current_time - self.last_reset_time > self.reset_delay:
            self.last_reset_time = current_time
            return True
        return False