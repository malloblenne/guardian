"""Enemy entity implementations."""

import itertools
import pygame
from typing import List
from core.base import GameObject, create_physical_object_dict
from core.interfaces import Enemy, AIBehavior
from core.sprite_manager import get_sprite, get_flipped_sprite
from config import get_enemy_config
from systems.ai_behaviors import ChasePlayerAI, CircularChaseAI
from entities.bullets import Bullet


def draw_circle_surface(radius: int, center: tuple, color: tuple, width: int = 0) -> pygame.Surface:
    """Create a surface with a circle."""
    surface = pygame.Surface([2 * radius, 2 * radius])
    pygame.draw.circle(surface, color, center, radius, width)
    surface.set_colorkey((0, 0, 0))
    return surface


def draw_circle(color: tuple, radius: int, width: int = 0) -> pygame.Surface:
    """Create a surface with a circle (shortcut)."""
    center = (radius, radius)
    return draw_circle_surface(radius, center, color, width)


class SmallSpaceship(GameObject, Enemy):
    """Small enemy spaceship implementation."""
    
    # Class-level sprite caching
    image_center = None
    image_left = None
    image_right = None
    
    def __init__(self):
        super().__init__(getattr(SmallSpaceship, 'containers', None))
        
        # Load enemy config
        config = get_enemy_config('small_spaceship')
        
        self.physical_obj = create_physical_object_dict(
            hit_points=config.hp,
            damage=config.damage,
            score_value=config.score_value
        )
        
        # Load sprites (class-level caching)
        if SmallSpaceship.image_center is None:
            SmallSpaceship.image_center = get_sprite(config.sprite_sheet, config.sprites['center'])
            SmallSpaceship.image_right = get_sprite(config.sprite_sheet, config.sprites['right'])
            SmallSpaceship.image_left = get_flipped_sprite(config.sprite_sheet, config.sprites['right'], True, False)
        
        self.image = SmallSpaceship.image_center
        self.rect = self.image.get_rect()
        
        # Movement properties
        self.max_speed = config.speed
        self.x_speed = 0.0
        self.y_speed = 0.0
        
        # AI properties
        self.player_x = 0
        self.player_y = 0
        self.last_time = pygame.time.get_ticks()
        self.interval = config.fire_interval
        
        # Position at top of screen
        self.rect.y = -self.rect.height - 1
        
        # Initialize AI behavior
        self.ai_behavior = ChasePlayerAI(
            kp=0.01, ki=0.01, anti_windup=100.0, max_speed=self.max_speed
        )
        
        self.times_update_func_called = 0
    
    def set_player_position(self, x: int, y: int):
        """Update player position for AI."""
        self.player_x = x
        self.player_y = y
    
    def get_behavior(self) -> AIBehavior:
        """Get the AI behavior."""
        return self.ai_behavior
    
    def _fire(self) -> List[Bullet]:
        """Create bullet based on time interval."""
        bullets = []
        
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time >= self.interval:
            self.last_time = ticks_now
            bullet = Bullet(enemy=True)
            bullet.rect.x = self.rect.x + self.rect.width // 2 - bullet.rect.width // 2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
        
        return bullets
    
    def update(self):
        """Update enemy ship."""
        from config import get_config
        
        # Update AI
        self.ai_behavior.update(self, (self.player_x, self.player_y), 1.0/60.0)
        
        self.times_update_func_called += 1.0
        
        # Move
        x_new = self.rect.x + self.x_speed
        y_new = self.rect.y + self.y_speed
        
        # Update sprite based on movement
        x_speed_int = int(self.x_speed)
        if x_speed_int > 1:
            self.image = SmallSpaceship.image_right
        elif x_speed_int < -1:
            self.image = SmallSpaceship.image_left
        else:
            self.image = SmallSpaceship.image_center
        
        self.rect = self.image.get_rect()
        self.rect.x = x_new
        self.rect.y = y_new
        
        # Check boundaries
        config = get_config()
        screen_width = config.game['screen']['width']
        screen_height = config.game['screen']['height']
        self.check_bounds(screen_width, screen_height)
        
        # Fire
        self._fire()


class WhaleBoss(GameObject, Enemy):
    """Whale boss enemy implementation."""
    
    # Class-level sprite caching
    images = []
    
    def __init__(self):
        super().__init__(getattr(WhaleBoss, 'containers', None))
        
        # Load enemy config
        config = get_enemy_config('whale_boss')
        
        self.physical_obj = create_physical_object_dict(
            hit_points=config.hp,
            damage=config.damage,
            score_value=config.score_value
        )
        
        # Load sprites (class-level caching)
        if not WhaleBoss.images:
            WhaleBoss.images.append(get_sprite(config.sprite_sheet, config.sprites['eye_right']))
            WhaleBoss.images.append(get_sprite(config.sprite_sheet, config.sprites['eye_center']))
            WhaleBoss.images.append(pygame.transform.flip(WhaleBoss.images[-1], True, False))  # mirror
            WhaleBoss.images.append(get_sprite(config.sprite_sheet, config.sprites['eye_left']))
            WhaleBoss.images.append(get_sprite(config.sprite_sheet, config.sprites['mouth_half']))
            WhaleBoss.images.append(get_sprite(config.sprite_sheet, config.sprites['mouth_open']))
        
        self.rect = WhaleBoss.images[0].get_rect()
        self.max_speed = config.speed
        self.x_speed = 0.0
        self.y_speed = 0.0
        
        # AI and animation properties
        self.player_x = 0
        self.player_y = 0
        self.last_time = pygame.time.get_ticks()
        self.interval = 700  # Animation interval
        self.last_time_fire = self.last_time
        self.interval_fire = config.fire_interval
        
        # Animation
        self.image_iterator = itertools.cycle(WhaleBoss.images)
        self.image = next(self.image_iterator)
        
        # Initialize AI behavior
        self.ai_behavior = CircularChaseAI(
            kp=0.5, ki=0.05, anti_windup=100.0, max_speed=self.max_speed
        )
    
    def set_player_position(self, x: int, y: int):
        """Update player position for AI."""
        self.player_x = x
        self.player_y = y
    
    def get_behavior(self) -> AIBehavior:
        """Get the AI behavior."""
        return self.ai_behavior
    
    def _fire(self) -> List[Bullet]:
        """Create bullets based on time interval."""
        bullets = []
        
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time_fire >= self.interval_fire:
            self.last_time_fire = ticks_now
            
            from config import get_config
            red_eye_color = get_config().game['colors']['red_eye']
            
            # Center bullet
            bullet = Bullet(enemy=True, image=draw_circle(red_eye_color, 8, 4))
            bullet.rect.x = self.rect.x + self.rect.width // 2 - bullet.rect.width // 2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            
            # Left bullet
            bullet = Bullet(enemy=True, x_speed=-1, image=draw_circle(red_eye_color, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width // 2 - bullet.rect.width // 2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            
            # Right bullet
            bullet = Bullet(enemy=True, x_speed=3, image=draw_circle(red_eye_color, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width // 2 - bullet.rect.width // 2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            
            # Another right bullet
            bullet = Bullet(enemy=True, x_speed=1, image=draw_circle(red_eye_color, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width // 2 - bullet.rect.width // 2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
        
        return bullets
    
    def update_animation(self):
        """Update animation."""
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time >= self.interval:
            self.last_time = ticks_now
            self.image = next(self.image_iterator)
    
    def update(self):
        """Update whale boss."""
        from config import get_config
        
        self.update_animation()
        
        # Update AI
        self.ai_behavior.update(self, (self.player_x, self.player_y), 1.0/60.0)
        
        # Move
        x_pos = self.rect.x + self.x_speed
        y_pos = self.rect.y + self.y_speed
        
        self.rect = self.image.get_rect()
        self.rect.x = x_pos
        self.rect.y = y_pos
        
        # Check boundaries
        config = get_config()
        screen_width = config.game['screen']['width']
        screen_height = config.game['screen']['height']
        self.check_bounds(screen_width, screen_height)
        
        # Fire
        self._fire()
