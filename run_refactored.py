#!/usr/bin/env python3
"""Entry point for the refactored Guardian game."""

import sys
import os

# Add src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

# Now we can import the game
from guardian_refactored import GuardianGame

if __name__ == "__main__":
    game = GuardianGame()
    game.run()
