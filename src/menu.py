import pygame
import os
from enum import Enum
from src.level import Level

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
        
        # Load logo
        self.logo = None
        self.logo_size = 540  # Size to scale logo to (50% larger than 360)
        if os.path.exists("assets/images/logo/fist.png"):
            try:
                logo_image = pygame.image.load("assets/images/logo/fist.png")
                self.logo = pygame.transform.scale(logo_image, (self.logo_size, self.logo_size))
            except pygame.error as e:
                print(f"Error loading logo: {e}")
        
        self.initialize_levels()
    
    def initialize_levels(self):
        """Initialize the available levels"""
        # Add the four levels as specified
        self.levels = [
            LevelInfo("Ryan Level", "assets/images/levels/ryan_level.png"),
            LevelInfo("John Level", "assets/images/levels/john_level.png"),
            LevelInfo("Martin Level", "assets/images/levels/martin_level.png"),
            LevelInfo("Slalom Level", "assets/images/levels/slalom.png")
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
    
    def calculate_overall_rankings(self):
        """Calculate overall rankings based on points from top 3 placements in each level
        
        Returns:
            List of tuples: (rank, player_name, total_points, levels_completed)
        """
        # Points awarded for rankings: 1st=3pts, 2nd=2pts, 3rd=1pt
        RANKING_POINTS = {0: 3, 1: 2, 2: 1}
        
        # Dictionary to track each player's points and level participation
        player_stats = {}  # {player_name: {'points': int, 'levels': set()}}
        
        # Iterate through all levels in the scoreboard
        for level_info in self.levels:
            level_name = level_info.name
            
            # Skip if level not in scoreboard or has no scores
            if level_name not in self.scoreboard or not self.scoreboard[level_name]:
                continue
            
            # Get scores for this level and sort by time
            level_scores = self.scoreboard[level_name]
            sorted_players = sorted(level_scores.items(), key=lambda x: x[1])
            
            # Award points to top 3 players
            for rank, (player, time) in enumerate(sorted_players[:3]):
                if player not in player_stats:
                    player_stats[player] = {'points': 0, 'levels': set()}
                
                # Add points for this ranking
                player_stats[player]['points'] += RANKING_POINTS[rank]
                # Track that this player completed this level
                player_stats[player]['levels'].add(level_name)
        
        # Convert to list of tuples with rankings
        rankings = []
        for player, stats in player_stats.items():
            rankings.append((
                player,
                stats['points'],
                len(stats['levels'])
            ))
        
        # Sort by points (descending), then by levels completed (descending) as tiebreaker
        rankings.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Add rank numbers
        final_rankings = []
        for idx, (player, points, levels_completed) in enumerate(rankings):
            final_rankings.append((idx + 1, player, points, levels_completed))
        
        return final_rankings
    
    def render_overall_leaderboard(self, screen):
        """Render the overall leaderboard at the top of the menu"""
        # Calculate rankings
        rankings = self.calculate_overall_rankings()
        
        # Skip rendering if no rankings
        if not rankings:
            return
        
        # Position below the title
        leaderboard_x = self.screen_width // 2
        leaderboard_y = 180  # Below title
        
        # Title for overall leaderboard
        overall_title = self.level_font.render("Overall Leaderboard", True, self.HIGHLIGHT_COLOR)
        overall_title_rect = overall_title.get_rect(center=(leaderboard_x, leaderboard_y))
        screen.blit(overall_title, overall_title_rect)
        
        # Render each player's ranking
        current_y = leaderboard_y + 40
        line_height = 30
        
        for rank, player, points, levels_completed in rankings:
            # Format: 1. PlayerName: 12 pts (4 levels)
            ranking_text = f"{rank}. {player}: {points} pts ({levels_completed} levels)"
            ranking_surface = self.level_font.render(ranking_text, True, self.WHITE)
            ranking_rect = ranking_surface.get_rect(center=(leaderboard_x, current_y))
            screen.blit(ranking_surface, ranking_rect)
            current_y += line_height
    
    def render(self, screen):
        """Render the menu screen"""
        # Clear screen with black background
        screen.fill(self.BLACK)
        
        # Draw title
        title_text = self.title_font.render("Fist Contact", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Draw logo on both sides of title (larger and closer to screen edges)
        if self.logo:
            # Left logo - positioned near left edge and lower down
            left_logo_x = 30  # 50px from left edge
            left_logo_y = 0  # Positioned lower (was centered at 100)
            screen.blit(self.logo, (left_logo_x, left_logo_y))
            
            # Right logo - positioned near right edge and lower down
            right_logo_x = self.screen_width - self.logo_size - 30  # 50px from right edge
            right_logo_y = 0  # Positioned lower (was centered at 100)
            screen.blit(self.logo, (right_logo_x, right_logo_y))
        
        # Render overall leaderboard
        self.render_overall_leaderboard(screen)
        
        # Calculate starting position for thumbnails (left side, vertically arranged)
        thumbnail_x = 50  # Fixed position on left side
        start_y = 500  # Moved down to avoid overlap with leaderboard
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