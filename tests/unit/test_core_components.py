"""Unit tests for the Guardian game refactoring."""

import pytest
import pygame
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config_loader import ConfigLoader, GameConfig
from core.base import GameObject, PhysicalObject, create_physical_object_dict
from systems.ai_behaviors import ChasePlayerAI, CircularChaseAI
from systems.controllers import PIController
from factories.enemy_factory import EnemyFactory


class TestConfigLoader:
    """Test the configuration loading system."""
    
    def test_config_loader_creation(self):
        """Test that ConfigLoader can be created."""
        config_loader = ConfigLoader("config/sprites.yaml")
        assert config_loader is not None
    
    def test_config_loading(self):
        """Test loading configuration from YAML."""
        # This test requires the actual config file
        if os.path.exists("config/sprites.yaml"):
            config_loader = ConfigLoader("config/sprites.yaml")
            config = config_loader.load_config()
            assert isinstance(config, GameConfig)
            assert len(config.sprite_sheets) > 0
            assert len(config.enemy_types) > 0
    
    def test_sprite_config_access(self):
        """Test accessing sprite configurations."""
        if os.path.exists("config/sprites.yaml"):
            config_loader = ConfigLoader("config/sprites.yaml")
            
            # Should not raise exception
            sprite_config = config_loader.get_sprite_config("the_guardian", "player_normal")
            assert sprite_config.x >= 0
            assert sprite_config.y >= 0
            assert sprite_config.width > 0
            assert sprite_config.height > 0


class TestPhysicalObject:
    """Test the PhysicalObject class."""
    
    def test_physical_object_creation(self):
        """Test creating a physical object."""
        obj = PhysicalObject(hit_points=10, damage=2)
        assert obj.hit_points == 10
        assert obj.max_hit_points == 10
        assert obj.damage == 2
        assert not obj.immortal
    
    def test_take_damage(self):
        """Test taking damage."""
        obj = PhysicalObject(hit_points=10)
        
        # Normal damage
        destroyed = obj.take_damage(3)
        assert obj.hit_points == 7
        assert not destroyed
        
        # Lethal damage
        destroyed = obj.take_damage(10)
        assert obj.hit_points <= 0
        assert destroyed
    
    def test_immortal_object(self):
        """Test immortal objects don't take damage."""
        obj = PhysicalObject(hit_points=10, immortal=True)
        destroyed = obj.take_damage(20)
        assert obj.hit_points == 10
        assert not destroyed
    
    def test_healing(self):
        """Test healing functionality."""
        obj = PhysicalObject(hit_points=10)
        obj.take_damage(5)
        assert obj.hit_points == 5
        
        obj.heal(3)
        assert obj.hit_points == 8
        
        # Can't heal above max
        obj.heal(10)
        assert obj.hit_points == 10


class TestLegacyCompatibility:
    """Test legacy compatibility functions."""
    
    def test_create_physical_object_dict(self):
        """Test legacy physical object dict creation."""
        obj_dict = create_physical_object_dict(hit_points=5, damage=2, immortal=True)
        assert obj_dict['hit_points'] == 5
        assert obj_dict['damage'] == 2
        assert obj_dict['immortal'] is True
        assert obj_dict['score_value'] == 0


class TestPIController:
    """Test the PI controller."""
    
    def test_pi_controller_creation(self):
        """Test creating a PI controller."""
        controller = PIController(kp=1.0, ki=0.1)
        assert controller.kp == 1.0
        assert controller.ki == 0.1
        assert controller.integral == 0.0
    
    def test_pi_control_output(self):
        """Test PI controller output."""
        controller = PIController(kp=1.0, ki=0.0)  # Pure proportional
        
        # With kp=1.0 and no integral, output should equal error
        output = controller.control(5.0)
        assert output == 5.0
        
        output = controller.control(-3.0)
        assert output == -3.0
    
    def test_pi_integral_term(self):
        """Test PI controller integral term."""
        controller = PIController(kp=0.0, ki=1.0)  # Pure integral
        
        # Integral should accumulate
        controller.control(2.0)
        output = controller.control(3.0)
        assert output == 5.0  # 2 + 3
    
    def test_anti_windup(self):
        """Test anti-windup functionality."""
        controller = PIController(kp=0.0, ki=1.0, anti_windup=10.0)
        
        # Build up large integral
        for _ in range(20):
            controller.control(5.0)
        
        # Integral should be clamped
        assert abs(controller.integral) <= 10.0


class TestAIBehaviors:
    """Test AI behavior implementations."""
    
    class MockEnemy:
        """Mock enemy for testing AI."""
        def __init__(self):
            self.rect = type('MockRect', (), {'x': 100, 'y': 100, 'width': 20, 'height': 20})()
            self.x_speed = 0
            self.y_speed = 0
    
    def test_chase_ai_creation(self):
        """Test creating chase AI."""
        ai = ChasePlayerAI(max_speed=5.0)
        assert ai.max_speed == 5.0
        assert ai.update_count == 0
    
    def test_chase_ai_update(self):
        """Test chase AI update."""
        ai = ChasePlayerAI(max_speed=10.0)
        enemy = self.MockEnemy()
        
        # Player at (200, 200), enemy at (100, 100)
        ai.update(enemy, (200, 200), 1.0/60.0)
        
        # Enemy should move towards player
        assert enemy.x_speed > 0  # Moving right towards player
        assert abs(enemy.x_speed) <= 10.0  # Within speed limit
        assert abs(enemy.y_speed) <= 10.0  # Within speed limit
    
    def test_circular_chase_ai_creation(self):
        """Test creating circular chase AI."""
        ai = CircularChaseAI(max_speed=5.0)
        assert ai.max_speed == 5.0
        assert ai.behavior == 0
        assert ai.behavior_timer == 0


class TestEnemyFactory:
    """Test the enemy factory."""
    
    def test_factory_methods_exist(self):
        """Test that factory methods exist."""
        factory = EnemyFactory()
        assert hasattr(factory, 'create_small_spaceship')
        assert hasattr(factory, 'create_whale_boss')
        assert hasattr(factory, 'create_enemy')
        assert hasattr(factory, 'create_random_enemy')
    
    def test_create_enemy_by_type(self):
        """Test creating enemies by type."""
        # Note: This test would require pygame initialization and config loading
        # For now, just test that the method exists and raises appropriate errors
        factory = EnemyFactory()
        
        with pytest.raises(ValueError):
            factory.create_enemy('unknown_type')


class MockGameObject(GameObject):
    """Mock game object for testing."""
    
    def __init__(self):
        # Don't call super().__init__() to avoid pygame dependencies
        self.physical_obj = PhysicalObject()
        self.x_speed = 0.0
        self.y_speed = 0.0
        # Mock rect
        self.rect = type('MockRect', (), {
            'x': 0, 'y': 0, 'width': 20, 'height': 20
        })()
    
    def update(self):
        """Required abstract method implementation."""
        self.move()
    
    def move(self):
        """Move based on speed."""
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed


class TestGameObject:
    """Test the base GameObject class."""
    
    def test_game_object_creation(self):
        """Test creating a game object."""
        obj = MockGameObject()
        assert obj.physical_obj is not None
        assert obj.x_speed == 0.0
        assert obj.y_speed == 0.0
    
    def test_game_object_movement(self):
        """Test game object movement."""
        obj = MockGameObject()
        obj.x_speed = 5.0
        obj.y_speed = -3.0
        
        original_x = obj.rect.x
        original_y = obj.rect.y
        
        obj.move()
        
        assert obj.rect.x == original_x + 5.0
        assert obj.rect.y == original_y - 3.0
    
    def test_boundary_checking(self):
        """Test boundary checking."""
        obj = MockGameObject()
        obj.rect.x = -10
        obj.rect.y = -10
        
        obj.check_bounds(200, 150)
        
        assert obj.rect.x >= 0
        assert obj.rect.y >= 0


if __name__ == '__main__':
    # Run tests if pygame is available
    try:
        import pygame
        pygame.init()
        pytest.main([__file__, '-v'])
    except ImportError:
        print("Pygame not available, skipping tests that require it.")
    except Exception as e:
        print(f"Error running tests: {e}")
        # Run tests that don't require pygame
        pytest.main([__file__, '-v', '-k', 'not (config or enemy_factory)'])
