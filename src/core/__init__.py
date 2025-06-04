"""Core game entities and interfaces."""

from core.base import GameObject, PhysicalObject
from core.interfaces import Enemy, Weapon, AIBehavior
from core.sprite_manager import SpriteManager

__all__ = [
    'GameObject', 
    'PhysicalObject', 
    'Enemy', 
    'Weapon', 
    'AIBehavior', 
    'SpriteManager'
]
