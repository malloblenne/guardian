"""Base classes for game objects."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import pygame


def create_physical_object_dict(hit_points: int = 1, damage: int = 1, 
                               immortal: bool = False, score_value: int = 0) -> Dict[str, Any]:
    """Create a physical object dictionary (legacy compatibility)."""
    return {
        'hit_points': hit_points,
        'damage': damage,
        'immortal': immortal,
        'score_value': score_value
    }


class PhysicalObject:
    """Represents physical properties of a game object."""
    
    def __init__(self, hit_points: int = 1, damage: int = 1, 
                 immortal: bool = False, score_value: int = 0):
        self.hit_points = hit_points
        self.max_hit_points = hit_points
        self.damage = damage
        self.immortal = immortal
        self.score_value = score_value
    
    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        if self.immortal:
            return False
        
        self.hit_points -= damage
        return self.hit_points <= 0
    
    def heal(self, amount: int):
        """Heal the object."""
        self.hit_points = min(self.hit_points + amount, self.max_hit_points)
    
    def is_alive(self) -> bool:
        """Check if object is still alive."""
        return self.hit_points > 0


class GameObject(pygame.sprite.Sprite, ABC):
    """Base class for all game objects."""
    
    def __init__(self, containers=None):
        if containers:
            super().__init__(containers)
        else:
            super().__init__()
        
        self.physical_obj = PhysicalObject()
        self.x_speed = 0.0
        self.y_speed = 0.0
    
    @abstractmethod
    def update(self):
        """Update the game object."""
        pass
    
    def move(self):
        """Move the object based on its speed."""
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed
    
    def check_bounds(self, screen_width: int, screen_height: int):
        """Keep object within screen bounds."""
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > screen_width - self.rect.width:
            self.rect.x = screen_width - self.rect.width
            
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y > screen_height - self.rect.height:
            self.rect.y = screen_height - self.rect.height
