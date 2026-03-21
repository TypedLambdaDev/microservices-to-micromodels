"""
Centralized configuration management for NLCRUD.

This module provides a single source of truth for all configuration,
eliminating scattered environment variables across the codebase.
"""
import os
from dataclasses import dataclass, field
from typing import Literal, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class OllamaConfig:
    """Configuration for Ollama LLM provider."""
    url: str = "http://localhost:11434/api/generate"
    model: str = "sqlcoder"

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Load Ollama config from environment variables."""
        return cls(
            url=os.environ.get("OLLAMA_URL", cls.url),
            model=os.environ.get("OLLAMA_MODEL", cls.model)
        )


@dataclass
class DatabaseConfig:
    """Configuration for database connection."""
    path: str = "db/db.sqlite"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database config from environment variables."""
        return cls(
            path=os.environ.get("DB_PATH", cls.path)
        )


@dataclass
class Config:
    """Main configuration class for NLCRUD application."""

    # Feature flags
    use_sqlcoder: bool = False
    use_regex_extractor: bool = False

    # Extractor type
    extractor_type: Literal["regex", "spacy"] = "spacy"

    # Logging
    log_level: str = "info"

    # Model paths
    intent_model_path: str = "model/intent.ftz"
    spacy_model: str = "en_core_web_sm"

    # Database
    database: Optional[DatabaseConfig] = field(default=None)

    # Ollama (only LLM provider for this POC)
    ollama: Optional[OllamaConfig] = field(default=None)

    def __post_init__(self):
        """Initialize nested config objects if not provided."""
        if self.database is None:
            self.database = DatabaseConfig.from_env()
        if self.ollama is None:
            self.ollama = OllamaConfig.from_env()

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Environment variables:
            USE_SQLCODER: Enable SQLCoder (true/false)
            USE_REGEX_EXTRACTOR: Use regex extractor instead of spaCy
            LOG_LEVEL: Log level (debug/info/warning/error/critical)
            INTENT_MODEL_PATH: Path to FastText intent model
            SPACY_MODEL: SpaCy model name
            DB_PATH: Database file path
            OLLAMA_URL: Ollama API endpoint
            OLLAMA_MODEL: Ollama model name
        """
        use_sqlcoder_str = os.environ.get("USE_SQLCODER", "false").lower()
        use_sqlcoder = use_sqlcoder_str in ("true", "1", "yes")

        use_regex_str = os.environ.get("USE_REGEX_EXTRACTOR", "false").lower()
        use_regex = use_regex_str in ("true", "1", "yes")

        extractor = "regex" if use_regex else "spacy"

        return cls(
            use_sqlcoder=use_sqlcoder,
            use_regex_extractor=use_regex,
            extractor_type=extractor,
            log_level=os.environ.get("LOG_LEVEL", "info"),
            intent_model_path=os.environ.get("INTENT_MODEL_PATH", "model/intent.ftz"),
            spacy_model=os.environ.get("SPACY_MODEL", "en_core_web_sm"),
            database=DatabaseConfig.from_env(),
            ollama=OllamaConfig.from_env()
        )

    def validate(self) -> bool:
        """Validate configuration settings.

        Returns:
            bool: True if config is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if self.log_level.lower() not in ("debug", "info", "warning", "error", "critical"):
            raise ValueError(f"Invalid log_level: {self.log_level}")

        if self.extractor_type not in ("regex", "spacy"):
            raise ValueError(f"Invalid extractor_type: {self.extractor_type}")

        if not os.path.exists(self.intent_model_path):
            raise ValueError(f"Intent model not found at {self.intent_model_path}")

        return True


# Global config instance (lazy-loaded)
_config: Config = None


def get_config() -> Config:
    """Get the global configuration instance.

    Lazily loads config on first access.

    Returns:
        Config: The global configuration
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance.

    Useful for testing with different configurations.

    Args:
        config: Configuration to use
    """
    global _config
    _config = config


# Print configuration on module load (useful for debugging)
if __name__ == "__main__":
    config = get_config()
    print(f"NLCRUD Configuration:")
    print(f"  SQLCoder enabled: {config.use_sqlcoder}")
    print(f"  Extractor type: {config.extractor_type}")
    print(f"  Log level: {config.log_level}")
    if config.database:
        print(f"  Database path: {config.database.path}")
    if config.ollama:
        print(f"  Ollama URL: {config.ollama.url}")
        print(f"  Ollama model: {config.ollama.model}")
