"""
Centralized logging configuration for NLCRUD.

Replaces scattered print statements with structured logging.
Integrates with Config for log level control.
"""
import logging
from typing import Optional

# Create logger instance
logger = logging.getLogger("nlcrud")

# Store whether logging has been initialized
_initialized = False


def setup_logging(level: str = "info") -> None:
    """Initialize logging with specified level.

    Args:
        level: Log level (debug, info, warning, error, critical)

    Raises:
        ValueError: If log level is invalid
    """
    global _initialized

    if _initialized:
        return

    valid_levels = ("debug", "info", "warning", "error", "critical")
    if level.lower() not in valid_levels:
        raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")

    # Set logger level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Create console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)

    _initialized = True
    logger.debug(f"Logging initialized with level: {level.upper()}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to "nlcrud")

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"nlcrud.{name}")
    return logger


def initialize_from_config() -> None:
    """Initialize logging from config.

    Should be called after config is loaded.
    """
    try:
        from nlcrud.config import get_config
        config = get_config()
        setup_logging(config.log_level)
    except Exception as e:
        # Fallback to info level if config not available
        setup_logging("info")
        logger.warning(f"Could not load log level from config: {e}")
