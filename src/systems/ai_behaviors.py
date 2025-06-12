"""AI behavior implementations for enemies."""

import math
import itertools
from typing import Tuple
from core.interfaces import AIBehavior
from systems.controllers import PIController


def circular_motion(radius: float = 100.0, num_points: int = 200):
    """Generator for circular motion coordinates."""
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        yield x, y


class ChasePlayerAI(AIBehavior):
    """AI that chases the player using PI controller."""
    
    def __init__(self, kp: float = 0.01, ki: float = 0.01, anti_windup: float = 100.0, 
                 max_speed: float = 10.0):
        self.max_speed = max_speed
        self.pi_x = PIController(kp, ki, anti_windup)
        self.pi_y = PIController(kp, ki, anti_windup)
        self.update_count = 0
    
    def update(self, enemy, player_pos: Tuple[int, int], dt: float):
        """Update chase behavior."""
        enemy_center_x = enemy.rect.x + enemy.rect.width // 2
        enemy_center_y = enemy.rect.y + enemy.rect.height // 2
        
        player_x, player_y = player_pos
        
        # Calculate error
        error_x = player_x - enemy_center_x
        error_y = player_y - enemy_center_y
        
        # Apply PI control
        enemy.x_speed = self.pi_x.control(error_x)
        enemy.x_speed = max(-self.max_speed, min(self.max_speed, enemy.x_speed))
        
        # Add sinusoidal offset to Y movement for more interesting behavior
        offset_max = 3.0
        freq = 1.0 / 240.0
        sin_value = math.sin(2.0 * math.pi * freq * self.update_count)
        offset_y = offset_max * sin_value - offset_max / 2.0 - 1.0
        
        enemy.y_speed = self.pi_y.control(error_y) + offset_y
        enemy.y_speed = max(-self.max_speed, min(self.max_speed, enemy.y_speed))
        
        self.update_count += 1


class CircularChaseAI(AIBehavior):
    """AI that performs circular motion around the player."""
    
    def __init__(self, kp: float = 0.5, ki: float = 0.05, anti_windup: float = 100.0,
                 max_speed: float = 5.0):
        self.max_speed = max_speed
        self.pi_x = PIController(kp, ki, anti_windup)
        self.pi_y = PIController(kp, ki, anti_windup)
        
        self.behavior = 0  # 0 = circle, 1 = chase
        self.behavior_timer = 0
        self.behavior_interval = 10000  # ms
        
        self.player_x_filtered = 0.0
        self.player_y_filtered = 0.0
        self.alpha_smoothing = 3.0 / 800.0
        
        self.circle_iterator = itertools.cycle(circular_motion())
    
    def update(self, enemy, player_pos: Tuple[int, int], dt: float):
        """Update circular chase behavior."""
        import pygame
        
        # Update behavior switching
        self.behavior_timer += dt
        if self.behavior_timer >= self.behavior_interval:
            self.behavior_timer = 0
            self.behavior = (self.behavior + 1) % 2
        
        player_x, player_y = player_pos
        
        # Apply exponential smoothing to player position
        if self.player_x_filtered == 0 and self.player_y_filtered == 0:
            self.player_x_filtered = player_x
            self.player_y_filtered = player_y
        
        alpha = self.alpha_smoothing
        self.player_x_filtered = player_x * alpha + (1.0 - alpha) * self.player_x_filtered
        self.player_y_filtered = player_y * alpha + (1.0 - alpha) * self.player_y_filtered
        
        enemy_center_x = enemy.rect.x + enemy.rect.width // 2
        enemy_center_y = enemy.rect.y + enemy.rect.height // 2
        
        if self.behavior == 1:  # Chase mode
            self.alpha_smoothing = 3.0 / 300.0
            
            error_x = self.player_x_filtered - enemy_center_x
            enemy.x_speed = self.pi_x.control(error_x)
            enemy.x_speed = max(-self.max_speed, min(self.max_speed, enemy.x_speed))
            
            y_offset = 200
            error_y = self.player_y_filtered - enemy_center_y - y_offset
            enemy.y_speed = self.pi_y.control(error_y)
            enemy.y_speed = max(-self.max_speed, min(self.max_speed, enemy.y_speed))
            
        else:  # Circle mode
            self.alpha_smoothing = 3.0 / 800.0
            
            x_circle, y_circle = next(self.circle_iterator)
            
            x_setpoint = self.player_x_filtered + x_circle
            y_setpoint = self.player_y_filtered - y_circle - enemy.rect.height
            
            error_x = x_setpoint - enemy_center_x
            enemy.x_speed = self.pi_x.control(error_x)
            enemy.x_speed = max(-self.max_speed, min(self.max_speed, enemy.x_speed))
            
            error_y = y_setpoint - enemy_center_y
            enemy.y_speed = self.pi_y.control(error_y)
            enemy.y_speed = max(-self.max_speed, min(self.max_speed, enemy.y_speed))
