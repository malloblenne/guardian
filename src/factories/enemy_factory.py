"""Enemy factory for creating different types of enemies."""

import random
from typing import Optional
from entities.enemies import SmallSpaceship, WhaleBoss
from config import get_config, get_enemy_config


class EnemyFactory:
    """Factory for creating enemy instances."""
    
    @staticmethod
    def create_small_spaceship() -> SmallSpaceship:
        """Create a small spaceship enemy."""
        enemy = SmallSpaceship()
        config = get_config()
        screen_width = config.game['screen']['width']
        enemy.rect.x = random.randint(0, screen_width - enemy.rect.width)
        return enemy
    
    @staticmethod
    def create_whale_boss() -> WhaleBoss:
        """Create a whale boss enemy."""
        enemy = WhaleBoss()
        config = get_config()
        screen_width = config.game['screen']['width']
        enemy.rect.x = random.randint(0, screen_width - enemy.rect.width)
        return enemy
    
    @staticmethod
    def create_enemy(enemy_type: str) -> Optional[object]:
        """Create an enemy by type name."""
        if enemy_type == 'small_spaceship':
            return EnemyFactory.create_small_spaceship()
        elif enemy_type == 'whale_boss':
            return EnemyFactory.create_whale_boss()
        else:
            raise ValueError(f"Unknown enemy type: {enemy_type}")
    
    @staticmethod
    def create_random_enemy(score: int = 0) -> object:
        """Create a random enemy based on game state."""
        # Boss can only spawn when score is high
        if score < 50:
            return EnemyFactory.create_small_spaceship()
        elif random.random() < 0.95:
            return EnemyFactory.create_small_spaceship()
        else:
            return EnemyFactory.create_whale_boss()


# Convenience functions (legacy compatibility)
def add_enemy():
    """Create an instance of a small enemy."""
    return EnemyFactory.create_small_spaceship()


def add_whale():
    """Create an instance of a whale boss."""
    return EnemyFactory.create_whale_boss()
