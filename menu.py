import pygame
import os
from enum import Enum
from level import Level

class GameState(Enum):
    """Enum to track current game state"""
    MENU = "menu"
    PLAYING = "playing"

class LevelInfo:
    """Data structure to hold level information"""
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.thumbnail = None
        self.thumbnail_rect = None

class MenuState:
    """Manages the level selection menu functionality"""
    
    def __init__(self, screen_width, screen_height, scoreboard=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_level_index = 0
        self.levels = []
        self.scoreboard = scoreboard or {}
        
        # Menu display constants
        self.THUMBNAIL_SIZE = (384, 432)  # Thumbnail dimensions (narrower width)
        self.THUMBNAIL_SPACING = 50      # Space between thumbnails
        self.MENU_TITLE_SIZE = 72
        self.LEVEL_NAME_SIZE = 36
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 100, 255)
        self.HIGHLIGHT_COLOR = (255, 255, 0)  # Yellow highlight
        
        # Fonts
        self.title_font = pygame.font.Font(None, self.MENU_TITLE_SIZE)
        self.level_font = pygame.font.Font(None, self.LEVEL_NAME_SIZE)
        
        self.initialize_levels()
    
    def initialize_levels(self):
        """Initialize the available levels"""
        # Add the three levels as specified
        self.levels = [
            LevelInfo("Ryan Level", "ryan_level.png"),
            LevelInfo("John Level", "john_level.png"),
            LevelInfo("Martin Level", "martin_level.png")
        ]
        
        # Generate thumbnails for each level
        for level_info in self.levels:
            self.generate_thumbnail(level_info)
    
    def generate_thumbnail(self, level_info):
        """Generate a thumbnail for a level"""
        if not os.path.exists(level_info.filename):
            print(f"Warning: Level file {level_info.filename} not found")
            # Create a placeholder thumbnail
            level_info.thumbnail = pygame.Surface(self.THUMBNAIL_SIZE)
            level_info.thumbnail.fill(self.BLACK)
            # Add text indicating missing file
            text = self.level_font.render("Missing", True, self.WHITE)
            text_rect = text.get_rect(center=(self.THUMBNAIL_SIZE[0]//2, self.THUMBNAIL_SIZE[1]//2))
            level_info.thumbnail.blit(text, text_rect)
            return
        
        try:
            # Load the level image
            level_image = pygame.image.load(level_info.filename)
            
            # Scale image while preserving aspect ratio
            original_width, original_height = level_image.get_size()
            target_width, target_height = self.THUMBNAIL_SIZE
            
            # Calculate scale factor to fit within thumbnail bounds
            scale_x = target_width / original_width
            scale_y = target_height / original_height
            scale = min(scale_x, scale_y)  # Use smaller scale to fit within bounds
            
            # Calculate new dimensions
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            # Scale the image preserving aspect ratio
            scaled_image = pygame.transform.scale(level_image, (new_width, new_height))
            
            # Create thumbnail surface and center the scaled image
            level_info.thumbnail = pygame.Surface(self.THUMBNAIL_SIZE)
            level_info.thumbnail.fill(self.BLACK)  # Fill background
            
            # Center the scaled image on the thumbnail
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            level_info.thumbnail.blit(scaled_image, (x_offset, y_offset))
            
        except pygame.error as e:
            print(f"Error loading level {level_info.filename}: {e}")
            # Create error placeholder
            level_info.thumbnail = pygame.Surface(self.THUMBNAIL_SIZE)
            level_info.thumbnail.fill((128, 0, 0))  # Dark red for error
    
    def navigate_up(self):
        """Move selection up (previous level)"""
        if self.selected_level_index > 0:
            self.selected_level_index -= 1
    
    def navigate_down(self):
        """Move selection down (next level)"""
        if self.selected_level_index < len(self.levels) - 1:
            self.selected_level_index += 1
    
    def get_selected_level(self):
        """Get the currently selected level info"""
        if 0 <= self.selected_level_index < len(self.levels):
            return self.levels[self.selected_level_index]
        return None
    
    def render(self, screen):
        """Render the menu screen"""
        # Clear screen with black background
        screen.fill(self.BLACK)
        
        # Draw title
        title_text = self.title_font.render("GRAVITATION", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.level_font.render("Select a Level", True, self.WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 180))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Calculate starting position for thumbnails (left side, vertically arranged)
        thumbnail_x = 50  # Fixed position on left side
        start_y = 300
        total_height = len(self.levels) * self.THUMBNAIL_SIZE[1] + (len(self.levels) - 1) * self.THUMBNAIL_SPACING
        
        # Draw thumbnails and level names
        for i, level_info in enumerate(self.levels):
            # Calculate thumbnail position (vertical layout)
            thumbnail_y = start_y + i * (self.THUMBNAIL_SIZE[1] + self.THUMBNAIL_SPACING)
            
            # Create thumbnail rect
            level_info.thumbnail_rect = pygame.Rect(thumbnail_x, thumbnail_y,
                                                   self.THUMBNAIL_SIZE[0], self.THUMBNAIL_SIZE[1])
            
            # Draw highlight border if selected
            if i == self.selected_level_index:
                highlight_rect = level_info.thumbnail_rect.copy()
                highlight_rect.inflate_ip(10, 10)  # Make border 5px wider on each side
                pygame.draw.rect(screen, self.HIGHLIGHT_COLOR, highlight_rect, 5)
            
            # Draw thumbnail
            if level_info.thumbnail:
                screen.blit(level_info.thumbnail, level_info.thumbnail_rect)
            
            # Draw scoreboard information to the right of thumbnail
            scoreboard_y = thumbnail_y + 20
            if self.scoreboard and level_info.name in self.scoreboard:
                level_scores = self.scoreboard[level_info.name]
                if level_scores:
                    # Sort scores by time (assuming time format is comparable as string)
                    sorted_scores = sorted(level_scores.items(), key=lambda x: x[1])
                    
                    # Display individual scores
                    current_y = scoreboard_y
                    for idx, (player, time) in enumerate(sorted_scores[:3]):  # Show top 3
                        score_text = f"{idx + 1}. {player}: {time}"
                        score_surface = self.level_font.render(score_text, True, self.WHITE)
                        score_rect = score_surface.get_rect(left=(thumbnail_x + self.THUMBNAIL_SIZE[0] + 40), top=current_y)
                        screen.blit(score_surface, score_rect)
                        current_y += 25
                else:
                    # No scores yet
                    no_scores_text = self.level_font.render("No scores yet", True, self.BLUE)
                    no_scores_rect = no_scores_text.get_rect(left=(thumbnail_x + self.THUMBNAIL_SIZE[0] + 20), top=scoreboard_y)
                    screen.blit(no_scores_text, no_scores_rect)
            else:
                # Level not in scoreboard
                no_data_text = self.level_font.render("No score data", True, self.BLUE)
                no_data_rect = no_data_text.get_rect(left=(thumbnail_x + self.THUMBNAIL_SIZE[0] + 20), top=scoreboard_y)
                screen.blit(no_data_text, no_data_rect)
        
        # Draw instructions on right side of screen
        instructions = [
            "Use Up/Down Arrow Keys or D-Pad to navigate",
            "Press Enter or X button to select level"
        ]
        
        instruction_x = self.screen_width // 2 + 100
        instruction_y = start_y
        for instruction in instructions:
            instruction_text = self.level_font.render(instruction, True, self.WHITE)
            instruction_rect = instruction_text.get_rect(left=instruction_x, top=instruction_y)
            screen.blit(instruction_text, instruction_rect)
            instruction_y += 50