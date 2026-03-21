"""
Custom exception classes for NLCRUD.

Provides a hierarchy of exceptions for different error scenarios,
making error handling more precise and meaningful.
"""


class NLCRUDError(Exception):
    """Base exception for all NLCRUD errors.

    All specific exceptions inherit from this, allowing broad catching
    of NLCRUD-specific errors while still being specific when needed.
    """

    pass


class IntentClassificationError(NLCRUDError):
    """Raised when intent classification fails.

    Occurs when:
    - Model fails to load
    - Text classification fails
    - Confidence is too low
    """

    pass


class EntityExtractionError(NLCRUDError):
    """Raised when entity extraction fails.

    Occurs when:
    - spaCy model fails to load
    - NER processing fails
    - Required entities cannot be extracted
    """

    pass


class ActionBuildError(NLCRUDError):
    """Raised when action building fails.

    Occurs when:
    - Intent and entities don't form valid action
    - Required parameters are missing
    - Resource type is invalid
    """

    pass


class ExecutionError(NLCRUDError):
    """Raised when database execution fails.

    Occurs when:
    - SQL generation fails
    - SQL execution fails
    - Database connection issues
    """

    pass


class ValidationError(NLCRUDError):
    """Raised when validation fails.

    Occurs when:
    - Configuration validation fails
    - Action validation fails
    - Input validation fails
    """

    pass


class ConfigurationError(NLCRUDError):
    """Raised when configuration is invalid or missing.

    Occurs when:
    - Required config values are missing
    - Config values are invalid
    - Config files cannot be read
    """

    pass


class ModelNotFoundError(NLCRUDError):
    """Raised when required model file is not found.

    Occurs when:
    - Intent model is missing
    - spaCy model is not installed
    - Required data files are missing
    """

    pass


class SQLGenerationError(ExecutionError):
    """Raised when SQL generation fails.

    Occurs when:
    - SQLCoder/Ollama returns invalid SQL
    - Rule-based SQL generation fails
    - SQL cannot be extracted from LLM response
    """

    pass


class DatabaseConnectionError(ExecutionError):
    """Raised when database connection fails.

    Occurs when:
    - SQLite database cannot be opened
    - Database file is locked
    - Database initialization fails
    """

    pass
