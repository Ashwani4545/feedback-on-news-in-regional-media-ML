"""App package for Regional Newsroom Feedback System."""
import logging
from app.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)

__version__ = "1.0.0"
