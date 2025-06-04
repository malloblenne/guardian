"""Interface definitions for game components."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import pygame


class AIBehavior(ABC):
    """Interface for enemy AI behaviors."""
    
    @abstractmethod
    def update(self, enemy, player_pos: Tuple[int, int], dt: float):
        """Update AI behavior."""
        pass


class Weapon(ABC):
    """Interface for weapon systems."""
    
    @abstractmethod
    def can_fire(self) -> bool:
        """Check if weapon can fire."""
        pass
    
    @abstractmethod
    def fire(self, position: Tuple[int, int]) -> List[pygame.sprite.Sprite]:
        """Fire the weapon and return bullet sprites."""
        pass


class Enemy(ABC):
    """Interface for enemy entities."""
    
    @abstractmethod
    def set_player_position(self, x: int, y: int):
        """Update the player position for AI."""
        pass
    
    @abstractmethod
    def get_behavior(self) -> AIBehavior:
        """Get the AI behavior."""
        pass


class Controllable(ABC):
    """Interface for controllable entities."""
    
    @abstractmethod
    def process_event(self, event: pygame.event.Event):
        """Process input events."""
        pass
