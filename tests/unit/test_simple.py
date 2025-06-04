"""Simple test to verify pytest works."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_simple_math():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 3 * 3 == 9


def test_import_config():
    """Test that we can import the config module."""
    try:
        from config.config_loader import ConfigLoader
        assert ConfigLoader is not None
    except ImportError as e:
        pytest.fail(f"Could not import ConfigLoader: {e}")


def test_import_utils():
    """Test that we can import utils."""
    try:
        from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT
        assert SCREEN_WIDTH > 0
        assert SCREEN_HEIGHT > 0
    except ImportError as e:
        pytest.fail(f"Could not import constants: {e}")
