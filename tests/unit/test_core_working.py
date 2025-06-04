"""Test core components functionality."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_config_loading():
    """Test configuration loading."""
    from config.config_loader import ConfigLoader, get_config
    
    # Test that config can be loaded
    config = get_config()
    assert config is not None
    assert hasattr(config, 'sprite_sheets')
    assert hasattr(config, 'enemy_types')
    assert hasattr(config, 'player')


def test_enemy_factory():
    """Test enemy factory."""
    import pygame
    pygame.init()
    # Set a display mode for sprite loading
    pygame.display.set_mode((1, 1))
    
    from factories.enemy_factory import EnemyFactory
    
    # Test creating enemies
    spaceship = EnemyFactory.create_small_spaceship()
    assert spaceship is not None
    assert hasattr(spaceship, 'physical_obj')
    
    whale = EnemyFactory.create_whale_boss()
    assert whale is not None
    assert hasattr(whale, 'physical_obj')
    
    pygame.quit()


def test_ai_behaviors():
    """Test AI behavior classes."""
    import pygame
    pygame.init()
    
    from systems.ai_behaviors import ChasePlayerAI, CircularChaseAI
    
    # Create AI instances
    chase_ai = ChasePlayerAI()
    assert chase_ai is not None
    
    circular_ai = CircularChaseAI()
    assert circular_ai is not None


def test_pi_controller():
    """Test PI controller."""
    from systems.controllers import PIController
    
    controller = PIController(kp=1.0, ki=0.1)
    assert controller is not None
    
    # Test control method
    error = 10.0
    output = controller.control(error)
    assert isinstance(output, float)
