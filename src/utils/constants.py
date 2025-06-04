"""Game constants extracted from original guardian.py."""

import pygame

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
RED_EYE = (219, 43, 0)

# Screen dimensions
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 220

# Game settings
FPS = 60
PLAYER_HP = 3
PLAYER_IMMORTAL = False
MAX_NUM_BULLET_AND_PLAYER = 3 + 1  # Max num player bullet on screen plus player

# Display settings
DISPLAY_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
