import pygame

class GameTimer:
    """Manages game timing functionality"""
    
    def __init__(self):
        self.start_time = 0
        self.current_time = 0
        self.is_running = False
    
    def start(self):
        """Start the timer"""
        self.start_time = pygame.time.get_ticks()
        self.current_time = 0
        self.is_running = True
    
    def stop(self):
        """Stop the timer"""
        self.is_running = False
    
    def update(self):
        """Update the timer if it's running"""
        if self.is_running:
            self.current_time = pygame.time.get_ticks() - self.start_time
    
    def get_current_time_ms(self):
        """Get the current time in milliseconds"""
        return self.current_time
    
    def get_formatted_time(self):
        """
        Convert current time to MM:SS.ms format (matching original format_timer function).
        
        Returns:
            str: Formatted time string in MM:SS.ms format
        """
        return self.format_timer(self.current_time)
    
    @staticmethod
    def format_timer(milliseconds):
        """
        Convert milliseconds to MM:SS.ms format (preserved from original main.py).
        
        Args:
            milliseconds: Time in milliseconds
            
        Returns:
            str: Formatted time string in MM:SS.ms format
        """
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        ms = milliseconds % 1000
        return f"{minutes:02d}:{seconds:02d}.{ms:03d}"