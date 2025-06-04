"""Bullet entity implementations."""

import pygame
from typing import Optional
from core.base import GameObject, create_physical_object_dict
from config import get_config


class Bullet(GameObject):
    """Base bullet class for enemy bullets."""
    
    def __init__(self, enemy: bool = True, x_speed: float = 0, y_speed: float = 4, 
                 image: Optional[pygame.Surface] = None):
        super().__init__(getattr(Bullet, 'containers', None))
        
        self.physical_obj = create_physical_object_dict(hit_points=1, damage=1)
        
        if image:
            self.image = image
        else:
            # Create default circular bullet
            self.image = pygame.Surface([8, 8])
            pygame.draw.circle(self.image, (255, 0, 0), (4, 4), 4)
            self.image.set_colorkey((0, 0, 0))
        
        self.rect = self.image.get_rect()
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.enemy = enemy
    
    def update(self):
        """Update bullet position."""
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed
        
        # Remove if off screen
        config = get_config()
        screen_width = config.game['screen']['width']
        screen_height = config.game['screen']['height']
        
        if (self.rect.y < -10 or self.rect.y > screen_height + 10 or
            self.rect.x < -10 or self.rect.x > screen_width + 10):
            self.kill()


class PlayerBullet(GameObject):
    """Player bullet implementation."""
    
    def __init__(self, image: Optional[pygame.Surface] = None):
        super().__init__(getattr(PlayerBullet, 'containers', None))
        
        self.physical_obj = create_physical_object_dict(hit_points=1, damage=1)
        
        if image:
            self.image = image
        else:
            # Default player bullet appearance
            self.image = pygame.Surface([4, 10])
            self.image.fill((0, 255, 0))
            self.image.set_colorkey((0, 0, 0))
        
        self.rect = self.image.get_rect()
        self.y_speed = -8  # Player bullets go up
    
    def update(self):
        """Update bullet position."""
        self.rect.y += self.y_speed
        
        # Remove if off screen (top)
        if self.rect.y < -10:
            self.kill()
