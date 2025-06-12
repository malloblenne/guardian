"""Sprite management and loading system."""

import os
import pygame
from typing import Dict, Optional, Tuple
from config import get_config


class SpriteSheet:
    """Utility class for loading and parsing a sprite sheet image."""
    
    def __init__(self, filename: str, color_key: Optional[Tuple[int, int, int]] = None):
        """Load the sprite sheet."""
        try:
            self.sprite_sheet = pygame.image.load(filename).convert()
        except pygame.error as message:
            print(f'Unable to load spritesheet image: {filename}')
            raise SystemExit(message)
        
        if color_key:
            self.sprite_sheet.set_colorkey(color_key)

    def get_image(self, x: int, y: int, width: int, height: int) -> pygame.Surface:
        """Get a specific image from the sprite sheet."""
        image = pygame.Surface([width, height]).convert()
        image.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
        image.set_colorkey((0, 0, 0))  # Assume black is transparent
        return image


class SpriteManager:
    """Manages sprite loading and caching."""
    
    def __init__(self):
        self._sprite_sheets: Dict[str, SpriteSheet] = {}
        self._sprites: Dict[str, pygame.Surface] = {}
        self._config = get_config()
    
    def get_sprite_sheet(self, sheet_name: str) -> SpriteSheet:
        """Get or load a sprite sheet."""
        if sheet_name not in self._sprite_sheets:
            sheet_config = self._config.sprite_sheets[sheet_name]
            self._sprite_sheets[sheet_name] = SpriteSheet(
                sheet_config.file, 
                sheet_config.color_key
            )
        return self._sprite_sheets[sheet_name]
    
    def get_sprite(self, sheet_name: str, sprite_name: str) -> pygame.Surface:
        """Get a specific sprite."""
        cache_key = f"{sheet_name}:{sprite_name}"
        
        if cache_key not in self._sprites:
            sheet_config = self._config.sprite_sheets[sheet_name]
            sprite_config = sheet_config.sprites[sprite_name]
            
            sprite_sheet = self.get_sprite_sheet(sheet_name)
            self._sprites[cache_key] = sprite_sheet.get_image(
                sprite_config.x,
                sprite_config.y, 
                sprite_config.width,
                sprite_config.height
            )
        
        return self._sprites[cache_key]
    
    def get_flipped_sprite(self, sheet_name: str, sprite_name: str, 
                          flip_x: bool = False, flip_y: bool = False) -> pygame.Surface:
        """Get a flipped version of a sprite."""
        cache_key = f"{sheet_name}:{sprite_name}:flip_{flip_x}_{flip_y}"
        
        if cache_key not in self._sprites:
            original = self.get_sprite(sheet_name, sprite_name)
            self._sprites[cache_key] = pygame.transform.flip(original, flip_x, flip_y)
        
        return self._sprites[cache_key]


# Global sprite manager instance
_sprite_manager = SpriteManager()


def get_sprite_manager() -> SpriteManager:
    """Get the global sprite manager."""
    return _sprite_manager


def get_sprite(sheet_name: str, sprite_name: str) -> pygame.Surface:
    """Shortcut to get a sprite."""
    return _sprite_manager.get_sprite(sheet_name, sprite_name)


def get_flipped_sprite(sheet_name: str, sprite_name: str, 
                      flip_x: bool = False, flip_y: bool = False) -> pygame.Surface:
    """Shortcut to get a flipped sprite."""
    return _sprite_manager.get_flipped_sprite(sheet_name, sprite_name, flip_x, flip_y)
