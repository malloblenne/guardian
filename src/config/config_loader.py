"""Configuration loader for sprites and game settings."""

import os
import yaml
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass
import pygame


@dataclass
class SpriteConfig:
    """Configuration for a single sprite."""
    x: int
    y: int
    width: int
    height: int
    
    def as_rect(self) -> Tuple[int, int, int, int]:
        """Return as pygame rect tuple."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class SpriteSheetConfig:
    """Configuration for a sprite sheet."""
    file: str
    color_key: Optional[Tuple[int, int, int]]
    sprites: Dict[str, SpriteConfig]


@dataclass
class EnemyTypeConfig:
    """Configuration for an enemy type."""
    sprite_sheet: str
    sprites: Dict[str, str]  # animation states -> sprite names
    hp: int
    damage: int
    score_value: int
    speed: float
    ai_type: str
    fire_interval: int


@dataclass
class PlayerConfig:
    """Configuration for the player."""
    sprite_sheet: str
    sprites: Dict[str, str]
    hp: int
    damage: int
    speed: int
    immortality_interval: int
    max_bullets: int


@dataclass
class GameConfig:
    """Complete game configuration."""
    sprite_sheets: Dict[str, SpriteSheetConfig]
    enemy_types: Dict[str, EnemyTypeConfig]
    player: PlayerConfig
    ui: Dict[str, Any]
    audio: Dict[str, Any]
    game: Dict[str, Any]


class ConfigLoader:
    """Loader for YAML configuration files."""
    
    def __init__(self, config_path: str = "config/sprites.yaml"):
        """Initialize with config file path."""
        self.config_path = config_path
        self._config: Optional[GameConfig] = None
    
    def load_config(self) -> GameConfig:
        """Load configuration from YAML file."""
        if self._config is not None:
            return self._config
            
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        
        # Parse sprite sheets
        sprite_sheets = {}
        for sheet_name, sheet_data in data.get('sprite_sheets', {}).items():
            sprites = {}
            for sprite_name, coords in sheet_data.get('sprites', {}).items():
                sprites[sprite_name] = SpriteConfig(*coords)
            
            sprite_sheets[sheet_name] = SpriteSheetConfig(
                file=sheet_data['file'],
                color_key=tuple(sheet_data.get('color_key', [])) if sheet_data.get('color_key') else None,
                sprites=sprites
            )
        
        # Parse enemy types
        enemy_types = {}
        for enemy_name, enemy_data in data.get('enemy_types', {}).items():
            enemy_types[enemy_name] = EnemyTypeConfig(
                sprite_sheet=enemy_data['sprite_sheet'],
                sprites=enemy_data['sprites'],
                hp=enemy_data['hp'],
                damage=enemy_data['damage'],
                score_value=enemy_data['score_value'],
                speed=enemy_data['speed'],
                ai_type=enemy_data['ai_type'],
                fire_interval=enemy_data['fire_interval']
            )
        
        # Parse player config
        player_data = data.get('player', {})
        player = PlayerConfig(
            sprite_sheet=player_data['sprite_sheet'],
            sprites=player_data['sprites'],
            hp=player_data['hp'],
            damage=player_data['damage'],
            speed=player_data['speed'],
            immortality_interval=player_data['immortality_interval'],
            max_bullets=player_data['max_bullets']
        )
        
        self._config = GameConfig(
            sprite_sheets=sprite_sheets,
            enemy_types=enemy_types,
            player=player,
            ui=data.get('ui', {}),
            audio=data.get('audio', {}),
            game=data.get('game', {})
        )
        
        return self._config
    
    def get_sprite_config(self, sheet_name: str, sprite_name: str) -> SpriteConfig:
        """Get configuration for a specific sprite."""
        config = self.load_config()
        if sheet_name not in config.sprite_sheets:
            raise ValueError(f"Sprite sheet '{sheet_name}' not found")
        
        sheet = config.sprite_sheets[sheet_name]
        if sprite_name not in sheet.sprites:
            raise ValueError(f"Sprite '{sprite_name}' not found in sheet '{sheet_name}'")
        
        return sheet.sprites[sprite_name]
    
    def get_enemy_config(self, enemy_type: str) -> EnemyTypeConfig:
        """Get configuration for a specific enemy type."""
        config = self.load_config()
        if enemy_type not in config.enemy_types:
            raise ValueError(f"Enemy type '{enemy_type}' not found")
        
        return config.enemy_types[enemy_type]


# Global config loader instance
_config_loader = ConfigLoader()


def get_config() -> GameConfig:
    """Get the global game configuration."""
    return _config_loader.load_config()


def get_sprite_config(sheet_name: str, sprite_name: str) -> SpriteConfig:
    """Get sprite configuration shortcut."""
    return _config_loader.get_sprite_config(sheet_name, sprite_name)


def get_enemy_config(enemy_type: str) -> EnemyTypeConfig:
    """Get enemy configuration shortcut."""
    return _config_loader.get_enemy_config(enemy_type)
