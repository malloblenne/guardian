"""Control system implementations."""

import pygame


class PIController:
    """Proportional-Integral controller for smooth movement."""
    
    def __init__(self, kp: float = 1.0, ki: float = 0.0, anti_windup: float = 100.0):
        """Initialize PI controller.
        
        Args:
            kp: Proportional gain
            ki: Integral gain  
            anti_windup: Anti-windup limit for integral term
        """
        self.kp = kp
        self.ki = ki
        self.anti_windup = anti_windup
        self.integral = 0.0
        self.last_error = 0.0
    
    def control(self, error: float) -> float:
        """Calculate control output.
        
        Args:
            error: Error signal (setpoint - current_value)
            
        Returns:
            Control signal
        """
        # Proportional term
        proportional = self.kp * error
        
        # Integral term with anti-windup
        self.integral += error
        if abs(self.integral) > self.anti_windup:
            self.integral = self.anti_windup if self.integral > 0 else -self.anti_windup
        
        integral = self.ki * self.integral
        
        # Output
        output = proportional + integral
        
        self.last_error = error
        return output
    
    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.last_error = 0.0


class JoypadControl:
    """Joypad/gamepad control handler."""
    
    def __init__(self):
        """Initialize joypad control."""
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
    
    def on_joypad_event(self, event) -> dict:
        """Process joypad events.
        
        Returns:
            Dictionary with 'type' and 'value' keys
        """
        if not self.joystick:
            return {'type': 'None', 'value': 'None'}
        
        import pygame
        
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button
                return {'type': 'pressed', 'value': 'fire'}
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == 0:  # A button
                return {'type': 'released', 'value': 'fire'}
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:  # X axis
                if event.value < -0.5:
                    return {'type': 'pressed', 'value': 'left'}
                elif event.value > 0.5:
                    return {'type': 'pressed', 'value': 'right'}
                else:
                    return {'type': 'released', 'value': 'horizontal'}
            elif event.axis == 1:  # Y axis
                if event.value < -0.5:
                    return {'type': 'pressed', 'value': 'up'}
                elif event.value > 0.5:
                    return {'type': 'pressed', 'value': 'down'}
                else:
                    return {'type': 'released', 'value': 'vertical'}
        
        return {'type': 'None', 'value': 'None'}
