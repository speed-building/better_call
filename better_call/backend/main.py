"""
New backend main module with improved architecture.
This replaces the old main.py with better separation of concerns.
"""

from .api import router
from .core.config import settings

# Export the router for use in the main application
__all__ = ["router", "settings"]
