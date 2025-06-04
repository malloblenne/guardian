"""Sprite factory for creating sprites and managing sprite sheets."""

import pygame
from typing import Dict, Optional, Tuple
from core.sprite_manager import SpriteManager, get_sprite_manager
from config import get_config


class SpriteFactory:
    """Factory for creating sprites and managing sprite resources."""
    
    def __init__(self):
        self.sprite_manager = get_sprite_manager()
        self.config = get_config()
    
    def create_player_sprites(self) -> Dict[str, pygame.Surface]:
        """Create all player sprites."""
        player_config = self.config.player
        sheet_name = player_config.sprite_sheet
        
        sprites = {}
        for state, sprite_name in player_config.sprites.items():
            if state == 'right':
                # Right sprite is flipped from left
                sprites[state] = self.sprite_manager.get_flipped_sprite(
                    sheet_name, player_config.sprites['left'], True, False
                )
            else:
                sprites[state] = self.sprite_manager.get_sprite(sheet_name, sprite_name)
        
        return sprites
    
    def create_enemy_sprites(self, enemy_type: str) -> Dict[str, pygame.Surface]:
        """Create sprites for a specific enemy type."""
        enemy_config = self.config.enemy_types[enemy_type]
        sheet_name = enemy_config.sprite_sheet
        
        sprites = {}
        for state, sprite_name in enemy_config.sprites.items():
            if state == 'left' and sprite_name == 'small_ship_left':
                # Left sprite is flipped from right for small ships
                sprites[state] = self.sprite_manager.get_flipped_sprite(
                    sheet_name, enemy_config.sprites['right'], True, False
                )
            else:
                sprites[state] = self.sprite_manager.get_sprite(sheet_name, sprite_name)
        
        return sprites
    
    def create_bullet_sprite(self, bullet_type: str = 'player') -> pygame.Surface:
        """Create a bullet sprite."""
        if bullet_type == 'player':
            return self.sprite_manager.get_sprite('bullets', 'player_bullet')
        else:
            # Default enemy bullet (can be expanded)
            return self.create_circle_bullet((255, 0, 0), 4)
    
    def create_circle_bullet(self, color: Tuple[int, int, int], radius: int, 
                           width: int = 0) -> pygame.Surface:
        """Create a circular bullet sprite."""
        surface = pygame.Surface([2 * radius, 2 * radius])
        surface.fill((0, 0, 0))
        pygame.draw.circle(surface, color, (radius, radius), radius, width)
        surface.set_colorkey((0, 0, 0))
        return surface
    
    def get_ui_sprite(self, sprite_name: str) -> pygame.Surface:
        """Get a UI sprite."""
        # For now, assume UI sprites are in the startup sheet
        return self.sprite_manager.get_sprite('startup', sprite_name)


# Global sprite factory instance
_sprite_factory = SpriteFactory()


def get_sprite_factory() -> SpriteFactory:
    """Get the global sprite factory."""
    return _sprite_factory
