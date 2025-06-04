"""Player entity implementation."""

import os
import itertools
import pygame
from typing import Optional, List
from core.base import GameObject, create_physical_object_dict
from core.interfaces import Controllable, Weapon
from core.sprite_manager import get_sprite, get_flipped_sprite
from config import get_config
from systems.controllers import JoypadControl


def on_keyboard_event_user1(event) -> dict:
    """Process keyboard events for player 1.
    
    Returns:
        Dictionary with 'type' and 'value' keys
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
            return {'type': 'pressed', 'value': 'left'}
        elif event.key == pygame.K_RIGHT:
            return {'type': 'pressed', 'value': 'right'}
        elif event.key == pygame.K_UP:
            return {'type': 'pressed', 'value': 'up'}
        elif event.key == pygame.K_DOWN:
            return {'type': 'pressed', 'value': 'down'}
        elif event.key == pygame.K_SPACE:
            return {'type': 'pressed', 'value': 'fire'}
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_LEFT:
            return {'type': 'released', 'value': 'left'}
        elif event.key == pygame.K_RIGHT:
            return {'type': 'released', 'value': 'right'}
        elif event.key == pygame.K_UP:
            return {'type': 'released', 'value': 'up'}
        elif event.key == pygame.K_DOWN:
            return {'type': 'released', 'value': 'down'}
        elif event.key == pygame.K_SPACE:
            return {'type': 'released', 'value': 'fire'}
    
    return {'type': 'None', 'value': 'None'}


class PlayerWeapon(Weapon):
    """Player weapon implementation."""
    
    def __init__(self, owner):
        self.owner = owner
        self.bullet_image = get_sprite("bullets", "player_bullet")
        
        # Load sounds
        if pygame.mixer:
            self.fire_sound = pygame.mixer.Sound(os.path.join('sounds', 'laser5.ogg'))
    
    def can_fire(self) -> bool:
        """Check if weapon can fire based on bullet limit."""
        from entities.bullets import PlayerBullet
        if not hasattr(PlayerBullet, 'containers'):
            return True
        
        num_bullets = min(len(group) for group in PlayerBullet.containers)
        config = get_config()
        max_bullets = config.player.max_bullets + 1  # +1 for player
        return num_bullets < max_bullets
    
    def fire(self, position) -> List[pygame.sprite.Sprite]:
        """Fire the weapon."""
        from entities.bullets import PlayerBullet
        
        if not self.can_fire():
            return []
        
        bullet = PlayerBullet(image=self.bullet_image)
        bullet.rect.x = position[0] - bullet.rect.width // 2
        bullet.rect.y = position[1]
        
        if pygame.mixer and hasattr(self, 'fire_sound'):
            self.fire_sound.play()
        
        return [bullet]


class Player(GameObject, Controllable):
    """Player spaceship implementation."""
    
    def __init__(self):
        super().__init__(getattr(Player, 'containers', None))
        
        # Load config
        config = get_config()
        player_config = config.player
        
        # Initialize physical properties
        self.physical_obj = create_physical_object_dict(
            hit_points=player_config.hp,
            immortal=False,
            damage=player_config.damage
        )
        
        # Load sprites
        self.spaceship_normal = get_sprite(player_config.sprite_sheet, player_config.sprites['normal'])
        self.spaceship_power1 = get_sprite(player_config.sprite_sheet, player_config.sprites['power1'])
        self.spaceship_power2 = get_sprite(player_config.sprite_sheet, player_config.sprites['power2'])
        self.spaceship_left = get_sprite(player_config.sprite_sheet, player_config.sprites['left'])
        self.spaceship_right = get_flipped_sprite(player_config.sprite_sheet, player_config.sprites['left'], True, False)
        
        # Reverse sprites for immortality animation
        reverse_spaceship = get_sprite(player_config.sprite_sheet, player_config.sprites['reverse'])
        reverse_spaceship_tilt1 = get_sprite(player_config.sprite_sheet, player_config.sprites['reverse_tilt1'])
        reverse_spaceship_tilt2 = get_sprite(player_config.sprite_sheet, player_config.sprites['reverse_tilt2'])
        reverse_spaceship_tilt1_flip = pygame.transform.flip(reverse_spaceship_tilt1, True, False)
        reverse_spaceship_tilt2_flip = pygame.transform.flip(reverse_spaceship_tilt2, True, False)
        
        # Animation iterators
        self.iterator_spaceship_center = itertools.cycle([
            self.spaceship_normal,
            self.spaceship_power1,
            self.spaceship_power2
        ])
        
        self.iterator_spaceship_reverse = itertools.cycle([
            reverse_spaceship_tilt2,
            reverse_spaceship_tilt1,
            reverse_spaceship,
            reverse_spaceship_tilt2_flip,
            reverse_spaceship_tilt1_flip,
            self.spaceship_normal
        ])
        
        # Set initial image and position
        self.image = self.spaceship_normal
        self.rect = self.image.get_rect()
        self.rect.x = config.game['screen']['width'] // 2 - self.rect.width // 2
        self.rect.y = config.game['screen']['height'] - self.rect.height // 2
        
        # Movement speeds
        self.x_speed_left = 0
        self.x_speed_right = 0  
        self.y_speed_up = 0
        self.y_speed_down = 0
        
        # Load sounds
        if pygame.mixer:
            self.collision_sound = pygame.mixer.Sound(
                os.path.join('sounds', '27826_erdie_sword01_short.ogg')
            )
        
        # Game state
        self.score = 0
        self.last_hit_points = self.physical_obj['hit_points']
        self.last_time_immortal = pygame.time.get_ticks()
        self.immortality_interval = player_config.immortality_interval
        self.immortality_always = False  # For testing
        self.iteration = 0
        self.reloading = False
        
        # Input handling
        self.joypad = JoypadControl()
        
        # Weapon system
        self.weapon = PlayerWeapon(self)
    
    def _fire(self):
        """Fire the player weapon."""
        center_x = self.rect.x + self.rect.width // 2
        bullets = self.weapon.fire((center_x, self.rect.y))
        return bullets
    
    def process_event(self, event):
        """Process input events."""
        # Try keyboard input first
        game_event = on_keyboard_event_user1(event)
        
        if game_event['type'] == 'None' or game_event['value'] == 'None':
            # Try joypad input
            game_event = self.joypad.on_joypad_event(event)
            if game_event['type'] == 'None' or game_event['value'] == 'None':
                return None
        
        firing = False
        
        if game_event['type'] == 'pressed':
            if game_event['value'] == 'left':
                self.x_speed_left = -3
            elif game_event['value'] == 'right':
                self.x_speed_right = 3
            elif game_event['value'] == 'up':
                self.y_speed_up = -3
            elif game_event['value'] == 'down':
                self.y_speed_down = 3
            elif game_event['value'] == 'fire':
                if self.weapon.can_fire():
                    self._fire()
                    firing = True
        
        elif game_event['type'] == 'released':
            if game_event['value'] == 'left':
                self.x_speed_left = 0
            elif game_event['value'] == 'right':
                self.x_speed_right = 0
            elif game_event['value'] == 'up':
                self.y_speed_up = 0
            elif game_event['value'] == 'down':
                self.y_speed_down = 0
        
        self.reloading = firing
        return None
    
    def _set_temporary_immortality(self):
        """Make immortal after taking damage."""
        self.physical_obj['immortal'] = True
        self.physical_obj['damage'] = 0.0
        self.last_time_immortal = pygame.time.get_ticks()
    
    def update(self):
        """Update player spaceship."""
        config = get_config()
        screen_width = config.game['screen']['width']
        screen_height = config.game['screen']['height']
        
        # Update position
        x_speed = self.x_speed_left + self.x_speed_right
        y_speed = self.y_speed_up + self.y_speed_down
        self.rect.x += x_speed
        self.rect.y += y_speed
        
        # Check boundaries
        self.check_bounds(screen_width, screen_height)
        
        # Remove immortality if time expired
        if self.physical_obj['immortal'] and not self.immortality_always:
            ticks_now = pygame.time.get_ticks()
            if ticks_now - self.last_time_immortal >= self.immortality_interval:
                self.physical_obj['immortal'] = False
        
        # Check if damage received
        if self.last_hit_points > self.physical_obj['hit_points']:
            self._set_temporary_immortality()
        
        self.last_hit_points = self.physical_obj['hit_points']
        
        # Update sprite based on state
        if self.physical_obj['immortal'] and not self.immortality_always:
            if self.iteration % 5 == 0:
                self.image = next(self.iterator_spaceship_reverse)
        else:
            if x_speed < 0 and self.image != self.spaceship_left:
                self.image = self.spaceship_left
            elif x_speed > 0 and self.image != self.spaceship_right:
                self.image = self.spaceship_right
            elif x_speed == 0 and self.iteration % 3 == 0:
                self.image = next(self.iterator_spaceship_center)
        
        self.iteration += 1
