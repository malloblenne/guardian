# Guardian Dependencies Analysis

## Overview
This document contains the dependency analysis performed on `guardian.py` and the Poetry project setup.

## Dependencies Found in guardian.py

### External Libraries
- **pygame** (^2.6.1) - Main game engine library
  - Used for: Graphics rendering, event handling, sound, sprite management
  - Key imports: `import pygame`
  - Features used: 
    - Surface rendering and blitting
    - Sprite groups and collision detection
    - Font rendering
    - Music and sound effects
    - Joystick/gamepad support
    - Time management

- **pytmx** (^3.32) - TMX map format support
  - Used for: Loading and handling Tiled map files
  - Import: `from pytmx.util_pygame import load_pygame`
  - Purpose: Loading TMX map data from `maps/mapcorridor.tmx`

- **pyscroll** (^2.31) - Scrolling library for pygame
  - Used for: Map scrolling and rendering
  - Import: `import pyscroll`
  - Features used:
    - TiledMapData for map handling
    - BufferedRenderer for efficient map rendering
    - Map centering and scrolling

### Standard Library
- **logging** - Logging and debugging
- **math** - Mathematical calculations (trigonometry for circular motion)
- **random** - Random number generation for game mechanics
- **os** - File path operations for loading assets
- **itertools** - Iterator utilities (cycling animations, chaining)
- **sys** - System-specific parameters and functions

## Assets Dependencies

### Graphics Files
- `bitmaps/theGuardian.png` - Main sprite sheet
- `bitmaps/originalStartup.png` - Startup screen graphics
- `bitmaps/bosses.png` - Boss sprites and window icon

### Font Files
- `fonts/PressStart2P.ttf` - Retro game font

### Audio Files
- `sounds/*.mid` - MIDI music files
- `sounds/*.ogg` - Sound effect files

### Map Files
- `maps/mapcorridor.tmx` - TMX format map file
- `maps/*.png` - Tileset graphics

## Development Dependencies

### Code Quality Tools
- **black** (<24) - Python code formatter (version <24 for Python 3.8 compatibility)
- **pytest** (^8.3.5) - Testing framework

## Poetry Project Configuration

### Project Metadata
- **Name**: guardian
- **Version**: 0.1.0
- **Description**: A tribute to The Guardian Legend NES game
- **License**: LGPL-3.0-or-later
- **Python Version**: ^3.8 (Python 3.8+)

### Entry Points
- **guardian** command: Runs `guardian:main` function

### Compatibility
- Generated `requirements.txt` for pip-based installations
- All dependencies tested and working in virtual environment

## Usage

### With Poetry (Recommended)
```bash
# Install dependencies
poetry install

# Run the game
poetry run guardian
# or
poetry run python guardian.py

# Development tools
poetry run black guardian.py  # Format code
poetry run pytest  # Run tests (when added)
```

### With pip (Legacy)
```bash
pip install -r requirements.txt
python guardian.py
```

## Notes
- All dependencies are properly locked in `poetry.lock`
- Project follows Python packaging best practices
- Virtual environment isolation ensures consistent behavior
- Development dependencies are separated from runtime dependencies
