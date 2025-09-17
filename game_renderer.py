import pygame

class GameRenderer:
    """Handles all game rendering operations"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Colors - preserved from original main.py
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREY = (128, 128, 128)
        
        # Timer font - preserved from original main.py
        self.timer_font = pygame.font.Font(None, 48)
    
    def clear_screen(self, screen):
        """Clear the screen with black background"""
        screen.fill(self.BLACK)
    
    def render_level_background(self, screen, level):
        """Render the level background"""
        if level:
            screen.blit(level.get_visual_surface(), (0, 0))
    
    def render_spaceship(self, screen, spaceship):
        """Render the spaceship"""
        if spaceship and spaceship.renderer.get_image() and spaceship.renderer.get_rect():
            screen.blit(spaceship.renderer.get_image(), spaceship.renderer.get_rect())
    
    def render_ghost(self, screen, ghost):
        """Render the ghost spaceship with transparency"""
        if ghost and ghost.is_visible() and ghost.renderer.get_image() and ghost.renderer.get_rect():
            screen.blit(ghost.renderer.get_image(), ghost.renderer.get_rect())
    
    def render_timer(self, screen, timer_text):
        """Render the timer in top-right corner with black background (matching original)"""
        # Render timer text
        timer_surface = self.timer_font.render(timer_text, True, self.WHITE)
        timer_rect = timer_surface.get_rect()
        timer_rect.topright = (self.screen_width - 20, 20)  # 20px padding from edges
        
        # Draw black background rectangle for better text readability (matching original)
        background_padding = 8
        background_rect = timer_rect.copy()
        background_rect.inflate_ip(background_padding * 2, background_padding * 2)
        pygame.draw.rect(screen, self.BLACK, background_rect)
        
        # Draw the timer text on top of the black background
        screen.blit(timer_surface, timer_rect)
    
    def render_menu(self, screen, menu_state):
        """Render the menu (delegated to MenuState)"""
        if menu_state:
            menu_state.render(screen)
    
    def render_level_completion_overlay(self, screen):
        """Render level completion overlay (matching original)"""
        # Show completion message
        completion_text = self.timer_font.render("Level Complete! Returning to menu...", True, self.WHITE)
        completion_rect = completion_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        
        # Draw completion overlay (matching original)
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill(self.BLACK)
        screen.blit(overlay, (0, 0))
        screen.blit(completion_text, completion_rect)
    
    def render_gameplay_scene(self, screen, level, spaceship, timer_text, ghost=None):
        """Render the complete gameplay scene"""
        # Clear screen
        self.clear_screen(screen)
        
        # Render level background
        self.render_level_background(screen, level)
        
        # Render ghost first (behind the player spaceship)
        if ghost:
            self.render_ghost(screen, ghost)
        
        # Render spaceship (on top of ghost)
        self.render_spaceship(screen, spaceship)
        
        # Render timer
        self.render_timer(screen, timer_text)
    
    def update_display(self):
        """Update the pygame display"""
        pygame.display.flip()