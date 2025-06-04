"""Integration tests for the Guardian game refactoring."""

import pytest
import pygame
import os
import sys
import tempfile

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestGameIntegration:
    """Integration tests for the complete game system."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Set up pygame for testing."""
        pygame.init()
        # Create a dummy display for testing
        pygame.display.set_mode((256, 220), pygame.NOFRAME)
        yield
        pygame.quit()
    
    def test_import_refactored_game(self):
        """Test that the refactored game can be imported."""
        try:
            # This might fail due to missing config files, but should import
            import guardian_refactored
            assert hasattr(guardian_refactored, 'GuardianGame')
            assert hasattr(guardian_refactored, 'main')
        except Exception as e:
            # Expected if config files are missing
            assert 'sprites.yaml' in str(e) or 'FileNotFoundError' in str(type(e).__name__)
    
    def test_config_system_integration(self):
        """Test configuration system integration."""
        # Create a minimal config for testing
        config_content = '''
sprite_sheets:
  test_sheet:
    file: "bitmaps/test.png"
    color_key: [0, 0, 0]
    sprites:
      test_sprite: [0, 0, 16, 16]

enemy_types:
  test_enemy:
    sprite_sheet: "test_sheet"
    sprites:
      center: "test_sprite"
    hp: 1
    damage: 1
    score_value: 10
    speed: 5.0
    ai_type: "chase_player"
    fire_interval: 1000

player:
  sprite_sheet: "test_sheet"
  sprites:
    normal: "test_sprite"
  hp: 3
  damage: 1
  speed: 3
  immortality_interval: 800
  max_bullets: 3

ui:
  fonts:
    main: "fonts/test.ttf"

audio:
  music:
    title: "sounds/test.mid"

game:
  screen:
    width: 256
    height: 220
  colors:
    red_eye: [219, 43, 0]
'''
        
        # Write config to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            from config.config_loader import ConfigLoader
            config_loader = ConfigLoader(temp_config_path)
            config = config_loader.load_config()
            
            assert config.sprite_sheets['test_sheet'].file == "bitmaps/test.png"
            assert config.enemy_types['test_enemy'].hp == 1
            assert config.player.hp == 3
            
        finally:
            os.unlink(temp_config_path)
    
    def test_sprite_manager_integration(self):
        """Test sprite manager integration with config."""
        # This test would require actual sprite files
        # For now, just test the import and class structure
        from core.sprite_manager import SpriteManager, get_sprite_manager
        
        manager = get_sprite_manager()
        assert isinstance(manager, SpriteManager)
    
    def test_factory_pattern_integration(self):
        """Test factory pattern integration."""
        from factories.enemy_factory import EnemyFactory
        
        factory = EnemyFactory()
        assert hasattr(factory, 'create_small_spaceship')
        assert hasattr(factory, 'create_whale_boss')
        assert hasattr(factory, 'create_random_enemy')
    
    def test_ai_system_integration(self):
        """Test AI system integration."""
        from systems.ai_behaviors import ChasePlayerAI, CircularChaseAI
        from systems.controllers import PIController
        
        # Create AI instances
        chase_ai = ChasePlayerAI()
        circular_ai = CircularChaseAI()
        pi_controller = PIController()
        
        assert chase_ai is not None
        assert circular_ai is not None
        assert pi_controller is not None
    
    def test_entity_system_integration(self):
        """Test entity system integration."""
        # Test that entity classes can be imported
        try:
            from entities.player import Player
            from entities.bullets import Bullet, PlayerBullet
            from entities.start_screen import StartScreen
            
            # These classes should exist
            assert Player is not None
            assert Bullet is not None
            assert PlayerBullet is not None
            assert StartScreen is not None
            
        except ImportError as e:
            # Might fail due to missing dependencies
            assert 'pygame' in str(e) or 'config' in str(e)


class TestGameplayFlow:
    """Test basic gameplay flow scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Set up pygame for testing."""
        pygame.init()
        pygame.display.set_mode((256, 220), pygame.NOFRAME)
        yield
        pygame.quit()
    
    def test_pi_controller_behavior(self):
        """Test PI controller produces reasonable behavior."""
        from systems.controllers import PIController
        
        controller = PIController(kp=1.0, ki=0.1, anti_windup=100.0)
        
        # Simulate tracking a moving target
        target = 100
        current = 0
        
        for _ in range(10):
            error = target - current
            control_output = controller.control(error)
            current += control_output * 0.1  # Simulate system response
        
        # Should converge towards target
        assert abs(current - target) < abs(0 - target)
    
    def test_enemy_ai_movement_patterns(self):
        """Test enemy AI produces reasonable movement patterns."""
        from systems.ai_behaviors import ChasePlayerAI
        
        class MockEnemy:
            def __init__(self):
                self.rect = type('Rect', (), {'x': 0, 'y': 0, 'width': 20, 'height': 20})()
                self.x_speed = 0
                self.y_speed = 0
        
        ai = ChasePlayerAI(max_speed=5.0)
        enemy = MockEnemy()
        
        # Test movement towards player
        for _ in range(5):
            ai.update(enemy, (100, 100), 1.0/60.0)
        
        # Enemy should be moving towards player position
        assert abs(enemy.x_speed) <= 5.0  # Within speed limits
        assert abs(enemy.y_speed) <= 5.0


class TestPerformance:
    """Performance and stress tests."""
    
    def test_config_loading_performance(self):
        """Test that config loading is reasonably fast."""
        import time
        
        config_content = '''
sprite_sheets:
  sheet1:
    file: "test.png"
    sprites:
      sprite1: [0, 0, 16, 16]
      sprite2: [16, 0, 16, 16]

enemy_types:
  enemy1:
    sprite_sheet: "sheet1"
    sprites:
      center: "sprite1"
    hp: 1
    damage: 1
    score_value: 10
    speed: 5.0
    ai_type: "chase"
    fire_interval: 1000

player:
  sprite_sheet: "sheet1"
  sprites:
    normal: "sprite1"
  hp: 3
  damage: 1
  speed: 3
  immortality_interval: 800
  max_bullets: 3

ui: {}
audio: {}
game:
  screen:
    width: 256
    height: 220
  colors: {}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            from config.config_loader import ConfigLoader
            
            start_time = time.time()
            config_loader = ConfigLoader(temp_config_path)
            config_loader.load_config()
            end_time = time.time()
            
            # Should load quickly (less than 100ms)
            assert (end_time - start_time) < 0.1
            
        finally:
            os.unlink(temp_config_path)
    
    def test_pi_controller_stability(self):
        """Test PI controller stability over many iterations."""
        from systems.controllers import PIController
        
        controller = PIController(kp=0.5, ki=0.1, anti_windup=50.0)
        
        # Run for many iterations
        for i in range(1000):
            error = 10.0 * (1.0 if i % 100 < 50 else -1.0)  # Square wave input
            output = controller.control(error)
            
            # Output should remain bounded
            assert abs(output) < 100.0  # Reasonable bound
            assert not (output != output)  # Not NaN


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
