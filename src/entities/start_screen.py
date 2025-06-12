"""Start screen entity implementation."""

import os
import pygame
from core.base import GameObject
from core.sprite_manager import get_sprite
from config import get_config


class StartScreen(GameObject):
    """Start screen implementation."""
    
    def __init__(self):
        super().__init__()
        
        config = get_config()
        ui_config = config.ui['start_screen']
        
        # Load logo sprite
        self.logo = get_sprite(ui_config['sprite_sheet'], ui_config['logo_sprite'])
        self.logo_rect = self.logo.get_rect()
        self.logo_rect.x, self.logo_rect.y = ui_config['logo_position']
        
        # Create a surface for the entire start screen
        screen_width = config.game['screen']['width']
        screen_height = config.game['screen']['height']
        self.image = pygame.Surface([screen_width, screen_height])
        self.image.fill((0, 0, 0))  # Black background
        
        # Blit logo onto the start screen
        self.image.blit(self.logo, self.logo_rect)
        
        self.rect = self.image.get_rect()
        
        # Music state
        self.music_playing = False
    
    def play_music(self):
        """Start playing title music."""
        if pygame.mixer and not self.music_playing:
            try:
                config = get_config()
                music_file = config.audio['music']['title']
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                self.music_playing = True
            except pygame.error:
                # Music file not found or couldn't load
                pass
    
    def stop_music(self):
        """Stop playing title music."""
        if pygame.mixer and self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False
    
    def update(self):
        """Update start screen (no movement)."""
        pass
